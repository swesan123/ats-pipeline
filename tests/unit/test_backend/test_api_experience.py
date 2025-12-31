"""Tests for experience API endpoints."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from src.models.resume import ExperienceItem, Bullet


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_experience():
    """Sample experience item."""
    return ExperienceItem(
        organization="Test Company",
        role="Software Engineer",
        location="Remote",
        start_date="Jan 2024",
        end_date="Present",
        bullets=[
            Bullet(text="Developed features", skills=[], evidence=None)
        ],
    )


def test_list_experience_empty(client):
    """Test listing experience when library is empty."""
    with patch('backend.app.api.v1.experience.ExperienceLibrary') as mock_library_class:
        mock_library = Mock()
        mock_library.get_all_experience.return_value = []
        mock_library_class.return_value = mock_library
        
        response = client.get("/api/v1/experience")
        assert response.status_code == 200
        assert response.json() == []


def test_list_experience_with_data(client, sample_experience):
    """Test listing experience with data."""
    with patch('backend.app.api.v1.experience.ExperienceLibrary') as mock_library_class:
        mock_library = Mock()
        mock_library.get_all_experience.return_value = [sample_experience]
        mock_library_class.return_value = mock_library
        
        response = client.get("/api/v1/experience")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["organization"] == "Test Company"
        assert data[0]["role"] == "Software Engineer"


def test_create_experience(client):
    """Test creating experience."""
    with patch('backend.app.api.v1.experience.ExperienceLibrary') as mock_library_class:
        mock_library = Mock()
        mock_library_class.return_value = mock_library
        
        request_data = {
            "organization": "New Company",
            "role": "Developer",
            "location": "Remote",
            "start_date": "Jan 2024",
            "end_date": "Present",
            "bullets": [{"text": "Built features", "skills": [], "evidence": None}],
        }
        
        response = client.post("/api/v1/experience", json=request_data)
        assert response.status_code == 201
        assert mock_library.add_experience.called


def test_create_experience_missing_required(client):
    """Test creating experience without required fields."""
    request_data = {
        "role": "Developer",
    }
    
    response = client.post("/api/v1/experience", json=request_data)
    assert response.status_code == 422


def test_update_experience(client, sample_experience):
    """Test updating experience."""
    with patch('backend.app.api.v1.experience.ExperienceLibrary') as mock_library_class:
        mock_library = Mock()
        mock_library.get_experience.return_value = sample_experience
        mock_library_class.return_value = mock_library
        
        request_data = {
            "organization": "Updated Company",
            "role": "Senior Engineer",
            "bullets": [{"text": "Updated bullet", "skills": [], "evidence": None}],
        }
        
        response = client.put(
            "/api/v1/experience/Test Company/Software Engineer",
            json=request_data
        )
        assert response.status_code == 200
        assert mock_library.add_experience.called


def test_update_experience_not_found(client):
    """Test updating non-existent experience."""
    with patch('backend.app.api.v1.experience.ExperienceLibrary') as mock_library_class:
        mock_library = Mock()
        mock_library.get_experience.return_value = None
        mock_library_class.return_value = mock_library
        
        request_data = {
            "organization": "Test",
            "role": "Engineer",
        }
        
        response = client.put(
            "/api/v1/experience/Nonexistent/Engineer",
            json=request_data
        )
        assert response.status_code == 404


def test_delete_experience(client):
    """Test deleting experience."""
    with patch('backend.app.api.v1.experience.ExperienceLibrary') as mock_library_class:
        mock_library = Mock()
        mock_library.remove_experience.return_value = True
        mock_library_class.return_value = mock_library
        
        response = client.delete("/api/v1/experience/Test Company/Engineer")
        assert response.status_code == 204
        mock_library.remove_experience.assert_called_once_with("Test Company", "Engineer")


def test_delete_experience_not_found(client):
    """Test deleting non-existent experience."""
    with patch('backend.app.api.v1.experience.ExperienceLibrary') as mock_library_class:
        mock_library = Mock()
        mock_library.remove_experience.return_value = False
        mock_library_class.return_value = mock_library
        
        response = client.delete("/api/v1/experience/Nonexistent/Engineer")
        assert response.status_code == 404
