from typing import Dict, Any, Optional, List
from shared.types import Message
from shared.logger import get_logger
import asyncio
from collections import defaultdict


class CommunicationBus:
    """Central communication system for agent messages"""
    
    def __init__(self):
        self.logger = get_logger("CommunicationBus")
        self.message_queues: Dict[str, List[Message]] = defaultdict(list)
        self.subscribers: Dict[str, List[str]] = defaultdict(list)
        
    async def send_message(self, message: Message) -> None:
        """Send message to receiver's queue"""
        self.logger.info("message_sent", 
                        sender=message.sender,
                        receiver=message.receiver,
                        type=message.message_type.value)
        
        self.message_queues[message.receiver].append(message)
        
        # Notify subscribers
        await self._notify_subscribers(message)
    
    async def receive_message(self, agent_name: str) -> Optional[Message]:
        """Receive next message for agent"""
        if self.message_queues[agent_name]:
            message = self.message_queues[agent_name].pop(0)
            self.logger.info("message_received", 
                           receiver=agent_name,
                           sender=message.sender)
            return message
        return None
    
    def subscribe(self, agent_name: str, event_type: str) -> None:
        """Subscribe to specific event types"""
        self.subscribers[event_type].append(agent_name)
    
    async def _notify_subscribers(self, message: Message) -> None:
        """Notify subscribers of message"""
        event_type = message.message_type.value
        for subscriber in self.subscribers.get(event_type, []):
            if subscriber != message.sender:
                await self.send_message(Message(
                    sender="system",
                    receiver=subscriber,
                    message_type=message.message_type,
                    payload={"notification": True, "original_message": message},
                    timestamp=message.timestamp,
                    correlation_id=message.correlation_id
                ))
    
    def get_queue_status(self) -> Dict[str, int]:
        """Get status of all message queues"""
        return {
            agent: len(messages) 
            for agent, messages in self.message_queues.items()
        }
