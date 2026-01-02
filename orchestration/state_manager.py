from shared.models import WorkflowState
from shared.logger import get_logger
from typing import Dict, Any, List
from datetime import datetime


class StateManager:
    """Manages workflow state and transitions"""
    
    def __init__(self):
        self.logger = get_logger("StateManager")
        self.current_state = WorkflowState.INITIALIZED
        self.state_history: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        
        # Define valid state transitions
        self.valid_transitions = {
            WorkflowState.INITIALIZED: [WorkflowState.RESEARCHING],
            WorkflowState.RESEARCHING: [WorkflowState.COLLECTING_DATA, WorkflowState.FAILED],
            WorkflowState.COLLECTING_DATA: [WorkflowState.TRAINING, WorkflowState.RESEARCHING, WorkflowState.FAILED],
            WorkflowState.TRAINING: [WorkflowState.EVALUATING, WorkflowState.COLLECTING_DATA, WorkflowState.FAILED],
            WorkflowState.EVALUATING: [WorkflowState.COMPLETED, WorkflowState.TRAINING, WorkflowState.FAILED],
            WorkflowState.COMPLETED: [],
            WorkflowState.FAILED: []
        }
    
    def transition(self, new_state: WorkflowState, reason: str = "") -> bool:
        """Transition to new state with validation"""
        if new_state not in self.valid_transitions[self.current_state]:
            self.logger.error("invalid_state_transition",
                            from_state=self.current_state.value,
                            to_state=new_state.value)
            return False
        
        old_state = self.current_state
        self.current_state = new_state
        
        self.state_history.append({
            "from": old_state.value,
            "to": new_state.value,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        
        self.logger.info("state_transition",
                        from_state=old_state.value,
                        to_state=new_state.value,
                        reason=reason)
        
        return True
    
    def get_current_state(self) -> WorkflowState:
        """Get current workflow state"""
        return self.current_state
    
    def get_state_history(self) -> List[Dict[str, Any]]:
        """Get complete state transition history"""
        return self.state_history.copy()
    
    def update_metadata(self, key: str, value: Any) -> None:
        """Update workflow metadata"""
        self.metadata[key] = value
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get workflow metadata"""
        return self.metadata.copy()
    
    def can_transition_to(self, target_state: WorkflowState) -> bool:
        """Check if transition to target state is valid"""
        return target_state in self.valid_transitions[self.current_state]
