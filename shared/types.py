from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime

# Re-export WorkflowState from models to ensure single source of truth
# This prevents enum type mismatches when interacting with the database
from shared.models import WorkflowState


class MessageType(Enum):
    """Types of messages agents can send"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    FEEDBACK = "feedback"
    ERROR = "error"
    STATUS_UPDATE = "status_update"


class FeedbackType(Enum):
    """Types of feedback between agents"""
    REWORK = "rework"
    APPROVAL = "approval"
    ESCALATION = "escalation"
    CLARIFICATION = "clarification"


@dataclass
class Message:
    """Inter-agent communication message"""
    sender: str
    receiver: str
    message_type: MessageType
    payload: Dict[str, Any]
    timestamp: datetime
    correlation_id: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TaskResult:
    """Result from an agent task"""
    agent_name: str
    task_id: str
    status: str  # "success", "failure", "partial"
    data: Any
    metrics: Dict[str, float]
    errors: Optional[List[str]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class Feedback:
    """Feedback from one agent to another"""
    source_agent: str
    target_agent: str
    feedback_type: FeedbackType
    message: str
    data: Optional[Dict[str, Any]] = None
    suggested_action: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
