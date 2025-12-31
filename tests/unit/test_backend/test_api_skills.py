"""Tests for skills API endpoints."""

import sys
from pathlib import Path
from unittest.mock import patch, mock_open
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_skills_data():
    """Sample skills data."""
    return {
        "skills": [
            {
                "name": "Python",
                "category": "Languages",
                "projects": ["Project1"],
                "evidence_sources": [
                    {
                        "source_type": "project",
                        "source_name": "Project1",
                        "evidence_text": "Used Python for backend",
                    }
                ],
            }
        ]
    }


def test_get_skills_empty(client):
    """Test getting skills when file doesn't exist."""
    with patch('pathlib.Path.exists', return_value=False):
        response = client.get("/api/v1/skills")
        assert response.status_code == 200
        assert response.json() == {"skills": []}


def test_get_skills_with_data(client, sample_skills_data):
    """Test getting skills with data."""
    with patch('pathlib.Path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=json.dumps(sample_skills_data))):
            response = client.get("/api/v1/skills")
            assert response.status_code == 200
            data = response.json()
            assert len(data["skills"]) == 1
            assert data["skills"][0]["name"] == "Python"


def test_update_skills(client, sample_skills_data):
    """Test updating skills."""
    with patch('pathlib.Path.exists', return_value=True):
        with patch('pathlib.Path.mkdir'):
            with patch('builtins.open', mock_open()) as mock_file:
                response = client.put(
                    "/api/v1/skills",
                    json=sample_skills_data
                )
                assert response.status_code == 200
                data = response.json()
                assert len(data["skills"]) == 1
                mock_file.assert_called()
