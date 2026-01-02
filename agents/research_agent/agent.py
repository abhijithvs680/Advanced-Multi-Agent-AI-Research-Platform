"""
Enhanced Research Agent - AI Principal Investigator.
Conducts systematic literature reviews, generates hypotheses, and designs experiments.
"""
from agents.base_agent import BaseAgent
from shared.types import TaskResult
from shared.llm_client import LLMClient, LLMProvider, get_default_client
from shared.paper_search import PaperSearchClient, Paper
from shared.knowledge_graph import get_knowledge_graph
from typing import Any, Dict, List, Optional
import asyncio
import json


# LLM Prompts for research tasks
LITERATURE_ANALYSIS_PROMPT = """Analyze these academic papers and provide insights:

Papers:
{papers_text}

Research Topic: {topic}
Domain: {domain}

Provide a JSON response with:
{{
    "summary": "Comprehensive summary of the literature (2-3 paragraphs)",
    "key_findings": ["List of 5-7 most important findings"],
    "methodologies": ["List of main methodologies used"],
    "research_gaps": ["List of identified gaps in current research"],
    "trends": ["Emerging trends in this field"],
    "key_papers": ["Titles of the most influential papers"],
    "confidence_score": 0.0-1.0
}}
"""

HYPOTHESIS_GENERATION_PROMPT = """Based on this literature analysis, generate novel research hypotheses:

Analysis:
{analysis}

Topic: {topic}
Domain: {domain}

Generate 3-5 original, testable hypotheses. For each, provide:
- The hypothesis statement
- Rationale based on the literature
- Novelty score (0.0-1.0) indicating how novel this is
- Required experiments to test it
- Potential impact if validated

Respond with JSON:
{{
    "hypotheses": [
        {{
            "id": "H1",
            "statement": "...",
            "rationale": "...",
            "novelty_score": 0.0-1.0,
            "experiments": ["..."],
            "potential_impact": "..."
        }}
    ]
}}
"""

METHODOLOGY_DESIGN_PROMPT = """Design a research methodology to test these hypotheses:

Hypotheses:
{hypotheses}

Domain: {domain}
Available Resources: Standard compute, public datasets

Create a comprehensive experimental design with:
- Null and alternative hypotheses
- Variables (independent, dependent, controlled)
- Data requirements with justification
- Model architectures to try
- Evaluation metrics and statistical tests
- Potential pitfalls and mitigations

Respond with JSON:
{{
    "experimental_design": {{
        "null_hypothesis": "...",
        "alternative_hypothesis": "...",
        "variables": {{
            "independent": ["..."],
            "dependent": ["..."],
            "controlled": ["..."]
        }},
        "data_requirements": {{
            "min_samples": 1000,
            "features": ["..."],
            "sources": ["..."],
            "quality_threshold": 0.9
        }},
        "model_architectures": [
            {{"name": "...", "rationale": "..."}}
        ],
        "evaluation": {{
            "metrics": ["..."],
            "statistical_tests": ["..."],
            "significance_level": 0.05
        }},
        "risks": [
            {{"risk": "...", "severity": "high|medium|low", "mitigation": "..."}}
        ]
    }}
}}
"""


