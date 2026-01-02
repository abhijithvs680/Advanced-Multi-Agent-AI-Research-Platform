import pytest
import asyncio
from agents.research_agent.agent import ResearchAgent
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_process_task_success():
    config = {"llm_model": "gpt-4"}
    agent = ResearchAgent("research", config)
    
    task = {"id": "test1", "query": "test query", "domain": "test"}
    
    with patch.object(agent, "search_literature", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = [{"title": "Test Paper"}]
        result = await agent.process_task(task)
    
    assert result.status == "success"
    assert result.agent_name == "research"


@pytest.mark.asyncio
async def test_validate_input_valid():
    config = {}
    agent = ResearchAgent("research", config)
    task = {"id": "test1", "query": "test query"}
    
    assert await agent.validate_input(task) is True


@pytest.mark.asyncio
async def test_validate_input_invalid():
    config = {}
    agent = ResearchAgent("research", config)
    task = {"id": "test1"}  # Missing query
    
    assert await agent.validate_input(task) is False


@pytest.mark.asyncio
async def test_search_literature():
    config = {}
    agent = ResearchAgent("research", config)
    
    papers = await agent.search_literature("machine learning")
    
    assert len(papers) > 0
    assert "title" in papers[0]


@pytest.mark.asyncio
async def test_analyze_papers():
    config = {}
    agent = ResearchAgent("research", config)
    
    papers = [{"title": "Test Paper", "abstract": "Test abstract"}]
    analysis = await agent.analyze_papers(papers)
    
    assert "summary" in analysis
    assert "confidence" in analysis


@pytest.mark.asyncio
async def test_propose_strategy():
    config = {}
    agent = ResearchAgent("research", config)
    
    analysis = {"summary": "Test", "confidence": 0.8}
    strategy = await agent.propose_strategy(analysis, "test")
    
    assert "approach" in strategy
    assert "model_types" in strategy


@pytest.mark.asyncio
async def test_assess_risks():
    config = {}
    agent = ResearchAgent("research", config)
    
    strategy = {"approach": "Supervised learning"}
    risks = await agent.assess_risks(strategy)
    
    assert len(risks) > 0
    assert "risk" in risks[0]
    assert "severity" in risks[0]
