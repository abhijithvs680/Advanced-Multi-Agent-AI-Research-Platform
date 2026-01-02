"""
Unit tests for Research Agent
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from agents.research_agent.agent import EnhancedResearchAgent
from shared.types import TaskResult


@pytest.fixture
def research_agent():
    """Create research agent instance"""
    config = {
        "max_papers": 10,
        "llm_provider": "openai"
    }
    return EnhancedResearchAgent("test_research", config)


@pytest.fixture
def sample_task():
    """Sample research task"""
    return {
        "id": "test_task_1",
        "query": "machine learning for healthcare",
        "domain": "AI",
        "job_id": "job_123"
    }


class TestResearchAgentValidation:
    """Tests for input validation"""
    
    @pytest.mark.asyncio
    async def test_validate_valid_input(self, research_agent, sample_task):
        """Test validation passes for valid input"""
        result = await research_agent.validate_input(sample_task)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_missing_query(self, research_agent):
        """Test validation fails without query"""
        task = {"id": "test"}
        result = await research_agent.validate_input(task)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_missing_id(self, research_agent):
        """Test validation fails without id"""
        task = {"query": "test query"}
        result = await research_agent.validate_input(task)
        assert result is False


class TestResearchAgentProcessing:
    """Tests for task processing"""
    
    @pytest.mark.asyncio
    async def test_process_task_success(self, research_agent, sample_task):
        """Test successful task processing"""
        # Mock paper search
        with patch.object(research_agent.paper_client, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            
            result = await research_agent.process_task(sample_task)
            
            assert isinstance(result, TaskResult)
            assert result.agent_name == "test_research"
            assert result.task_id == "test_task_1"
            assert result.status == "success"
    
    @pytest.mark.asyncio
    async def test_process_task_invalid_input(self, research_agent):
        """Test task processing with invalid input"""
        task = {"invalid": "data"}
        result = await research_agent.process_task(task)
        
        assert result.status == "failure"
        assert len(result.errors) > 0
    
    @pytest.mark.asyncio
    async def test_search_literature(self, research_agent):
        """Test literature search"""
        with patch.object(research_agent.paper_client, 'search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                MagicMock(title="Test Paper", authors=["Author"], year=2024)
            ]
            
            papers = await research_agent.search_literature("test query", "AI")
            
            assert len(papers) == 1
            mock_search.assert_called_once()


class TestResearchAgentHypotheses:
    """Tests for hypothesis generation"""
    
    @pytest.mark.asyncio
    async def test_generate_hypotheses_fallback(self, research_agent):
        """Test fallback hypothesis generation without LLM"""
        analysis = {
            "summary": "Test summary",
            "key_findings": ["Finding 1"]
        }
        
        result = await research_agent.generate_hypotheses(analysis, "test", "AI")
        
        assert "hypotheses" in result
        assert len(result["hypotheses"]) > 0
    
    @pytest.mark.asyncio
    async def test_design_methodology_fallback(self, research_agent):
        """Test fallback methodology design without LLM"""
        hypotheses = {
            "hypotheses": [
                {"id": "H1", "statement": "Test hypothesis"}
            ]
        }
        
        result = await research_agent.design_methodology(hypotheses, "AI")
        
        assert "experimental_design" in result
        assert "data_requirements" in result["experimental_design"]
