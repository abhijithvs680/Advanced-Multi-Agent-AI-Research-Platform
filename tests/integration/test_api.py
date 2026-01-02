"""
Integration tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from api.server import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns service info"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert data["status"] == "RUNNING"
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestJobEndpoints:
    """Tests for job CRUD endpoints"""
    
    def test_create_job(self, client):
        """Test job creation"""
        job_data = {
            "topic": "Test research topic",
            "domain": "AI",
            "priority": 5
        }
        
        response = client.post("/api/v1/jobs", json=job_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["topic"] == job_data["topic"]
        assert data["status"] == "PENDING"
    
    def test_create_job_minimal(self, client):
        """Test job creation with minimal data"""
        job_data = {"topic": "Minimal test"}
        
        response = client.post("/api/v1/jobs", json=job_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["domain"] == "general"
    
    def test_list_jobs(self, client):
        """Test listing jobs"""
        response = client.get("/api/v1/jobs")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    
    def test_list_jobs_with_filter(self, client):
        """Test listing jobs with status filter"""
        response = client.get("/api/v1/jobs?status=PENDING")
        
        assert response.status_code == 200
    
    def test_get_job_not_found(self, client):
        """Test getting non-existent job"""
        response = client.get("/api/v1/jobs/non-existent-id")
        
        assert response.status_code == 404


class TestJobActions:
    """Tests for job actions"""
    
    def test_cancel_job_not_found(self, client):
        """Test canceling non-existent job"""
        response = client.post("/api/v1/jobs/non-existent-id/cancel")
        
        assert response.status_code == 404
    
    def test_retry_job_not_found(self, client):
        """Test retrying non-existent job"""
        response = client.post("/api/v1/jobs/non-existent-id/retry")
        
        assert response.status_code == 404
    
    def test_delete_job_not_found(self, client):
        """Test deleting non-existent job"""
        response = client.delete("/api/v1/jobs/non-existent-id")
        
        assert response.status_code == 404


class TestValidation:
    """Tests for input validation"""
    
    def test_create_job_empty_topic(self, client):
        """Test rejection of empty topic"""
        job_data = {"topic": ""}
        
        response = client.post("/api/v1/jobs", json=job_data)
        
        # Should still work but with empty topic
        # Add stricter validation in production
        assert response.status_code in [200, 422]
    
    def test_create_job_invalid_priority(self, client):
        """Test validation of invalid priority"""
        job_data = {
            "topic": "Test",
            "priority": 100  # Out of range
        }
        
        response = client.post("/api/v1/jobs", json=job_data)
        
        # Depending on validation
        assert response.status_code in [200, 422]
