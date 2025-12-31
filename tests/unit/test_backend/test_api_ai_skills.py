"""Tests for AI skills suggestions API endpoints."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_suggest_skills_success(client):
    """Test successful skill suggestions."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = '{"suggested_skills": ["Python", "Docker"], "reasoning": "Test reasoning"}'
    
    with patch('backend.app.api.v1.ai_skills.OpenAI') as mock_openai_class, \
         patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        response = client.post(
            "/api/v1/skills/ai-suggestions",
            json={
                "job_description": "Looking for a Python developer",
                "current_skills": ["JavaScript"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "suggested_skills" in data
        assert "reasoning" in data
        assert len(data["suggested_skills"]) > 0


def test_suggest_skills_no_api_key(client):
    """Test skill suggestions without API key."""
    with patch.dict('os.environ', {}, clear=True):
        response = client.post(
            "/api/v1/skills/ai-suggestions",
            json={
                "job_description": "Looking for a Python developer",
                "current_skills": []
            }
        )
        
        assert response.status_code == 500
        assert "api key" in response.json()["detail"].lower()


def test_suggest_skills_empty_description(client):
    """Test skill suggestions with empty job description."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = '{"suggested_skills": [], "reasoning": ""}'
    
    with patch('backend.app.api.v1.ai_skills.OpenAI') as mock_openai_class, \
         patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        response = client.post(
            "/api/v1/skills/ai-suggestions",
            json={
                "job_description": "",
                "current_skills": []
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "suggested_skills" in data
