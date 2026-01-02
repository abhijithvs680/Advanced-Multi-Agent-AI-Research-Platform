"""
Health check and metrics API routes.
"""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from api.schemas import HealthResponse, ReadinessResponse, MetricsResponse
from shared.models import Job, JobStatus
from shared.database import get_db_session, get_db_manager
from shared.queue import get_job_queue
from shared.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        Service health status
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow()
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(db: Session = Depends(get_db_session)):
    """
    Readiness check - verifies all dependencies are accessible.
    
    Returns:
        Readiness status for each dependency
    """
    # Check database
    db_healthy = False
    try:
        db_manager = get_db_manager()
        db_healthy = db_manager.health_check()
    except Exception as e:
        logger.error("readiness_check_database_failed", error=str(e))
    
    # Check queue
    queue_healthy = False
    try:
        job_queue = get_job_queue()
        queue_healthy = job_queue.health_check()
    except Exception as e:
        logger.error("readiness_check_queue_failed", error=str(e))
    
    # Check MLflow (stubbed for now)
    mlflow_healthy = True  # TODO: Add actual MLflow health check
    
    ready = db_healthy and queue_healthy and mlflow_healthy
    
    return ReadinessResponse(
        ready=ready,
        database=db_healthy,
        queue=queue_healthy,
        mlflow=mlflow_healthy,
        timestamp=datetime.utcnow()
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(db: Session = Depends(get_db_session)):
    """
    Get system metrics.
    
    Returns:
        Current system metrics
    """
    # Queue metrics
    job_queue = get_job_queue()
    queue_length = job_queue.get_queue_length()
    running_jobs_count = len(job_queue.get_running_jobs())
    
    # Job metrics from last 24 hours
    cutoff = datetime.utcnow() - timedelta(hours=24)
    
    completed_24h = db.query(func.count(Job.id))\
                      .filter(Job.status == JobStatus.COMPLETED)\
                      .filter(Job.completed_at >= cutoff)\
                      .scalar() or 0
    
    failed_24h = db.query(func.count(Job.id))\
                  .filter(Job.status == JobStatus.FAILED)\
                  .filter(Job.updated_at >= cutoff)\
                  .scalar() or 0
    
    # Average duration for completed jobs in last 24h
    avg_duration_query = db.query(
        func.avg(
            func.extract('epoch', Job.completed_at - Job.started_at)
        ) / 60.0  # Convert to minutes
    ).filter(
        Job.status == JobStatus.COMPLETED,
        Job.completed_at >= cutoff,
        Job.started_at.isnot(None),
        Job.completed_at.isnot(None)
    ).scalar()
    
    avg_duration = round(avg_duration_query, 2) if avg_duration_query else 0.0
    
    return MetricsResponse(
        queue_length=queue_length,
        running_jobs=running_jobs_count,
        completed_jobs_24h=completed_24h,
        failed_jobs_24h=failed_24h,
        average_duration_minutes=avg_duration
    )


@router.get("/metrics/prometheus")
async def prometheus_metrics(db: Session = Depends(get_db_session)):
    """
    Prometheus-compatible metrics endpoint.
    
    Returns:
        Metrics in Prometheus text format
    """
    # Get metrics
    metrics = await get_metrics(db)
    
    # Format as Prometheus metrics
    output = []
    
    output.append("# HELP job_queue_length Current number of jobs in queue")
    output.append("# TYPE job_queue_length gauge")
    output.append(f"job_queue_length {metrics.queue_length}")
    
    output.append("# HELP jobs_running Current number of running jobs")
    output.append("# TYPE jobs_running gauge")
    output.append(f"jobs_running {metrics.running_jobs}")
    
    output.append("# HELP jobs_completed_24h Jobs completed in last 24 hours")
    output.append("# TYPE jobs_completed_24h counter")
    output.append(f"jobs_completed_24h {metrics.completed_jobs_24h}")
    
    output.append("# HELP jobs_failed_24h Jobs failed in last 24 hours")
    output.append("# TYPE jobs_failed_24h counter")
    output.append(f"jobs_failed_24h {metrics.failed_jobs_24h}")
    
    output.append("# HELP job_duration_minutes_avg Average job duration in minutes")
    output.append("# TYPE job_duration_minutes_avg gauge")
    output.append(f"job_duration_minutes_avg {metrics.average_duration_minutes}")
    
    return Response(content="\n".join(output) + "\n", media_type="text/plain")
