import pytest
import asyncio
from agents.training_agent.agent import TrainingAgent
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_process_task_success():
    config = {}
    agent = TrainingAgent("training", config)
    
    task = {
        "id": "test1",
        "features": "mock_features",
        "strategy": {"model_types": ["RandomForest"]}
    }
    
    with patch.object(agent, "train_models", new_callable=AsyncMock) as mock_train:
        mock_train.return_value = [{"type": "RandomForest", "score": 0.9}]
        result = await agent.process_task(task)
    
    assert result.status == "success"
    assert "best_score" in result.metrics


@pytest.mark.asyncio
async def test_validate_input_valid():
    config = {}
    agent = TrainingAgent("training", config)
    task = {"id": "test1", "features": "test_features"}
    
    assert await agent.validate_input(task) is True


@pytest.mark.asyncio
async def test_validate_input_invalid():
    config = {}
    agent = TrainingAgent("training", config)
    task = {"id": "test1"}  # Missing features
    
    assert await agent.validate_input(task) is False


@pytest.mark.asyncio
async def test_setup_experiment():
    config = {}
    agent = TrainingAgent("training", config)
    
    experiment = await agent.setup_experiment("task123", {"approach": "Supervised"})
    
    assert "id" in experiment
    assert "name" in experiment


@pytest.mark.asyncio
async def test_train_models():
    config = {}
    agent = TrainingAgent("training", config)
    
    strategy = {"model_types": ["RandomForest", "XGBoost"]}
    models = await agent.train_models("features", strategy)
    
    assert len(models) == 2
    assert all("score" in m for m in models)


@pytest.mark.asyncio
async def test_optimize_hyperparameters():
    config = {}
    agent = TrainingAgent("training", config)
    
    models = [{"type": "RF", "score": 0.8}]
    optimized = await agent.optimize_hyperparameters(models, None)
    
    assert len(optimized) == 1
    assert optimized[0]["score"] >= 0.8
