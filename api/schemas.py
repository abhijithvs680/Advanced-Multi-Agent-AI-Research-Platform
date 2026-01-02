"""
Pydantic schemas for API request/response validation.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class JobStatusEnum(str, Enum):
    """Job status enumeration"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WorkflowStateEnum(str, Enum):
    """Workflow state enumeration"""
    INITIALIZED = "INITIALIZED"
    RESEARCHING = "RESEARCHING"
    COLLECTING_DATA = "COLLECTING_DATA"
    TRAINING = "TRAINING"
    EVALUATING = "EVALUATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Request Schemas

class JobCreate(BaseModel):
    """Schema for creating a new job"""
    topic: str = Field(..., min_length=1, max_length=255, description="Research topic")
    domain: str = Field(..., min_length=1, max_length=100, description="Research domain")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Custom configuration")
    priority: int = Field(default=0, description="Job priority (higher = more urgent)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "topic": "machine learning",
                "domain": "AI",
                "priority": 0
            }
        }
    )


class JobUpdate(BaseModel):
    """Schema for updating job status"""
    status: Optional[JobStatusEnum] = None
    current_state: Optional[WorkflowStateEnum] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


# Response Schemas

class JobResponse(BaseModel):
    """Schema for job response"""
    id: str
    topic: str
    domain: str
    status: JobStatusEnum
    current_state: Optional[WorkflowStateEnum]
    
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    config: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    
    mlflow_experiment_id: Optional[str]
    mlflow_run_id: Optional[str]
    
    retry_count: int
    max_retries: int
    
    # Stage results for UI visualization
    state_results: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    """Schema for listing jobs"""
    jobs: List[JobResponse]
    total: int
    page: int
    page_size: int


class WorkflowExecutionResponse(BaseModel):
    """Schema for workflow execution response"""
    id: str
    job_id: str
    iteration: int
    state: WorkflowStateEnum
    status: JobStatusEnum
    
    started_at: datetime
    completed_at: Optional[datetime]
    
    state_results: Optional[Dict[str, Any]]
    metrics: Optional[Dict[str, Any]]
    error_message: Optional[str]
    
    mlflow_run_id: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


# Health Check Schemas

class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str = Field(..., description="Service status")
    version: str = Field(default="1.0.0", description="API version")
    timestamp: datetime


class ReadinessResponse(BaseModel):
    """Schema for readiness check response"""
    ready: bool
    database: bool
    queue: bool
    mlflow: bool
    timestamp: datetime


# Error Schemas

class ErrorResponse(BaseModel):
    """Schema for error responses"""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Metrics Schema

class MetricsResponse(BaseModel):
    """Schema for metrics response"""
    queue_length: int
    running_jobs: int
    completed_jobs_24h: int
    failed_jobs_24h: int
    average_duration_minutes: float
