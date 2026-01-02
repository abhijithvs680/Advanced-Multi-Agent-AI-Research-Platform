from shared.types import Feedback, FeedbackType
from shared.logger import get_logger
from typing import Dict, Any, Optional


class FeedbackHandler:
    """Handles feedback between agents and iteration logic"""
    
    def __init__(self):
        self.logger = get_logger("FeedbackHandler")
        self.feedback_history = []
        self.iteration_count = 0
        self.max_iterations = 5
    
    async def process_feedback(self, feedback: Feedback) -> Dict[str, Any]:
        """Process feedback and determine action"""
        self.logger.info("processing_feedback",
                        source=feedback.source_agent,
                        target=feedback.target_agent,
                        type=feedback.feedback_type.value)
        
        self.feedback_history.append(feedback)
        
        if feedback.feedback_type == FeedbackType.REWORK:
            return await self._handle_rework(feedback)
        elif feedback.feedback_type == FeedbackType.APPROVAL:
            return await self._handle_approval(feedback)
        elif feedback.feedback_type == FeedbackType.ESCALATION:
            return await self._handle_escalation(feedback)
        elif feedback.feedback_type == FeedbackType.CLARIFICATION:
            return await self._handle_clarification(feedback)
        
        return {"action": "unknown", "feedback": feedback}
    
    async def _handle_rework(self, feedback: Feedback) -> Dict[str, Any]:
        """Handle rework request"""
        self.iteration_count += 1
        
        if self.iteration_count >= self.max_iterations:
            self.logger.warning("max_iterations_reached",
                              count=self.iteration_count)
            return {
                "action": "escalate",
                "reason": "Max iterations reached",
                "target": "human_review"
            }
        
        return {
            "action": "retry",
            "target_agent": feedback.target_agent,
            "instructions": feedback.message,
            "data": feedback.data
        }
    
    async def _handle_approval(self, feedback: Feedback) -> Dict[str, Any]:
        """Handle approval feedback"""
        return {
            "action": "proceed",
            "next_agent": self._get_next_agent(feedback.source_agent)
        }
    
    async def _handle_escalation(self, feedback: Feedback) -> Dict[str, Any]:
        """Handle escalation request"""
        self.logger.warning("feedback_escalated",
                          source=feedback.source_agent,
                          reason=feedback.message)
        
        return {
            "action": "escalate",
            "reason": feedback.message,
            "requires_human": True
        }
    
    async def _handle_clarification(self, feedback: Feedback) -> Dict[str, Any]:
        """Handle clarification request"""
        return {
            "action": "clarify",
            "target_agent": feedback.target_agent,
            "question": feedback.message
        }
    
    def _get_next_agent(self, current_agent: str) -> Optional[str]:
        """Get next agent in workflow"""
        agent_flow = {
            "research": "data",
            "data": "training",
            "training": "evaluation",
            "evaluation": None
        }
        return agent_flow.get(current_agent)
    
    def should_iterate(self, metrics: Dict[str, Any]) -> bool:
        """Determine if iteration is needed based on metrics"""
        if self.iteration_count >= self.max_iterations:
            return False
        
        # Check if metrics meet thresholds
        quality_threshold = 0.8
        current_quality = metrics.get('quality_score', 0.0)
        
        return current_quality < quality_threshold
    
    def get_iteration_count(self) -> int:
        """Get current iteration count"""
        return self.iteration_count
    
    def reset_iterations(self) -> None:
        """Reset iteration counter"""
        self.iteration_count = 0
