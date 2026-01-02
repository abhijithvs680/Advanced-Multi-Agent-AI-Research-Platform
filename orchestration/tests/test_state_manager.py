import pytest
from orchestration.state_manager import StateManager
from shared.types import WorkflowState


def test_initial_state():
    manager = StateManager()
    assert manager.get_current_state() == WorkflowState.INITIALIZED


def test_valid_transition():
    manager = StateManager()
    assert manager.transition(WorkflowState.RESEARCHING, "test") is True
    assert manager.get_current_state() == WorkflowState.RESEARCHING


def test_invalid_transition():
    manager = StateManager()
    # From INITIALIZED to TRAINING (invalid)
    assert manager.transition(WorkflowState.TRAINING, "test") is False
    assert manager.get_current_state() == WorkflowState.INITIALIZED


def test_state_history():
    manager = StateManager()
    manager.transition(WorkflowState.RESEARCHING, "start")
    history = manager.get_state_history()
    assert len(history) == 1
    assert history[0]["to"] == "researching"


def test_multiple_transitions():
    manager = StateManager()
    manager.transition(WorkflowState.RESEARCHING, "step1")
    manager.transition(WorkflowState.COLLECTING_DATA, "step2")
    manager.transition(WorkflowState.TRAINING, "step3")
    
    history = manager.get_state_history()
    assert len(history) == 3
    assert manager.get_current_state() == WorkflowState.TRAINING


def test_can_transition_to():
    manager = StateManager()
    assert manager.can_transition_to(WorkflowState.RESEARCHING) is True
    assert manager.can_transition_to(WorkflowState.TRAINING) is False


def test_metadata_operations():
    manager = StateManager()
    manager.update_metadata("key1", "value1")
    manager.update_metadata("key2", {"nested": "value"})
    
    metadata = manager.get_metadata()
    assert metadata["key1"] == "value1"
    assert metadata["key2"]["nested"] == "value"


def test_transition_to_failed():
    manager = StateManager()
    manager.transition(WorkflowState.RESEARCHING, "start")
    assert manager.transition(WorkflowState.FAILED, "error") is True
    assert manager.get_current_state() == WorkflowState.FAILED


def test_transition_to_completed():
    manager = StateManager()
    manager.transition(WorkflowState.RESEARCHING, "step1")
    manager.transition(WorkflowState.COLLECTING_DATA, "step2")
    manager.transition(WorkflowState.TRAINING, "step3")
    manager.transition(WorkflowState.EVALUATING, "step4")
    manager.transition(WorkflowState.COMPLETED, "done")
    
    assert manager.get_current_state() == WorkflowState.COMPLETED