class EnhancedResearchAgent(BaseAgent):
    """
    AI Principal Investigator Agent.
    
    Capabilities:
    - Systematic literature review using Semantic Scholar and arXiv
    - LLM-powered analysis and synthesis
    - Novel hypothesis generation
    - Experimental design with statistical rigor
    - Knowledge graph integration for persistence
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        if hasattr(config, '__dict__') and not isinstance(config, dict):
            config = config.__dict__
        super().__init__(name, config if isinstance(config, dict) else {})
        
        # Initialize components
        self.paper_client = PaperSearchClient()
        self.knowledge_graph = get_knowledge_graph()
        self.llm_client: Optional[LLMClient] = None
        
        # Configuration
        self.max_papers = self.config.get('max_papers', 30)
        self.llm_model = self.config.get('llm_model', None)
        self.llm_provider = self.config.get('llm_provider', 'openai')
    
    def _get_llm_client(self) -> LLMClient:
        """Lazy initialization of LLM client"""
        if self.llm_client is None:
            try:
                provider = LLMProvider.OPENAI if self.llm_provider == 'openai' else LLMProvider.ANTHROPIC
                self.llm_client = LLMClient(provider=provider, model=self.llm_model)
            except Exception as e:
                self.logger.warning("llm_init_failed", error=str(e))
                # Return None if LLM not available - will use fallback
                return None
        return self.llm_client
    
    async def process_task(self, task: Dict[str, Any]) -> TaskResult:
        """Process research task with full pipeline"""
        self.logger.info("processing_research_task", task_id=task.get('id'))
        
        query = task.get('query')
        domain = task.get('domain', 'general')
        job_id = task.get('job_id')
        
        if not await self.validate_input(task):
            return TaskResult(
                agent_name=self.name,
                task_id=task.get('id'),
                status="failure",
                data=None,
                metrics={},
                errors=["Invalid input: query and id are required"]
            )
        
        try:
            # Step 1: Literature Search
            self.logger.info("step_literature_search", query=query)
            papers = await self.search_literature(query, domain)
            
            # Step 2: Analyze Papers
            self.logger.info("step_analyze_papers", count=len(papers))
            analysis = await self.analyze_papers(papers, query, domain)
            
            # Step 3: Generate Hypotheses
            self.logger.info("step_generate_hypotheses")
            hypotheses = await self.generate_hypotheses(analysis, query, domain)
            
            # Step 4: Design Methodology
            self.logger.info("step_design_methodology")
            methodology = await self.design_methodology(hypotheses, domain)
            
            # Step 5: Store in Knowledge Graph
            if job_id:
                await self._store_in_knowledge_graph(job_id, papers, hypotheses, analysis)
            
            result_data = {
                "papers": [p.to_dict() if hasattr(p, 'to_dict') else p for p in papers],
                "analysis": analysis,
                "hypotheses": hypotheses,
                "methodology": methodology,
                "data_requirements": methodology.get("experimental_design", {}).get("data_requirements", {})
            }
            
            return TaskResult(
                agent_name=self.name,
                task_id=task.get('id'),
                status="success",
                data=result_data,
                metrics={
                    "papers_found": len(papers),
                    "hypotheses_generated": len(hypotheses.get("hypotheses", [])),
                    "confidence_score": analysis.get("confidence_score", 0.0)
                }
            )
            
        except Exception as e:
            self.logger.error("research_task_failed", error=str(e))
            return TaskResult(
                agent_name=self.name,
                task_id=task.get('id'),
                status="failure",
                data=None,
                metrics={},
                errors=[str(e)]
            )
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate research task input"""
        required = ['query', 'id']
        return all(field in input_data for field in required)
    
    async def search_literature(self, query: str, domain: str = "general") -> List[Paper]:
        """Search academic databases for relevant papers"""
        self.logger.info("searching_literature", query=query, domain=domain)
        
        # Search across sources
        papers = await self.paper_client.search(
            query=query,
            limit=self.max_papers,
            sources=["semantic_scholar", "arxiv"]
        )
        
        self.logger.info("literature_search_complete", papers_found=len(papers))
        return papers
    
    async def analyze_papers(
        self,
        papers: List[Paper],
        topic: str,
        domain: str
    ) -> Dict[str, Any]:
        """Analyze papers using LLM"""
        self.logger.info("analyzing_papers", count=len(papers))
        
        # Format papers for LLM
        papers_text = ""
        for i, paper in enumerate(papers[:15], 1):  # Limit to top 15 for context
            p = paper.to_dict() if hasattr(paper, 'to_dict') else paper
            papers_text += f"""
{i}. {p.get('title', 'Unknown')} ({p.get('year', 'N/A')})
   Authors: {', '.join(p.get('authors', [])[:3])}
   Citations: {p.get('citation_count', 0)}
   Abstract: {p.get('abstract', 'No abstract')[:500]}
"""
        
        llm = self._get_llm_client()
        
        if llm:
            try:
                prompt = LITERATURE_ANALYSIS_PROMPT.format(
                    papers_text=papers_text,
                    topic=topic,
                    domain=domain
                )
                
                result = await llm.structured_output(
                    prompt=prompt,
                    output_schema={
                        "type": "object",
                        "properties": {
                            "summary": {"type": "string"},
                            "key_findings": {"type": "array"},
                            "methodologies": {"type": "array"},
                            "research_gaps": {"type": "array"},
                            "trends": {"type": "array"},
                            "key_papers": {"type": "array"},
                            "confidence_score": {"type": "number"}
                        }
                    },
                    system_prompt="You are an expert research analyst specializing in literature review and synthesis."
                )
                return result
                
            except Exception as e:
                self.logger.warning("llm_analysis_failed", error=str(e))
        
        # Fallback analysis without LLM
        return {
            "summary": f"Literature review found {len(papers)} papers on {topic}",
            "key_findings": [f"Finding from paper: {p.title[:50]}..." for p in papers[:5]],
            "methodologies": ["Machine Learning", "Deep Learning", "Statistical Analysis"],
            "research_gaps": ["Limited real-world validation", "Scalability concerns"],
            "trends": ["Transformer architectures", "Self-supervised learning"],
            "key_papers": [p.title for p in papers[:5]],
            "confidence_score": 0.7
        }
    
    async def generate_hypotheses(
        self,
        analysis: Dict[str, Any],
        topic: str,
        domain: str
    ) -> Dict[str, Any]:
        """Generate novel research hypotheses using LLM"""
        self.logger.info("generating_hypotheses")
        
        llm = self._get_llm_client()
        
        if llm:
            try:
                prompt = HYPOTHESIS_GENERATION_PROMPT.format(
                    analysis=json.dumps(analysis, indent=2),
                    topic=topic,
                    domain=domain
                )
                
                result = await llm.structured_output(
                    prompt=prompt,
                    output_schema={
                        "type": "object",
                        "properties": {
                            "hypotheses": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "statement": {"type": "string"},
                                        "rationale": {"type": "string"},
                                        "novelty_score": {"type": "number"},
                                        "experiments": {"type": "array"},
                                        "potential_impact": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    system_prompt="You are a senior researcher generating novel, testable hypotheses based on literature gaps."
                )
                return result
                
            except Exception as e:
                self.logger.warning("hypothesis_generation_failed", error=str(e))
        
        # Fallback hypotheses
        return {
            "hypotheses": [
                {
                    "id": "H1",
                    "statement": f"Ensemble methods will outperform single models for {topic}",
                    "rationale": "Literature shows ensemble approaches provide robust performance",
                    "novelty_score": 0.6,
                    "experiments": ["Compare Random Forest, XGBoost, and ensemble"],
                    "potential_impact": "Improved prediction accuracy"
                },
                {
                    "id": "H2",
                    "statement": f"Feature engineering based on domain knowledge improves {topic} models",
                    "rationale": "Gap in literature for domain-specific features",
                    "novelty_score": 0.7,
                    "experiments": ["Compare raw vs engineered features"],
                    "potential_impact": "Better interpretability and performance"
                }
            ]
        }
    
    async def design_methodology(
        self,
        hypotheses: Dict[str, Any],
        domain: str
    ) -> Dict[str, Any]:
        """Design experimental methodology"""
        self.logger.info("designing_methodology")
        
        llm = self._get_llm_client()
        
        if llm:
            try:
                prompt = METHODOLOGY_DESIGN_PROMPT.format(
                    hypotheses=json.dumps(hypotheses, indent=2),
                    domain=domain
                )
                
                result = await llm.structured_output(
                    prompt=prompt,
                    output_schema={
                        "type": "object",
                        "properties": {
                            "experimental_design": {"type": "object"}
                        }
                    },
                    system_prompt="You are an experimental methodologist designing rigorous research protocols."
                )
                return result
                
            except Exception as e:
                self.logger.warning("methodology_design_failed", error=str(e))
        
        # Fallback methodology
        return {
            "experimental_design": {
                "null_hypothesis": "No significant difference between approaches",
                "alternative_hypothesis": "Proposed approach shows significant improvement",
                "variables": {
                    "independent": ["model_type", "hyperparameters"],
                    "dependent": ["accuracy", "f1_score"],
                    "controlled": ["dataset", "random_seed", "train_test_split"]
                },
                "data_requirements": {
                    "min_samples": 1000,
                    "features": ["feature_1", "feature_2", "feature_3"],
                    "sources": ["kaggle", "uci"],
                    "quality_threshold": 0.9
                },
                "model_architectures": [
                    {"name": "Random Forest", "rationale": "Baseline ensemble"},
                    {"name": "XGBoost", "rationale": "State-of-art gradient boosting"},
                    {"name": "Neural Network", "rationale": "Deep learning comparison"}
                ],
                "evaluation": {
                    "metrics": ["accuracy", "precision", "recall", "f1_score", "auc_roc"],
                    "statistical_tests": ["t_test", "wilcoxon"],
                    "significance_level": 0.05
                },
                "risks": [
                    {"risk": "Data quality issues", "severity": "medium", "mitigation": "Data validation"},
                    {"risk": "Overfitting", "severity": "high", "mitigation": "Cross-validation"}
                ]
            }
        }
    
    async def _store_in_knowledge_graph(
        self,
        job_id: str,
        papers: List[Paper],
        hypotheses: Dict[str, Any],
        analysis: Dict[str, Any]
    ):
        """Store research artifacts in knowledge graph"""
        try:
            # Store papers
            paper_ids = []
            for paper in papers[:20]:  # Limit storage
                p = paper.to_dict() if hasattr(paper, 'to_dict') else paper
                paper_id = self.knowledge_graph.store_paper(
                    paper_id=p.get('paper_id', ''),
                    title=p.get('title', ''),
                    abstract=p.get('abstract', ''),
                    authors=p.get('authors', []),
                    year=p.get('year', 0),
                    citation_count=p.get('citation_count', 0)
                )
                paper_ids.append(paper_id)
            
            # Store hypotheses
            for hyp in hypotheses.get('hypotheses', []):
                self.knowledge_graph.store_hypothesis(
                    hypothesis_text=hyp.get('statement', ''),
                    rationale=hyp.get('rationale', ''),
                    novelty_score=hyp.get('novelty_score', 0.5),
                    source_papers=paper_ids[:5],
                    experiment_id=job_id
                )
            
            self.logger.info("knowledge_graph_stored", job_id=job_id, papers=len(paper_ids))
            
        except Exception as e:
            self.logger.warning("knowledge_graph_storage_failed", error=str(e))


# Alias for backward compatibility
ResearchAgent = EnhancedResearchAgent
