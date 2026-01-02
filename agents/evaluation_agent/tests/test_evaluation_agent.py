import pytest
import asyncio
from agents.evaluation_agent.agent import EvaluationAgent
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_process_task_success():
    config = {}
    agent = EvaluationAgent("evaluation", config)
    
    task = {
        "id": "test1",
        "models": [{"type": "RF", "score": 0.9}],
        "evaluation_criteria": {"acceptance_threshold": 0.8}
    }
    
    with patch.object(agent, "evaluate_models", new_callable=AsyncMock) as mock_eval:
        mock_eval.return_value = [{"model": {"type": "RF"}, "accuracy": 0.9, "precision": 0.9, "recall": 0.9, "f1_score": 0.9}]
        result = await agent.process_task(task)
    
    assert result.status == "success"
    assert result.data["acceptable"] is True


@pytest.mark.asyncio
async def test_validate_input_valid():
    config = {}
    agent = EvaluationAgent("evaluation", config)
    task = {"id": "test1", "models": [{"type": "RF"}]}
    
    assert await agent.validate_input(task) is True


@pytest.mark.asyncio
async def test_validate_input_invalid():
    config = {}
    agent = EvaluationAgent("evaluation", config)
    task = {"id": "test1"}  # Missing models
    
    assert await agent.validate_input(task) is False


@pytest.mark.asyncio
async def test_evaluate_models():
    config = {}
    agent = EvaluationAgent("evaluation", config)
    
    models = [{"type": "RF", "score": 0.9}]
    evaluations = await agent.evaluate_models(models, {})
    
    assert len(evaluations) == 1
    assert "accuracy" in evaluations[0]
    assert "f1_score" in evaluations[0]


@pytest.mark.asyncio
async def test_run_simulations():
    config = {}
    agent = EvaluationAgent("evaluation", config)
    
    simulations = await agent.run_simulations([])
    
    assert "simulation_runs" in simulations
    assert "success_rate" in simulations


@pytest.mark.asyncio
async def test_rank_candidates():
    config = {}
    agent = EvaluationAgent("evaluation", config)
    
    evaluations = [
        {"model": {"type": "RF"}, "accuracy": 0.9, "f1_score": 0.85, "precision": 0.88, "recall": 0.82},
        {"model": {"type": "XGB"}, "accuracy": 0.85, "f1_score": 0.8, "precision": 0.82, "recall": 0.78}
    ]
    rankings = await agent.rank_candidates(evaluations, {})
    
    assert len(rankings) == 2
    assert rankings[0]["rank"] == 1
    assert rankings[1]["rank"] == 2


@pytest.mark.asyncio
async def test_generate_report():
    config = {}
    agent = EvaluationAgent("evaluation", config)
    
    rankings = [{"model_type": "RF", "score": 0.9, "rank": 1}]
    report = await agent.generate_report(rankings, [])
    
    assert "summary" in report
    assert "best_model" in report
    assert "recommendations" in report
