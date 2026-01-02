"""
Shared module for Multi-Agent AI Research Assistant
"""
from .config import AgentConfig, SystemConfig
from .logger import setup_logging, get_logger
from .types import (
    MessageType,
    WorkflowState,
    FeedbackType,
    Message,
    TaskResult,
    Feedback
)
from .utils import to_json, from_json, flatten_dict, chunk_list, safe_get

__all__ = [
    'AgentConfig',
    'SystemConfig',
    'setup_logging',
    'get_logger',
    'MessageType',
    'WorkflowState',
    'FeedbackType',
    'Message',
    'TaskResult',
    'Feedback',
    'to_json',
    'from_json',
    'flatten_dict',
    'chunk_list',
    'safe_get',
]
