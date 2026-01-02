from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import uuid
from datetime import datetime
from shared.types import Message, TaskResult, MessageType
from shared.logger import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential


class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.logger = get_logger(self.name)
        self.state = {}
        self.message_queue = []
        
    @abstractmethod
    async def process_task(self, task: Dict[str, Any]) -> TaskResult:
        """Process a task and return result"""
        pass
    
    @abstractmethod
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data before processing"""
        pass
    
    async def send_message(self, receiver: str, message_type: MessageType, 
                          payload: Dict[str, Any]) -> None:
        """Send message to another agent"""
        message = Message(
            sender=self.name,
            receiver=receiver,
            message_type=message_type,
            payload=payload,
            timestamp=datetime.now(),
            correlation_id=str(uuid.uuid4())
        )
        self.logger.info("message_sent", receiver=receiver, type=message_type.value)
        # Communication bus will handle delivery
        await self._deliver_message(message)
    
    async def receive_message(self) -> Optional[Message]:
        """Receive message from queue"""
        if self.message_queue:
            return self.message_queue.pop(0)
        return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def execute_with_retry(self, func, *args, **kwargs):
        """Execute function with retry logic"""
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            self.logger.error("execution_failed", error=str(e), func=func.__name__)
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "name": self.name,
            "state": self.state,
            "queue_size": len(self.message_queue),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _deliver_message(self, message: Message) -> None:
        """Internal method to deliver message via communication bus"""
        # This will be implemented by the communication system
        pass
