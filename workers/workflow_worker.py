"""
Workflow worker for processing jobs from the queue.
"""
import asyncio
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from shared.models import Job, JobStatus, WorkflowExecution, WorkflowState
from shared.database import get_db_manager
from shared.queue import get_job_queue
from shared.logger import get_logger
from orchestration.decision_engine import DecisionEngine
from shared.config import SystemConfig

logger = get_logger(__name__)


class WorkflowWorker:
    """Worker that processes jobs from the queue"""
    
    def __init__(self, worker_id: int, config_path: str = "/app/config/config.yaml"):
        """
        Initialize workflow worker.
        
        Args:
            worker_id: Unique worker identifier
            config_path: Path to configuration file
        """
        self.worker_id = worker_id
        self.config_path = config_path
        self.running = False
        self.current_job_id: Optional[str] = None
        
        logger.info("workflow_worker_initialized", worker_id=worker_id)
    
    async def process_job(self, job_id: str) -> bool:
        """
        Process a single job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if successful, False otherwise
        """
        db_manager = get_db_manager()
        
        with db_manager.get_session() as db:
            job = db.query(Job).filter(Job.id == job_id).first()
            
            if not job:
                logger.error("job_not_found", job_id=job_id, worker_id=self.worker_id)
                return False
            
            try:
                # Update job status
                job.status = JobStatus.RUNNING
                job.started_at = datetime.utcnow()
                job.current_state = WorkflowState.INITIALIZED
                db.commit()
                
                logger.info(
                    "job_processing_started",
                    job_id=job_id,
                    worker_id=self.worker_id,
                    topic=job.topic,
                    domain=job.domain
                )
                
                # Load configuration
                config = SystemConfig.load_from_yaml(self.config_path)
                
                # Create decision engine
                engine = DecisionEngine(config.__dict__)
                
                # Execute workflow
                result = await engine.run_workflow(
                    topic=job.topic,
                    domain=job.domain,
                    job_id=job_id
                )
                
                # Update job with result
                from shared.utils import sanitize_for_json
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.utcnow()
                job.current_state = WorkflowState.COMPLETED
                job.result = sanitize_for_json(result)
                db.commit()
                
                logger.info(
                    "job_processing_completed",
                    job_id=job_id,
                    worker_id=self.worker_id,
                    status=result.get("status")
                )
                
                return True
                
            except Exception as e:
                # Update job with error
                job.status = JobStatus.FAILED
                job.current_state = WorkflowState.FAILED
                job.error_message = str(e)
                job.updated_at = datetime.utcnow()
                db.commit()
                
                logger.error(
                    "job_processing_failed",
                    job_id=job_id,
                    worker_id=self.worker_id,
                    error=str(e)
                )
                
                return False
    
    async def run(self):
        """Main worker loop"""
        self.running = True
        job_queue = get_job_queue()
        
        logger.info("workflow_worker_started", worker_id=self.worker_id)
        
        while self.running:
            try:
                # Get next job from queue
                job_id = job_queue.dequeue()
                
                if job_id:
                    self.current_job_id = job_id
                    
                    # Process job
                    success = await self.process_job(job_id)
                    
                    # Mark job as complete in queue
                    job_queue.complete_job(job_id, success=success)
                    
                    self.current_job_id = None
                else:
                    # No jobs available, wait before checking again
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(
                    "worker_loop_error",
                    worker_id=self.worker_id,
                    error=str(e)
                )
                await asyncio.sleep(5)
        
        logger.info("workflow_worker_stopped", worker_id=self.worker_id)
    
    def stop(self):
        """Stop the worker"""
        logger.info("workflow_worker_stopping", worker_id=self.worker_id)
        self.running = False
