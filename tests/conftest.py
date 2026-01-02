"""
Test configuration and fixtures
"""
import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing"""
    return {
        "content": '{"hypotheses": [{"id": "H1", "statement": "Test hypothesis"}]}',
        "usage": {"prompt_tokens": 100, "completion_tokens": 50}
    }


@pytest.fixture
def mock_papers():
    """Mock paper search results"""
    return [
        {
            "paper_id": "123",
            "title": "Test Paper 1",
            "abstract": "Abstract 1",
            "authors": ["Author A", "Author B"],
            "year": 2024,
            "citation_count": 10
        },
        {
            "paper_id": "456",
            "title": "Test Paper 2",
            "abstract": "Abstract 2",
            "authors": ["Author C"],
            "year": 2023,
            "citation_count": 25
        }
    ]


@pytest.fixture
def sample_features():
    """Sample features for training tests"""
    import pandas as pd
    import numpy as np
    
    np.random.seed(42)
    n_samples = 100
    
    data = {
        "feature_1": np.random.randn(n_samples),
        "feature_2": np.random.randn(n_samples),
        "feature_3": np.random.randn(n_samples),
        "target": np.random.randint(0, 2, n_samples)
    }
    
    return pd.DataFrame(data)
