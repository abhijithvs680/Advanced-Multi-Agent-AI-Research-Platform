import pytest
import asyncio
from orchestration.decision_engine import DecisionEngine
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def mock_config():
    return {"agents": {"research": {}, "data": {}, "training": {}, "evaluation": {}}}


@pytest.mark.asyncio
async def test_execute_workflow_success(mock_config):
    with patch("orchestration.decision_engine.ResearchAgent") as mock_research, \
         patch("orchestration.decision_engine.DataAgent") as mock_data, \
         patch("orchestration.decision_engine.TrainingAgent") as mock_training, \
         patch("orchestration.decision_engine.EvaluationAgent") as mock_eval:
        
        # Setup mock instances
        mock_research_instance = MagicMock()
        mock_research_instance.process_task = AsyncMock(return_value=MagicMock(
            status="success",
            data={"data_requirements": {}}
        ))
        mock_research.return_value = mock_research_instance
        
        mock_data_instance = MagicMock()
        mock_data_instance.process_task = AsyncMock(return_value=MagicMock(
            status="success",
            data={"features": [], "strategy": {}},
            metrics={"quality_score": 0.9}
        ))
        mock_data.return_value = mock_data_instance
        
        mock_training_instance = MagicMock()
        mock_training_instance.process_task = AsyncMock(return_value=MagicMock(
            status="success",
            data={"all_models": [{"type": "RF", "score": 0.9}]},
            metrics={"best_score": 0.9}
        ))
        mock_training.return_value = mock_training_instance
        
        mock_eval_instance = MagicMock()
        mock_eval_instance.process_task = AsyncMock(return_value=MagicMock(
            status="success",
            data={"recommendation": {"model_type": "RF", "score": 0.9}, "acceptable": True},
            metrics={"best_score": 0.9}
        ))
        mock_eval.return_value = mock_eval_instance
        
        engine = DecisionEngine(mock_config)
        result = await engine.execute_workflow("test topic")
        
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_workflow_failure_research(mock_config):
    with patch("orchestration.decision_engine.ResearchAgent") as mock_research, \
         patch("orchestration.decision_engine.DataAgent") as mock_data, \
         patch("orchestration.decision_engine.TrainingAgent") as mock_training, \
         patch("orchestration.decision_engine.EvaluationAgent") as mock_eval:
        
        mock_research_instance = MagicMock()
        mock_research_instance.process_task = AsyncMock(return_value=MagicMock(status="failure"))
        mock_research.return_value = mock_research_instance
        
        # Provide minimal mocks for other agents
        mock_data.return_value = MagicMock()
        mock_training.return_value = MagicMock()
        mock_eval.return_value = MagicMock()
        
        engine = DecisionEngine(mock_config)
        result = await engine.execute_workflow("test topic")
        
    assert result["status"] == "failed"


@pytest.mark.asyncio
async def test_create_failure_result(mock_config):
    with patch("orchestration.decision_engine.ResearchAgent"), \
         patch("orchestration.decision_engine.DataAgent"), \
         patch("orchestration.decision_engine.TrainingAgent"), \
         patch("orchestration.decision_engine.EvaluationAgent"):
        
        engine = DecisionEngine(mock_config)
        result = engine._create_failure_result("workflow123", "Test failure")
        
    assert result["status"] == "failed"
    assert result["workflow_id"] == "workflow123"
    assert result["reason"] == "Test failure"


@pytest.mark.asyncio
async def test_create_escalation_result(mock_config):
    with patch("orchestration.decision_engine.ResearchAgent"), \
         patch("orchestration.decision_engine.DataAgent"), \
         patch("orchestration.decision_engine.TrainingAgent"), \
         patch("orchestration.decision_engine.EvaluationAgent"):
        
        engine = DecisionEngine(mock_config)
        result = engine._create_escalation_result("workflow123", {"reason": "Max iterations"})
        
    assert result["status"] == "escalated"
    assert result["requires_human_review"] is True
