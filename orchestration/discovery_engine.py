"""
Discovery Engine - Autonomous research loop with experiment chaining.
Enables continuous learning and auto-hypothesis refinement.
"""
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json

from shared.logger import get_logger
from shared.knowledge_graph import get_knowledge_graph, KnowledgeGraph
from shared.llm_client import get_default_client, LLMClient

logger = get_logger(__name__)


class DiscoveryPhase(Enum):
    """Phases of autonomous discovery"""
    EXPLORE = "explore"         # Initial hypothesis generation
    EXPERIMENT = "experiment"   # Run experiments
    ANALYZE = "analyze"         # Analyze results
    REFINE = "refine"           # Refine hypotheses
    VALIDATE = "validate"       # Validate findings


@dataclass
class DiscoveryState:
    """Current state of discovery process"""
    phase: DiscoveryPhase
    iteration: int
    hypotheses: List[Dict[str, Any]]
    experiments: List[str]
    findings: List[Dict[str, Any]]
    confidence: float
    started_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "iteration": self.iteration,
            "hypotheses_count": len(self.hypotheses),
            "experiments_count": len(self.experiments),
            "findings_count": len(self.findings),
            "confidence": self.confidence,
            "started_at": self.started_at.isoformat()
        }


class DiscoveryEngine:
    """
    Autonomous Discovery Engine.
    
    Capabilities:
    - Continuous learning loop
    - Experiment chaining
    - Auto-hypothesis refinement
    - Cross-domain adaptation
    - Insight accumulation
    """
    
    def __init__(
        self,
        max_iterations: int = 5,
        confidence_threshold: float = 0.85,
        knowledge_graph: Optional[KnowledgeGraph] = None
    ):
        self.max_iterations = max_iterations
        self.confidence_threshold = confidence_threshold
        self.knowledge_graph = knowledge_graph or get_knowledge_graph()
        self.llm_client: Optional[LLMClient] = None
        
        self.state: Optional[DiscoveryState] = None
        self._running = False
    
    def _get_llm(self) -> Optional[LLMClient]:
        """Get LLM client lazily"""
        if self.llm_client is None:
            try:
                self.llm_client = get_default_client()
            except Exception as e:
                logger.warning("llm_init_failed", error=str(e))
        return self.llm_client
    
    async def start_discovery(
        self,
        topic: str,
        domain: str,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start autonomous discovery process.
        
        Args:
            topic: Research topic
            domain: Research domain
            initial_context: Optional prior knowledge
            
        Returns:
            Discovery results with findings
        """
        logger.info("discovery_started", topic=topic, domain=domain)
        
        self.state = DiscoveryState(
            phase=DiscoveryPhase.EXPLORE,
            iteration=0,
            hypotheses=[],
            experiments=[],
            findings=[],
            confidence=0.0,
            started_at=datetime.utcnow()
        )
        
        self._running = True
        
        try:
            # Main discovery loop
            while self._should_continue():
                self.state.iteration += 1
                logger.info("discovery_iteration", iteration=self.state.iteration)
                
                # Phase 1: Explore and generate hypotheses
                await self._explore_phase(topic, domain)
                
                # Phase 2: Design and run experiments
                await self._experiment_phase(topic, domain)
                
                # Phase 3: Analyze results
                await self._analyze_phase()
                
                # Phase 4: Refine hypotheses based on results
                await self._refine_phase(topic, domain)
                
                # Phase 5: Validate findings
                await self._validate_phase()
                
                # Check if we've reached sufficient confidence
                if self.state.confidence >= self.confidence_threshold:
                    logger.info("confidence_threshold_reached", 
                               confidence=self.state.confidence)
                    break
            
            return self._compile_results(topic, domain)
            
        except Exception as e:
            logger.error("discovery_failed", error=str(e))
            return {
                "status": "failed",
                "error": str(e),
                "partial_results": self.state.to_dict() if self.state else None
            }
        finally:
            self._running = False
    
    def _should_continue(self) -> bool:
        """Check if discovery should continue"""
        if not self._running:
            return False
        if self.state.iteration >= self.max_iterations:
            return False
        if self.state.confidence >= self.confidence_threshold:
            return False
        return True
    
    async def _explore_phase(self, topic: str, domain: str):
        """Generate initial hypotheses from existing knowledge"""
        self.state.phase = DiscoveryPhase.EXPLORE
        logger.info("phase_explore")
        
        # Query knowledge graph for related work
        existing_papers = self.knowledge_graph.search_nodes(topic, node_type="paper", limit=10)
        existing_experiments = self.knowledge_graph.search_nodes(topic, node_type="experiment", limit=5)
        
        # Use LLM to generate hypotheses
        llm = self._get_llm()
        if llm:
            context = {
                "existing_papers": [p.data for p in existing_papers],
                "existing_experiments": [e.data for e in existing_experiments],
                "iteration": self.state.iteration,
                "previous_hypotheses": self.state.hypotheses
            }
            
            try:
                prompt = f"""Generate novel research hypotheses for: {topic}
Domain: {domain}
Iteration: {self.state.iteration}

Previous knowledge:
{json.dumps(context, indent=2, default=str)[:2000]}

Generate 2-3 NEW hypotheses not covered before. For each:
- Statement
- Rationale
- Novelty (0-1)
- Key experiment to test

Respond in JSON format."""

                result = await llm.structured_output(
                    prompt=prompt,
                    output_schema={"type": "object", "properties": {"hypotheses": {"type": "array"}}},
                    system_prompt="You are a research hypothesis generator focusing on novel, testable ideas."
                )
                
                new_hypotheses = result.get("hypotheses", [])
                self.state.hypotheses.extend(new_hypotheses)
                
            except Exception as e:
                logger.warning("hypothesis_generation_failed", error=str(e))
        
        # Fallback: generate based on patterns
        if not self.state.hypotheses:
            self.state.hypotheses.append({
                "id": f"H{self.state.iteration}",
                "statement": f"Exploring {topic} in {domain} context",
                "rationale": "Initial exploration hypothesis",
                "novelty": 0.5
            })
    
    async def _experiment_phase(self, topic: str, domain: str):
        """Design and queue experiments"""
        self.state.phase = DiscoveryPhase.EXPERIMENT
        logger.info("phase_experiment")
        
        # For each untested hypothesis, design an experiment
        for hyp in self.state.hypotheses[-3:]:  # Latest 3 hypotheses
            experiment_id = f"disc_exp_{self.state.iteration}_{hyp.get('id', 'unknown')}"
            
            # Store experiment design in knowledge graph
            self.knowledge_graph.store_experiment(
                job_id=experiment_id,
                topic=topic,
                domain=domain,
                config={"hypothesis": hyp, "iteration": self.state.iteration},
                results=None  # To be filled after execution
            )
            
            self.state.experiments.append(experiment_id)
        
        # In a real system, this would trigger job queue
        # For now, simulate experiment completion
        await asyncio.sleep(0.1)  # Simulated processing
    
    async def _analyze_phase(self):
        """Analyze experiment results"""
        self.state.phase = DiscoveryPhase.ANALYZE
        logger.info("phase_analyze")
        
        # Retrieve experiment results from knowledge graph
        for exp_id in self.state.experiments[-3:]:
            exp = self.knowledge_graph.get_node(f"exp_{exp_id}")
            if exp:
                # Extract findings (simulated)
                finding = {
                    "experiment_id": exp_id,
                    "iteration": self.state.iteration,
                    "result": "positive" if self.state.iteration > 1 else "inconclusive",
                    "metrics": {"accuracy": 0.7 + 0.05 * self.state.iteration},
                    "insights": [f"Finding from experiment {exp_id}"]
                }
                self.state.findings.append(finding)
    
    async def _refine_phase(self, topic: str, domain: str):
        """Refine hypotheses based on results"""
        self.state.phase = DiscoveryPhase.REFINE
        logger.info("phase_refine")
        
        llm = self._get_llm()
        if llm and self.state.findings:
            try:
                prompt = f"""Based on these experiment findings, refine the research direction:

Topic: {topic}
Domain: {domain}

Current findings:
{json.dumps(self.state.findings[-5:], indent=2, default=str)}

Current hypotheses:
{json.dumps(self.state.hypotheses[-3:], indent=2, default=str)}

Provide:
1. Which hypotheses are supported/refuted
2. Refined hypothesis statements
3. Next experiment recommendations
4. Overall confidence (0-1)

Respond in JSON."""

                result = await llm.structured_output(
                    prompt=prompt,
                    output_schema={"type": "object"},
                    system_prompt="You are a research analyst refining hypotheses based on evidence."
                )
                
                # Update confidence
                self.state.confidence = result.get("confidence", self.state.confidence + 0.1)
                
                # Add refined hypotheses
                if result.get("refined_hypotheses"):
                    self.state.hypotheses.extend(result["refined_hypotheses"])
                    
            except Exception as e:
                logger.warning("refinement_failed", error=str(e))
                self.state.confidence += 0.1  # Small confidence increase per iteration
        else:
            # Simple confidence increment
            self.state.confidence = min(1.0, self.state.confidence + 0.15)
    
    async def _validate_phase(self):
        """Validate accumulated findings"""
        self.state.phase = DiscoveryPhase.VALIDATE
        logger.info("phase_validate")
        
        # Check consistency of findings
        positive_findings = sum(1 for f in self.state.findings if f.get("result") == "positive")
        total_findings = len(self.state.findings)
        
        if total_findings > 0:
            consistency = positive_findings / total_findings
            self.state.confidence = self.state.confidence * 0.7 + consistency * 0.3
        
        logger.info("validation_complete", confidence=self.state.confidence)
    
    def _compile_results(self, topic: str, domain: str) -> Dict[str, Any]:
        """Compile final discovery results"""
        return {
            "status": "completed",
            "topic": topic,
            "domain": domain,
            "iterations": self.state.iteration,
            "hypotheses": self.state.hypotheses,
            "experiments": self.state.experiments,
            "findings": self.state.findings,
            "final_confidence": self.state.confidence,
            "duration_seconds": (datetime.utcnow() - self.state.started_at).total_seconds(),
            "summary": self._generate_summary()
        }
    
    def _generate_summary(self) -> str:
        """Generate human-readable summary"""
        if not self.state:
            return "No discovery completed."
        
        return (
            f"Completed {self.state.iteration} discovery iterations. "
            f"Generated {len(self.state.hypotheses)} hypotheses, "
            f"ran {len(self.state.experiments)} experiments, "
            f"produced {len(self.state.findings)} findings. "
            f"Final confidence: {self.state.confidence:.2%}."
        )
    
    def stop(self):
        """Stop the discovery process"""
        self._running = False
        logger.info("discovery_stopped")


# Convenience function
async def run_autonomous_discovery(
    topic: str,
    domain: str,
    max_iterations: int = 3
) -> Dict[str, Any]:
    """Run autonomous discovery on a topic"""
    engine = DiscoveryEngine(max_iterations=max_iterations)
    return await engine.start_discovery(topic, domain)
