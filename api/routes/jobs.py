"""
Job management API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta

from api.schemas import (
    JobCreate, JobResponse, JobListResponse, JobUpdate
)
from shared.models import Job, JobStatus, WorkflowExecution
from shared.database import get_db_session
from shared.queue import get_job_queue
from shared.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db_session)
):
    """
    Create a new research job and add it to the queue.
    
    Args:
        job_data: Job creation data
        db: Database session
        
    Returns:
        Created job details
    """
    try:
        # Create job in database
        job = Job(
            topic=job_data.topic,
            domain=job_data.domain,
            config=job_data.config,
            status=JobStatus.PENDING
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Add to job queue
        job_queue = get_job_queue()
        job_queue.enqueue(job.id, priority=job_data.priority)
        
        logger.info("job_created", job_id=job.id, topic=job.topic, domain=job.domain)
        
        return job
        
    except Exception as e:
        logger.error("job_creation_failed", error=str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create job")


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Get details of a specific job.
    
    Args:
        job_id: Job identifier
        db: Database session
        
    Returns:
        Job details
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db_session)
):
    """
    List all jobs with optional filters.
    
    Args:
        status: Filter by job status
        domain: Filter by research domain
        page: Page number
        page_size: Number of items per page
        db: Database session
        
    Returns:
        Paginated list of jobs
    """
    query = db.query(Job)
    
    # Apply filters
    if status:
        try:
            status_enum = JobStatus(status)
            query = query.filter(Job.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    if domain:
        query = query.filter(Job.domain == domain)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    jobs = query.order_by(desc(Job.created_at))\
                .offset((page - 1) * page_size)\
                .limit(page_size)\
                .all()
    
    return JobListResponse(
        jobs=jobs,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/jobs/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(
    job_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Cancel a pending or running job.
    
    Args:
        job_id: Job identifier
        db: Database session
        
    Returns:
        Updated job details
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job with status: {job.status.value}"
        )
    
    # Remove from queue
    job_queue = get_job_queue()
    job_queue.cancel_job(job_id)
    
    # Update database
    job.status = JobStatus.CANCELLED
    job.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(job)
    
    logger.info("job_cancelled_via_api", job_id=job_id)
    
    return job


@router.post("/jobs/{job_id}/retry", response_model=JobResponse)
async def retry_job(
    job_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Retry a failed job.
    
    Args:
        job_id: Job identifier
        db: Database session
        
    Returns:
        Updated job details
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.FAILED:
        raise HTTPException(
            status_code=400,
            detail=f"Can only retry failed jobs, current status: {job.status.value}"
        )
    
    if job.retry_count >= job.max_retries:
        raise HTTPException(
            status_code=400,
            detail=f"Max retries ({job.max_retries}) exceeded"
        )
    
    # Update job
    job.status = JobStatus.PENDING
    job.retry_count += 1
    job.error_message = None
    job.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(job)
    
    # Re-enqueue
    job_queue = get_job_queue()
    job_queue.enqueue(job_id, priority=1)  # Higher priority for retries
    
    logger.info("job_retried_via_api", job_id=job_id, retry_count=job.retry_count)
    
    return job


@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(
    job_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Delete a job and its executions.
    
    Args:
        job_id: Job identifier
        db: Database session
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status == JobStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete running job. Cancel it first."
        )
    
    db.delete(job)
    db.commit()
    
    logger.info("job_deleted_via_api", job_id=job_id)


@router.get("/jobs/{job_id}/executions")
async def get_job_executions(
    job_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Get workflow executions for a job.
    
    Args:
        job_id: Job identifier
        db: Database session
        
    Returns:
        List of workflow executions
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    executions = db.query(WorkflowExecution)\
                  .filter(WorkflowExecution.job_id == job_id)\
                  .order_by(WorkflowExecution.iteration)\
                  .all()
    
    return {
        "job_id": job_id,
        "executions": executions,
        "total_iterations": len(executions)
    }


@router.get("/jobs/{job_id}/export")
async def export_job(
    job_id: str,
    format: str = Query("pdf", description="Export format: pdf, markdown, latex, jupyter"),
    db: Session = Depends(get_db_session)
):
    """
    Export job results in various formats.
    
    Args:
        job_id: Job identifier
        format: Export format (pdf, markdown, latex, jupyter)
        db: Database session
        
    Returns:
        Exported file as response
    """
    from fastapi.responses import Response
    from shared.export import export_job_report
    
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job must be completed to export, current status: {job.status.value}"
        )
    
    # Map format to mime types
    mime_types = {
        "pdf": "application/pdf",
        "markdown": "text/markdown",
        "latex": "text/x-latex",
        "jupyter": "application/json"
    }
    
    file_extensions = {
        "pdf": "pdf",
        "markdown": "md",
        "latex": "tex",
        "jupyter": "ipynb"
    }
    
    if format not in mime_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {format}. Supported: {list(mime_types.keys())}"
        )
    
    try:
        # Build job data for export
        job_data = {
            "id": job.id,
            "topic": job.topic,
            "domain": job.domain,
            "status": job.status.value,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "result": job.result or {},
            "config": job.config or {}
        }
        
        # Generate report
        content = export_job_report(job_data, format)
        
        filename = f"research_report_{job_id}.{file_extensions[format]}"
        
        return Response(
            content=content,
            media_type=mime_types[format],
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        logger.error("export_failed", job_id=job_id, format=format, error=str(e))
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
