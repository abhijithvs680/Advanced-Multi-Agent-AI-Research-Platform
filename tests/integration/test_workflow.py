import pytest
import asyncio
from orchestration.decision_engine import DecisionEngine
from shared.config import SystemConfig


@pytest.fixture
def engine():
    config = {
        'agents': {
            'research': {},
            'data': {},
            'training': {},
            'evaluation': {}
        }
    }
    return DecisionEngine(config)


@pytest.mark.asyncio
async def test_complete_workflow(engine):
    """Test complete research workflow"""
    result = await engine.execute_workflow(
        topic="test research topic",
        domain="test",
        max_iterations=2
    )
    
    assert result['status'] in ['COMPLETED', 'ESCALATED']
    assert 'workflow_id' in result
    assert 'state_history' in result


@pytest.mark.asyncio
async def test_workflow_state_transitions(engine):
    """Test that workflow progresses through expected states"""
    result = await engine.execute_workflow(
        topic="machine learning",
        domain="AI",
        max_iterations=3
    )
    
    state_history = result.get('state_history', [])
    
    # Should have transitioned through states
    assert len(state_history) >= 1
    
    # Check first transition is to RESEARCHING
    if state_history:
        assert state_history[0]['to'] == 'RESEARCHING'


@pytest.mark.asyncio
async def test_workflow_with_different_domains(engine):
    """Test workflow with different research domains"""
    domains = ["biotech", "finance", "healthcare"]
    
    for domain in domains:
        result = await engine.execute_workflow(
            topic=f"test topic for {domain}",
            domain=domain,
            max_iterations=2
        )
        
        assert result['status'] in ['COMPLETED', 'ESCALATED', 'FAILED']
        assert 'workflow_id' in result


@pytest.mark.asyncio
async def test_workflow_failure_recovery(engine):
    """Test workflow handles failures gracefully"""
    # This tests the basic failure recovery mechanism
    result = await engine.execute_workflow(
        topic="",  # Empty topic might cause issues
        domain="test"
    )
    
    # Should not crash, should return some result
    assert 'status' in result
    assert 'workflow_id' in result
