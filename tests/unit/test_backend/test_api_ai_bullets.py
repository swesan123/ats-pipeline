"""Tests for AI bullets API endpoints."""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    """Create test client."""
    yield TestClient(app)


@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
def test_generate_bullets_success(client):
    """Test successful AI bullet generation."""
    import json
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "bullets": [
            "Built a web application using **Python** and **React**.",
            "Implemented REST APIs with **Flask**.",
            "Deployed using **Docker**.",
        ],
        "reasoning": "Generated professional resume bullets."
    })
    
    with patch("backend.app.api.v1.ai_bullets.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        response = client.post(
            "/api/v1/bullets/generate",
            json={
                "project_name": "Test Project",
                "description": "A web application",
                "tech_stack": ["Python", "React", "Flask"],
            }
        )
        
        assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
        data = response.json()
        assert "bullets" in data
        assert len(data["bullets"]) >= 1
        assert isinstance(data["bullets"], list)


@patch.dict(os.environ, {}, clear=True)
def test_generate_bullets_no_api_key(client):
    """Test bullet generation without API key."""
    response = client.post(
        "/api/v1/bullets/generate",
        json={
            "project_name": "Test Project",
            "description": "A web application",
            "tech_stack": [],
        }
    )
    
    assert response.status_code == 500
    assert "api key" in response.json()["detail"].lower()


@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
def test_format_bullets_success(client):
    """Test successful bullet formatting."""
    import json
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "bullets": [
            "Built a web application using **Python** and **React**.",
            "Implemented REST APIs with **Flask**.",
        ],
        "reasoning": "Formatted bullets to match professional standards."
    })
    
    with patch("backend.app.api.v1.ai_bullets.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        response = client.post(
            "/api/v1/bullets/format",
            json={
                "bullets": [
                    "Built a web app using Python and React.",
                    "Made REST APIs with Flask.",
                ],
                "project_name": "Test Project",
                "tech_stack": ["Python", "React", "Flask"],
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "bullets" in data
        assert len(data["bullets"]) > 0
        assert isinstance(data["bullets"], list)


@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
def test_format_bullets_invalid_input(client):
    """Test bullet formatting with invalid input."""
    import json
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "bullets": ["Formatted bullet."],
        "reasoning": "Formatted bullet."
    })
    
    with patch("backend.app.api.v1.ai_bullets.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        response = client.post(
            "/api/v1/bullets/format",
            json={
                "bullets": ["not a sentence."],
                "project_name": "Test Project",
                "tech_stack": [],
            }
        )
        
        # Should return 200
        assert response.status_code == 200
        data = response.json()
        assert "bullets" in data
