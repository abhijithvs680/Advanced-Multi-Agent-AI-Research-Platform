"""
Database models for job persistence and workflow tracking.
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import (
    Column, String, DateTime, Enum, Integer, Text, JSON, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


class JobStatus(PyEnum):
    """Job execution status"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WorkflowState(PyEnum):
    """Workflow execution state"""
    INITIALIZED = "INITIALIZED"
    RESEARCHING = "RESEARCHING"
    COLLECTING_DATA = "COLLECTING_DATA"
    TRAINING = "TRAINING"
    EVALUATING = "EVALUATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Job(Base):
    """Research job model"""
    __tablename__ = "jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    topic = Column(String(255), nullable=False)
    domain = Column(String(100), nullable=False)
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.PENDING)
    current_state = Column(Enum(WorkflowState), nullable=True)
    message = Column(Text, nullable=True)
    progress = Column(Integer, nullable=True) # Progress percentage 0-100
    
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Configuration and results
    config = Column(JSON, nullable=True)  # Job-specific configuration
    result = Column(JSON, nullable=True)  # Final workflow result
    state_results = Column(JSON, nullable=True)  # Stage results for UI visualization
    error_message = Column(Text, nullable=True)
    
    # MLflow tracking
    mlflow_experiment_id = Column(String(100), nullable=True)
    mlflow_run_id = Column(String(100), nullable=True)
    
    # Retry tracking
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Relationships
    executions = relationship("WorkflowExecution", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Job(id={self.id}, topic='{self.topic}', status={self.status.value})>"


class WorkflowExecution(Base):
    """Individual workflow execution/iteration within a job"""
    __tablename__ = "workflow_executions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    
    # Execution tracking
    iteration = Column(Integer, nullable=False, default=0)
    state = Column(Enum(WorkflowState), nullable=False)
    status = Column(Enum(JobStatus), nullable=False)
    
    # Timing
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Results
    state_results = Column(JSON, nullable=True)  # Results from each state
    metrics = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # MLflow tracking
    mlflow_run_id = Column(String(100), nullable=True)
    
    # Relationships
    job = relationship("Job", back_populates="executions")
    
    def __repr__(self):
        return f"<WorkflowExecution(id={self.id}, job_id={self.job_id}, iteration={self.iteration})>"
