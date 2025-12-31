"""Tests for job API resume-related fields (has_resume, latest_resume_id)."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.dependencies import get_db
from src.db.database import Database


@pytest.fixture
def mock_db():
    """Create mock database."""
    db = Mock(spec=Database)
    db.conn = Mock()
    cursor_mock = Mock()
    cursor_mock.execute.return_value = None
    cursor_mock.fetchall.return_value = []
    cursor_mock.fetchone.return_value = None
    db.conn.cursor.return_value = cursor_mock
    return db


@pytest.fixture
def client(mock_db):
    """Create test client with mocked database."""
    app.dependency_overrides[get_db] = lambda: mock_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_jobs_includes_resume_fields(client, mock_db):
    """Test that job list includes has_resume and latest_resume_id fields."""
    from datetime import datetime
    
    sample_job_dict = {
        "id": 1,
        "company": "Test Company",
        "title": "Software Engineer",
        "description": "Test description",
        "status": "New",
        "created_at": datetime.now(),
    }
    
    mock_db.list_jobs.return_value = [sample_job_dict]
    mock_db.get_job_skills.return_value = None
    
    # Mock get_resumes_by_job_id to return empty list (no resumes)
    mock_db.get_resumes_by_job_id = Mock(return_value=[])
    
    response = client.get("/api/v1/jobs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "has_resume" in data[0]
    assert "latest_resume_id" in data[0]
    assert data[0]["has_resume"] is False
    assert data[0]["latest_resume_id"] is None


def test_list_jobs_with_resume(client, mock_db):
    """Test that job list includes resume info when resumes exist."""
    from datetime import datetime
    
    sample_job_dict = {
        "id": 1,
        "company": "Test Company",
        "title": "Software Engineer",
        "description": "Test description",
        "status": "New",
        "created_at": datetime.now(),
    }
    
    mock_db.list_jobs.return_value = [sample_job_dict]
    mock_db.get_job_skills.return_value = None
    
    # Mock get_resumes_by_job_id to return a resume
    mock_db.get_resumes_by_job_id = Mock(return_value=[{"id": 5}])
    
    response = client.get("/api/v1/jobs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["has_resume"] is True
    assert data[0]["latest_resume_id"] == 5
