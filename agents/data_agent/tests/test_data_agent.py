import pytest
import asyncio
import pandas as pd
from agents.data_agent.agent import DataAgent
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_process_task_success():
    config = {}
    agent = DataAgent("data", config)
    
    task = {
        "id": "test1",
        "data_requirements": {"min_samples": 100, "features": ["f1"]}
    }
    
    with patch.object(agent, "collect_data", new_callable=AsyncMock) as mock_collect:
        mock_collect.return_value = pd.DataFrame({"f1": [1, 2, 3, 4, 5]})
        result = await agent.process_task(task)
    
    assert result.status == "success"
    assert "quality_score" in result.metrics


@pytest.mark.asyncio
async def test_validate_input_valid():
    config = {}
    agent = DataAgent("data", config)
    task = {"id": "test1", "data_requirements": {"min_samples": 100}}
    
    assert await agent.validate_input(task) is True


@pytest.mark.asyncio
async def test_validate_input_invalid():
    config = {}
    agent = DataAgent("data", config)
    task = {"id": "test1"}  # Missing data_requirements
    
    assert await agent.validate_input(task) is False


@pytest.mark.asyncio
async def test_collect_data():
    config = {}
    agent = DataAgent("data", config)
    
    requirements = {"min_samples": 100, "features": ["f1", "f2"]}
    data = await agent.collect_data(requirements)
    
    assert len(data) >= 100
    assert len(data.columns) == 2


@pytest.mark.asyncio
async def test_clean_data():
    config = {}
    agent = DataAgent("data", config)
    
    data = pd.DataFrame({"f1": [1, 2, 2, 3, None], "f2": [4, 5, 5, 6, 7]})
    cleaned = await agent.clean_data(data)
    
    # Should have removed duplicates and filled NA
    assert cleaned.isnull().sum().sum() == 0


@pytest.mark.asyncio
async def test_validate_quality():
    config = {}
    agent = DataAgent("data", config)
    
    data = pd.DataFrame({"f1": [1, 2, 3], "f2": [4, 5, 6]})
    quality = await agent.validate_quality(data)
    
    assert "quality_score" in quality
    assert "n_samples" in quality
    assert quality["n_samples"] == 3
