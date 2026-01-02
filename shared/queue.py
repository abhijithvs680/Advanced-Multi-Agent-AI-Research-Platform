"""
Job queue implementation using Redis.
"""
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import redis
from redis import Redis
import os

from shared.logger import get_logger
from shared.models import Job, JobStatus

logger = get_logger(__name__)


class JobQueue:
    """Redis-based job queue for workflow execution"""
    
    # Queue names
    PENDING_QUEUE = "jobs:pending"
    RUNNING_QUEUE = "jobs:running"
    COMPLETED_QUEUE = "jobs:completed"
    FAILED_QUEUE = "jobs:failed"
    
    # Key prefixes
    JOB_DATA_PREFIX = "job:data:"
    JOB_STATUS_PREFIX = "job:status:"
    
    def __init__(self, redis_url: str = None):
        """
        Initialize job queue.
        
        Args:
            redis_url: Redis connection URL (defaults to env var REDIS_URL)
        """
        self.redis_url = redis_url or os.getenv(
            "REDIS_URL",
            "redis://redis:6379/0"
        )
        
        self.redis_client: Redis = redis.from_url(
            self.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
        )
        
        logger.info("job_queue_initialized", redis_url=self.redis_url.split("@")[-1])
    
    def enqueue(self, job_id: str, priority: int = 0) -> bool:
        """
        Add a job to the pending queue.
        
        Args:
            job_id: Unique job identifier
            priority: Job priority (higher = more urgent), default 0
            
        Returns:
            True if successfully enqueued
        """
        try:
            # Add to pending queue with priority (sorted set)
            self.redis_client.zadd(
                self.PENDING_QUEUE,
                {job_id: priority}
            )
            
            # Set job status
            self.set_job_status(job_id, JobStatus.PENDING)
            
            logger.info("job_enqueued", job_id=job_id, priority=priority)
            return True
            
        except Exception as e:
            logger.error("job_enqueue_failed", job_id=job_id, error=str(e))
            return False
    
    def dequeue(self) -> Optional[str]:
        """
        Get the next job from the pending queue.
        
        Returns:
            Job ID if available, None otherwise
        """
        try:
            # Get highest priority job (ZREVRANGE returns high to low)
            result = self.redis_client.zpopmax(self.PENDING_QUEUE)
            
            if not result:
                return None
            
            job_id, priority = result[0]
            
            # Move to running queue
            self.redis_client.sadd(self.RUNNING_QUEUE, job_id)
            self.set_job_status(job_id, JobStatus.RUNNING)
            
            logger.info("job_dequeued", job_id=job_id, priority=priority)
            return job_id
            
        except Exception as e:
            logger.error("job_dequeue_failed", error=str(e))
            return None
    
    def complete_job(self, job_id: str, success: bool = True):
        """
        Mark a job as completed or failed.
        
        Args:
            job_id: Job identifier
            success: True if completed successfully, False if failed
        """
        try:
            # Remove from running queue
            self.redis_client.srem(self.RUNNING_QUEUE, job_id)
            
            if success:
                self.redis_client.sadd(self.COMPLETED_QUEUE, job_id)
                self.set_job_status(job_id, JobStatus.COMPLETED)
                logger.info("job_completed", job_id=job_id)
            else:
                self.redis_client.sadd(self.FAILED_QUEUE, job_id)
                self.set_job_status(job_id, JobStatus.FAILED)
                logger.info("job_failed", job_id=job_id)
                
        except Exception as e:
            logger.error("job_complete_failed", job_id=job_id, error=str(e))
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending or running job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if successfully cancelled
        """
        try:
            # Remove from pending queue
            self.redis_client.zrem(self.PENDING_QUEUE, job_id)
            
            # Remove from running queue
            self.redis_client.srem(self.RUNNING_QUEUE, job_id)
            
            # Set status
            self.set_job_status(job_id, JobStatus.CANCELLED)
            
            logger.info("job_cancelled", job_id=job_id)
            return True
            
        except Exception as e:
            logger.error("job_cancel_failed", job_id=job_id, error=str(e))
            return False
    
    def get_job_status(self, job_id: str) -> Optional[str]:
        """Get current status of a job from Redis"""
        try:
            status = self.redis_client.get(f"{self.JOB_STATUS_PREFIX}{job_id}")
            return status
        except Exception as e:
            logger.error("get_job_status_failed", job_id=job_id, error=str(e))
            return None
    
    def set_job_status(self, job_id: str, status: JobStatus):
        """Set job status in Redis with TTL"""
        try:
            self.redis_client.setex(
                f"{self.JOB_STATUS_PREFIX}{job_id}",
                timedelta(days=7),  # Keep status for 7 days
                status.value
            )
        except Exception as e:
            logger.error("set_job_status_failed", job_id=job_id, error=str(e))
    
    def get_queue_length(self, queue_name: str = PENDING_QUEUE) -> int:
        """Get the number of jobs in a queue"""
        try:
            if queue_name == self.PENDING_QUEUE:
                return self.redis_client.zcard(queue_name)
            else:
                return self.redis_client.scard(queue_name)
        except Exception as e:
            logger.error("get_queue_length_failed", queue=queue_name, error=str(e))
            return 0
    
    def get_running_jobs(self) -> List[str]:
        """Get list of currently running jobs"""
        try:
            return list(self.redis_client.smembers(self.RUNNING_QUEUE))
        except Exception as e:
            logger.error("get_running_jobs_failed", error=str(e))
            return []
    
    def health_check(self) -> bool:
        """Check if Redis is accessible"""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error("queue_health_check_failed", error=str(e))
            return False


# Global queue instance
_job_queue: JobQueue = None


def get_job_queue() -> JobQueue:
    """Get or create global job queue instance"""
    global _job_queue
    if _job_queue is None:
        _job_queue = JobQueue()
    return _job_queue
