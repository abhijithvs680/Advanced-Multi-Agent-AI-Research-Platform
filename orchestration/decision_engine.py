from typing import Dict, Any, Optional
import uuid
import asyncio
from shared.types import WorkflowState, MessageType, Feedback, FeedbackType
from shared.logger import get_logger
from orchestration.state_manager import StateManager
from orchestration.communication import CommunicationBus
from orchestration.feedback_handler import FeedbackHandler
from agents.research_agent.agent import ResearchAgent
from agents.data_agent.agent import DataAgent
from agents.training_agent.agent import TrainingAgent
from agents.evaluation_agent.agent import EvaluationAgent
from shared.database import get_db_manager
from shared.models import Job
from datetime import datetime


class DecisionEngine:
    """Orchestrates workflow and coordinates agents"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger("DecisionEngine")
        self.config = config
        self.state_manager = StateManager()
        self.communication_bus = CommunicationBus()
        self.feedback_handler = FeedbackHandler()
        self.current_job_id: Optional[str] = None
        
        # Initialize agents
        self.agents = {
            "research": ResearchAgent("research", config.get('agents', {}).get('research', {})),
            "data": DataAgent("data", config.get('agents', {}).get('data', {})),
            "training": TrainingAgent("training", config.get('agents', {}).get('training', {})),
            "evaluation": EvaluationAgent("evaluation", config.get('agents', {}).get('evaluation', {}))
        }
    
    async def _emit_state_transition(self, state: WorkflowState, message: str, progress: Optional[float] = None):
        """Emit WebSocket event and update database for state transition"""
        if self.current_job_id:
            # 1. Update Database
            try:
                db_manager = get_db_manager()
                with db_manager.get_session() as session:
                    job = session.query(Job).filter(Job.id == self.current_job_id).first()
                    if job:
                        job.current_state = state
                        if progress is not None:
                            job.progress = int(progress) if isinstance(progress, (int, float)) else None
                        job.message = message
                        job.updated_at = datetime.utcnow()
                        session.commit()
            except Exception as e:
                self.logger.error("db_persist_failed", job_id=self.current_job_id, error=str(e))

            # 2. Emit WebSocket Event
            try:
                from api.routes.websocket import emit_job_status
                await emit_job_status(
                    job_id=self.current_job_id,
                    status="RUNNING",
                    current_state=state.value if hasattr(state, 'value') else str(state),
                    progress=progress,
                    message=message
                )
            except Exception as e:
                self.logger.warning("ws_emit_failed", error=str(e))
    
    
    async def run_workflow(self, topic: str, domain: str = "general",
                          job_id: Optional[str] = None,
                          max_iterations: int = 5) -> Dict[str, Any]:
        """
        Run workflow with optional job tracking.
        
        Args:
            topic: Research topic
            domain: Research domain
            job_id: Optional job ID for tracking
            max_iterations: Maximum number of iterations
            
        Returns:
            Workflow result dictionary
        """
        # Store job_id for WebSocket emissions
        self.current_job_id = job_id
        
        if job_id:
            self.logger.info("workflow_started_for_job", job_id=job_id, topic=topic)
            # Emit initial state
            await self._emit_state_transition(WorkflowState.INITIALIZED, "Workflow started", 0.0)
        
        return await self.execute_workflow(topic, domain, max_iterations)
    
    async def execute_workflow(self, topic: str, domain: str = "general", 
                              max_iterations: int = 5) -> Dict[str, Any]:
        """Execute complete research workflow"""
        workflow_id = str(uuid.uuid4())
        self.logger.info("workflow_started", id=workflow_id, topic=topic)
        
        self.feedback_handler.max_iterations = max_iterations
        
        try:
            # Phase 1: Research
            self.state_manager.transition(WorkflowState.RESEARCHING, "Starting research phase")
            await self._emit_state_transition(WorkflowState.RESEARCHING, "Researching literature and generating hypotheses", 10.0)
            research_result = await self._execute_research_phase(topic, domain)
            
            if research_result.status == "failure":
                self.state_manager.transition(WorkflowState.FAILED, "Research phase failed")
                await self._emit_state_transition(WorkflowState.FAILED, "Research phase failed", 100.0)
                return self._create_failure_result(workflow_id, "Research phase failed")
            
            # Phase 2: Data Collection
            self.state_manager.transition(WorkflowState.COLLECTING_DATA, "Starting data collection")
            await self._emit_state_transition(WorkflowState.COLLECTING_DATA, "Collecting and preparing data", 30.0)
            data_result = await self._execute_data_phase(research_result.data)
            
            if data_result.status == "failure":
                self.state_manager.transition(WorkflowState.FAILED, "Data phase failed")
                await self._emit_state_transition(WorkflowState.FAILED, "Data phase failed", 100.0)
                return self._create_failure_result(workflow_id, "Data phase failed")
            
            # Handle partial data quality
            if data_result.status == "partial":
                feedback = Feedback(
                    source_agent="data",
                    target_agent="research",
                    feedback_type=FeedbackType.REWORK,
                    message="Data quality below threshold",
                    data=data_result.data
                )
                action = await self.feedback_handler.process_feedback(feedback)
                
                if action['action'] == 'escalate':
                    return self._create_escalation_result(workflow_id, action)
            
            # Phase 3: Training
            self.state_manager.transition(WorkflowState.TRAINING, "Starting training phase")
            await self._emit_state_transition(WorkflowState.TRAINING, "Training machine learning models", 50.0)
            training_result = await self._execute_training_phase(data_result.data)
            
            if training_result.status == "failure":
                self.state_manager.transition(WorkflowState.FAILED, "Training phase failed")
                await self._emit_state_transition(WorkflowState.FAILED, "Training phase failed", 100.0)
                return self._create_failure_result(workflow_id, "Training phase failed")
            
            # Phase 4: Evaluation
            self.state_manager.transition(WorkflowState.EVALUATING, "Starting evaluation phase")
            await self._emit_state_transition(WorkflowState.EVALUATING, "Evaluating model performance", 80.0)
            evaluation_result = await self._execute_evaluation_phase(training_result.data)
            
            if evaluation_result.status == "failure":
                self.state_manager.transition(WorkflowState.FAILED, "Evaluation phase failed")
                await self._emit_state_transition(WorkflowState.FAILED, "Evaluation phase failed", 100.0)
                return self._create_failure_result(workflow_id, "Evaluation phase failed")
            
            # Check if iteration needed
            if evaluation_result.status == "partial":
                if self.feedback_handler.should_iterate(evaluation_result.metrics):
                    feedback = Feedback(
                        source_agent="evaluation",
                        target_agent="training",
                        feedback_type=FeedbackType.REWORK,
                        message="Results below threshold, requesting retraining"
                    )
                    action = await self.feedback_handler.process_feedback(feedback)
                    
                    if action['action'] == 'retry':
                        # Retry training with feedback
                        training_result = await self._execute_training_phase(
                            data_result.data, 
                            feedback=action
                        )
                        evaluation_result = await self._execute_evaluation_phase(training_result.data)
            
            # Workflow completed
            self.state_manager.transition(WorkflowState.COMPLETED, "Workflow completed successfully")
            await self._emit_state_transition(WorkflowState.COMPLETED, "Workflow completed successfully", 100.0)
            
            return {
                "workflow_id": workflow_id,
                "status": "COMPLETED",
                "final_results": {
                    "research": research_result.data,
                    "data": data_result.metrics,
                    "training": training_result.metrics,
                    "evaluation": evaluation_result.data
                },
                "best_model": evaluation_result.data.get('recommendation'),
                "iterations": self.feedback_handler.get_iteration_count(),
                "state_history": self.state_manager.get_state_history()
            }
            
        except Exception as e:
            self.logger.error("workflow_failed", error=str(e), workflow_id=workflow_id)
            self.state_manager.transition(WorkflowState.FAILED, f"Error: {str(e)}")
            return self._create_failure_result(workflow_id, str(e))
    
    async def _execute_research_phase(self, topic: str, domain: str) -> Any:
        """Execute research agent phase"""
        task = {
            "id": str(uuid.uuid4()),
            "query": topic,
            "domain": domain
        }
        return await self.agents["research"].process_task(task)
    
    async def _execute_data_phase(self, research_data: Dict[str, Any]) -> Any:
        """Execute data agent phase"""
        task = {
            "id": str(uuid.uuid4()),
            "data_requirements": research_data.get('data_requirements', {})
        }
        return await self.agents["data"].process_task(task)
    
    async def _execute_training_phase(self, data_result: Dict[str, Any], 
                                     feedback: Optional[Dict] = None) -> Any:
        """Execute training agent phase"""
        task = {
            "id": str(uuid.uuid4()),
            "job_id": self.current_job_id,
            "features": data_result.get('features'),
            "strategy": data_result.get('strategy', {}),
            "feedback": feedback
        }
        return await self.agents["training"].process_task(task)
    
    async def _execute_evaluation_phase(self, training_data: Dict[str, Any]) -> Any:
        """Execute evaluation agent phase"""
        task = {
            "id": str(uuid.uuid4()),
            "job_id": self.current_job_id,
            "models": training_data.get('all_models', []),
            "evaluation_criteria": {
                "acceptance_threshold": 0.85
            }
        }
        return await self.agents["evaluation"].process_task(task)
    
    def _create_failure_result(self, workflow_id: str, reason: str) -> Dict[str, Any]:
        """Create failure result"""
        return {
            "workflow_id": workflow_id,
            "status": "FAILED",
            "reason": reason,
            "state_history": self.state_manager.get_state_history()
        }
    
    def _create_escalation_result(self, workflow_id: str, action: Dict) -> Dict[str, Any]:
        """Create escalation result"""
        return {
            "workflow_id": workflow_id,
            "status": "escalated",
            "reason": action.get('reason'),
            "requires_human_review": True,
            "state_history": self.state_manager.get_state_history()
        }
