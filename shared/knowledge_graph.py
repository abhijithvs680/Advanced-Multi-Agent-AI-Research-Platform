"""
Knowledge Graph - Store and retrieve research artifacts with relationships.
Enables lineage tracking and similarity search across experiments.
"""
import json
import sqlite3
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import hashlib

from shared.logger import get_logger

logger = get_logger(__name__)


@dataclass
class KnowledgeNode:
    """Base class for knowledge graph nodes"""
    node_id: str
    node_type: str
    data: Dict[str, Any]
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KnowledgeEdge:
    """Relationship between nodes"""
    source_id: str
    target_id: str
    edge_type: str
    properties: Dict[str, Any]


class KnowledgeGraph:
    """
    In-memory and persistent knowledge graph for research artifacts.
    
    Node Types:
    - paper: Academic papers with metadata
    - experiment: Job/workflow executions
    - model: Trained models
    - dataset: Used datasets
    - hypothesis: Research hypotheses
    
    Edge Types:
    - cites: Paper cites another paper
    - uses: Experiment uses dataset/model
    - produces: Experiment produces model/result
    - related_to: General relation
    """
    
    def __init__(self, db_path: str = "data/knowledge_graph.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info("knowledge_graph_initialized", db_path=db_path)
    
    def _init_database(self):
        """Initialize SQLite database with schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Nodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                node_id TEXT PRIMARY KEY,
                node_type TEXT NOT NULL,
                data JSON NOT NULL,
                embedding JSON,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Edges table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                edge_type TEXT NOT NULL,
                properties JSON,
                created_at TEXT NOT NULL,
                FOREIGN KEY (source_id) REFERENCES nodes(node_id),
                FOREIGN KEY (target_id) REFERENCES nodes(node_id),
                UNIQUE(source_id, target_id, edge_type)
            )
        """)
        
        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(node_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(edge_type)")
        
        conn.commit()
        conn.close()
    
    def _generate_id(self, prefix: str, data: Any) -> str:
        """Generate unique ID from content"""
        content = json.dumps(data, sort_keys=True)
        hash_val = hashlib.md5(content.encode()).hexdigest()[:12]
        return f"{prefix}_{hash_val}"
    
    # ==================== Node Operations ====================
    
    def add_node(
        self,
        node_type: str,
        data: Dict[str, Any],
        node_id: Optional[str] = None
    ) -> str:
        """
        Add a node to the knowledge graph.
        
        Args:
            node_type: Type of node (paper, experiment, model, etc.)
            data: Node data dictionary
            node_id: Optional custom ID
            
        Returns:
            Node ID
        """
        node_id = node_id or self._generate_id(node_type, data)
        now = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO nodes (node_id, node_type, data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (node_id, node_type, json.dumps(data), now, now))
            conn.commit()
            logger.info("node_added", node_id=node_id, node_type=node_type)
        except Exception as e:
            logger.error("add_node_failed", error=str(e))
            raise
        finally:
            conn.close()
        
        return node_id
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get a node by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM nodes WHERE node_id = ?", (node_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return KnowledgeNode(
                node_id=row[0],
                node_type=row[1],
                data=json.loads(row[2]),
                created_at=row[4]
            )
        return None
    
    def get_nodes_by_type(self, node_type: str, limit: int = 100) -> List[KnowledgeNode]:
        """Get all nodes of a specific type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM nodes WHERE node_type = ? ORDER BY created_at DESC LIMIT ?",
            (node_type, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [
            KnowledgeNode(
                node_id=row[0],
                node_type=row[1],
                data=json.loads(row[2]),
                created_at=row[4]
            )
            for row in rows
        ]
    
    def search_nodes(
        self,
        query: str,
        node_type: Optional[str] = None,
        limit: int = 20
    ) -> List[KnowledgeNode]:
        """Search nodes by text in data JSON"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if node_type:
            cursor.execute("""
                SELECT * FROM nodes 
                WHERE node_type = ? AND data LIKE ?
                ORDER BY created_at DESC LIMIT ?
            """, (node_type, f"%{query}%", limit))
        else:
            cursor.execute("""
                SELECT * FROM nodes 
                WHERE data LIKE ?
                ORDER BY created_at DESC LIMIT ?
            """, (f"%{query}%", limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            KnowledgeNode(
                node_id=row[0],
                node_type=row[1],
                data=json.loads(row[2]),
                created_at=row[4]
            )
            for row in rows
        ]
    
    # ==================== Edge Operations ====================
    
    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add an edge between two nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            edge_type: Type of relationship
            properties: Optional edge properties
            
        Returns:
            True if successful
        """
        now = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO edges (source_id, target_id, edge_type, properties, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (source_id, target_id, edge_type, json.dumps(properties or {}), now))
            conn.commit()
            logger.info("edge_added", source=source_id, target=target_id, type=edge_type)
            return True
        except Exception as e:
            logger.error("add_edge_failed", error=str(e))
            return False
        finally:
            conn.close()
    
    def get_edges(
        self,
        node_id: str,
        direction: str = "both",
        edge_type: Optional[str] = None
    ) -> List[KnowledgeEdge]:
        """Get edges connected to a node"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        edges = []
        
        if direction in ("out", "both"):
            query = "SELECT * FROM edges WHERE source_id = ?"
            params = [node_id]
            if edge_type:
                query += " AND edge_type = ?"
                params.append(edge_type)
            
            cursor.execute(query, params)
            for row in cursor.fetchall():
                edges.append(KnowledgeEdge(
                    source_id=row[1],
                    target_id=row[2],
                    edge_type=row[3],
                    properties=json.loads(row[4]) if row[4] else {}
                ))
        
        if direction in ("in", "both"):
            query = "SELECT * FROM edges WHERE target_id = ?"
            params = [node_id]
            if edge_type:
                query += " AND edge_type = ?"
                params.append(edge_type)
            
            cursor.execute(query, params)
            for row in cursor.fetchall():
                edges.append(KnowledgeEdge(
                    source_id=row[1],
                    target_id=row[2],
                    edge_type=row[3],
                    properties=json.loads(row[4]) if row[4] else {}
                ))
        
        conn.close()
        return edges
    
    # ==================== Specialized Operations ====================
    
    def store_paper(
        self,
        paper_id: str,
        title: str,
        abstract: str,
        authors: List[str],
        year: int,
        citations: Optional[List[str]] = None,
        **metadata
    ) -> str:
        """Store a paper and its citations"""
        data = {
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "year": year,
            **metadata
        }
        
        node_id = self.add_node("paper", data, node_id=f"paper_{paper_id}")
        
        # Add citation edges
        if citations:
            for cited_id in citations:
                self.add_edge(node_id, f"paper_{cited_id}", "cites")
        
        return node_id
    
    def store_experiment(
        self,
        job_id: str,
        topic: str,
        domain: str,
        config: Dict[str, Any],
        results: Optional[Dict[str, Any]] = None,
        paper_ids: Optional[List[str]] = None,
        model_ids: Optional[List[str]] = None
    ) -> str:
        """Store an experiment/job execution"""
        data = {
            "topic": topic,
            "domain": domain,
            "config": config,
            "results": results
        }
        
        node_id = self.add_node("experiment", data, node_id=f"exp_{job_id}")
        
        # Link to papers
        if paper_ids:
            for paper_id in paper_ids:
                self.add_edge(node_id, f"paper_{paper_id}", "references")
        
        # Link to models
        if model_ids:
            for model_id in model_ids:
                self.add_edge(node_id, model_id, "produces")
        
        return node_id
    
    def store_model(
        self,
        model_id: str,
        model_type: str,
        architecture: Dict[str, Any],
        metrics: Dict[str, float],
        experiment_id: Optional[str] = None
    ) -> str:
        """Store a trained model"""
        data = {
            "model_type": model_type,
            "architecture": architecture,
            "metrics": metrics
        }
        
        node_id = self.add_node("model", data, node_id=f"model_{model_id}")
        
        if experiment_id:
            self.add_edge(f"exp_{experiment_id}", node_id, "produces")
        
        return node_id
    
    def store_hypothesis(
        self,
        hypothesis_text: str,
        rationale: str,
        novelty_score: float,
        source_papers: Optional[List[str]] = None,
        experiment_id: Optional[str] = None
    ) -> str:
        """Store a research hypothesis"""
        data = {
            "text": hypothesis_text,
            "rationale": rationale,
            "novelty_score": novelty_score
        }
        
        node_id = self.add_node("hypothesis", data)
        
        if source_papers:
            for paper_id in source_papers:
                self.add_edge(node_id, f"paper_{paper_id}", "derived_from")
        
        if experiment_id:
            self.add_edge(f"exp_{experiment_id}", node_id, "tests")
        
        return node_id
    
    def get_experiment_lineage(self, job_id: str) -> Dict[str, Any]:
        """Get complete lineage for an experiment"""
        experiment = self.get_node(f"exp_{job_id}")
        if not experiment:
            return {}
        
        lineage = {
            "experiment": experiment.to_dict(),
            "papers": [],
            "models": [],
            "hypotheses": []
        }
        
        edges = self.get_edges(f"exp_{job_id}", direction="both")
        
        for edge in edges:
            if edge.edge_type == "references":
                paper = self.get_node(edge.target_id)
                if paper:
                    lineage["papers"].append(paper.to_dict())
            elif edge.edge_type == "produces":
                model = self.get_node(edge.target_id)
                if model:
                    lineage["models"].append(model.to_dict())
            elif edge.edge_type == "tests":
                hypothesis = self.get_node(edge.target_id)
                if hypothesis:
                    lineage["hypotheses"].append(hypothesis.to_dict())
        
        return lineage
    
    def get_stats(self) -> Dict[str, int]:
        """Get knowledge graph statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute("SELECT node_type, COUNT(*) FROM nodes GROUP BY node_type")
        for row in cursor.fetchall():
            stats[f"{row[0]}_count"] = row[1]
        
        cursor.execute("SELECT COUNT(*) FROM edges")
        stats["edge_count"] = cursor.fetchone()[0]
        
        conn.close()
        return stats


# Global instance
_knowledge_graph: Optional[KnowledgeGraph] = None


def get_knowledge_graph(db_path: str = "data/knowledge_graph.db") -> KnowledgeGraph:
    """Get or create global knowledge graph instance"""
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = KnowledgeGraph(db_path)
    return _knowledge_graph
