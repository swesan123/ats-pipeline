"""Tests for jobs API endpoints."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.dependencies import get_db
from src.db.database import Database
from src.models.job import JobPosting, JobSkills


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
    # Override the dependency
    app.dependency_overrides[get_db] = lambda: mock_db
    yield TestClient(app)
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_job_dict():
    """Sample job dictionary."""
    return {
        "id": 1,
        "company": "Test Company",
        "title": "Software Engineer",
        "location": "Remote",
        "description": "Test job description",
        "source_url": "https://example.com/job",
        "status": "New",
        "notes": None,
        "contact_name": None,
        "date_applied": None,
        "created_at": "2024-01-01T00:00:00",
    }


def test_list_jobs_empty(client, mock_db):
    """Test listing jobs when database is empty."""
    mock_db.list_jobs.return_value = []
    response = client.get("/api/v1/jobs")
    assert response.status_code == 200
    assert response.json() == []


def test_list_jobs_with_status_filter(client, mock_db, sample_job_dict):
    """Test listing jobs with status filter."""
    mock_db.list_jobs.return_value = [sample_job_dict]
    mock_db.get_job_skills.return_value = None
    
    response = client.get("/api/v1/jobs?status=New")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["company"] == "Test Company"


def test_get_job_not_found(client, mock_db):
    """Test getting a non-existent job."""
    mock_db.get_job_full.return_value = None
    
    response = client.get("/api/v1/jobs/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_job_success(client, mock_db, sample_job_dict):
    """Test getting an existing job."""
    mock_db.get_job_full.return_value = sample_job_dict
    mock_db.get_job_skills.return_value = None
    
    response = client.get("/api/v1/jobs/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["company"] == "Test Company"


def test_create_job_from_url(client, mock_db, sample_job_dict):
    """Test creating a job from URL."""
    with patch('backend.app.api.v1.jobs.JobURLScraper') as mock_scraper_class:
        with patch('backend.app.api.v1.jobs.JobSkillExtractor') as mock_extractor_class:
            mock_scraper = Mock()
            mock_scraper.extract_job_content.return_value = {
                "company": "Test Company",
                "title": "Software Engineer",
                "description": "Test description",
                "source_url": "https://example.com/job",
            }
            mock_scraper_class.return_value = mock_scraper
            
            mock_extractor = Mock()
            mock_extractor.extract_skills.return_value = JobSkills(
                required_skills=["Python"],
                preferred_skills=[],
                soft_skills=[],
                seniority_indicators=[],
            )
            mock_extractor_class.return_value = mock_extractor
            
            mock_db.save_job.return_value = 1
            mock_db.get_job_full.return_value = sample_job_dict
            mock_db.get_job_skills.return_value = None
            
            response = client.post(
                "/api/v1/jobs",
                json={"url": "https://example.com/job"}
            )
            assert response.status_code == 201
            data = response.json()
            assert data["company"] == "Test Company"


def test_create_job_from_description(client, mock_db, sample_job_dict):
    """Test creating a job from description."""
    with patch('backend.app.api.v1.jobs._save_job_from_text') as mock_save:
        mock_save.return_value = 1
        mock_db.get_job_full.return_value = sample_job_dict
        mock_db.get_job_skills.return_value = None
        
        response = client.post(
            "/api/v1/jobs",
            json={"description": "Test job description"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["company"] == "Test Company"
        mock_save.assert_called_once()


def test_create_job_missing_data(client):
    """Test creating a job without URL or description."""
    response = client.post("/api/v1/jobs", json={})
    assert response.status_code == 400
    assert "either url or description" in response.json()["detail"].lower()


def test_update_job_status(client, mock_db, sample_job_dict):
    """Test updating job status."""
    mock_db.get_job_full.return_value = sample_job_dict
    mock_db.get_job_skills.return_value = None
    
    updated_job = sample_job_dict.copy()
    updated_job["status"] = "Applied"
    mock_db.get_job_full.side_effect = [sample_job_dict, updated_job]
    
    response = client.put(
        "/api/v1/jobs/1",
        json={"status": "Applied"}
    )
    assert response.status_code == 200
    mock_db.update_job_status.assert_called_once_with(1, "Applied")


def test_delete_job(client, mock_db, sample_job_dict):
    """Test deleting a job."""
    mock_db.get_job_full.return_value = sample_job_dict
    
    response = client.delete("/api/v1/jobs/1")
    assert response.status_code == 204
    mock_db.delete_job.assert_called_once_with(1)


def test_delete_job_not_found(client, mock_db):
    """Test deleting a non-existent job."""
    mock_db.get_job_full.return_value = None
    
    response = client.delete("/api/v1/jobs/999")
    assert response.status_code == 404


def test_extract_skills_from_url(client):
    """Test extracting skills from URL."""
    with patch('backend.app.api.v1.jobs.JobURLScraper') as mock_scraper_class:
        with patch('backend.app.api.v1.jobs.JobSkillExtractor') as mock_extractor_class:
            with patch('backend.app.api.v1.jobs._extract_job_info_from_text') as mock_extract_info:
                mock_scraper = Mock()
                mock_scraper.extract_job_content.return_value = {
                    "company": "Test",
                    "title": "Engineer",
                    "description": "Python, React, Docker",
                }
                mock_scraper_class.return_value = mock_scraper
                
                mock_extractor = Mock()
                mock_extractor.extract_skills.return_value = JobSkills(
                    required_skills=["Python", "React"],
                    preferred_skills=["Docker"],
                    soft_skills=[],
                    seniority_indicators=[],
                )
                mock_extractor_class.return_value = mock_extractor
                
                response = client.post(
                    "/api/v1/jobs/extract-skills",
                    json={"url": "https://example.com/job"}
                )
                assert response.status_code == 200
                data = response.json()
                assert "Python" in data["required_skills"]


def test_match_job(client, mock_db):
    """Test matching a job with resume."""
    from src.models.resume import Resume
    from src.models.job import JobSkills, JobMatch
    
    # get_job returns a JobPosting object
    mock_db.get_job.return_value = JobPosting(
        company="Test",
        title="Engineer",
        description="Test",
    )
    mock_db.get_latest_resume.return_value = Resume(
        version=1,
        name="Test User",
        email="test@example.com",
        phone="123-456-7890",
        experience=[],
        projects=[],
        skills={},
    )
    # get_job_skills returns a dict (parsed from JSON)
    mock_db.get_job_skills.return_value = {
        "required_skills": ["Python"],
        "preferred_skills": [],
        "soft_skills": [],
        "seniority_indicators": [],
    }
    
    # Patch SkillMatcher and SkillOntology at the import location inside the function
    with patch('src.matching.skill_matcher.SkillMatcher') as mock_matcher_class:
        with patch('src.models.skills.SkillOntology') as mock_ontology_class:
            mock_matcher = Mock()
            mock_match = JobMatch(
                job_id=1,
                fit_score=0.85,
                matching_skills=["Python"],  # JobMatch uses matching_skills
                missing_skills=[],
            )
            mock_matcher.match_job.return_value = mock_match
            mock_matcher_class.return_value = mock_matcher
            mock_ontology_class.return_value = Mock()
            
            response = client.post("/api/v1/jobs/1/match")
            assert response.status_code == 200
            data = response.json()
            assert data["fit_score"] == 0.85


def test_generate_cover_letter(client, mock_db):
    """Test generating a cover letter for a job."""
    from src.models.resume import Resume
    
    mock_db.get_job.return_value = JobPosting(
        company="Test Company",
        title="Software Engineer",
        description="We are looking for a Software Engineer with Python experience.",
    )
    mock_db.get_latest_resume.return_value = Resume(
        version=1,
        name="Test User",
        email="test@example.com",
        phone="123-456-7890",
        experience=[],
        projects=[],
        skills={},
    )
    
    with patch('src.generators.cover_letter_generator.CoverLetterGenerator') as mock_generator_class:
        mock_generator = Mock()
        mock_generator.generate.return_value = "Dear Hiring Manager,\n\nI am writing to apply..."
        mock_generator_class.return_value = mock_generator
        
        response = client.post("/api/v1/jobs/1/cover-letter")
        assert response.status_code == 200
        data = response.json()
        assert "cover_letter" in data
        assert len(data["cover_letter"]) > 0


def test_generate_cover_letter_job_not_found(client, mock_db):
    """Test generating cover letter for non-existent job."""
    mock_db.get_job.return_value = None
    
    response = client.post("/api/v1/jobs/999/cover-letter")
    assert response.status_code == 404


def test_generate_cover_letter_no_resume(client, mock_db):
    """Test generating cover letter when no resume exists."""
    mock_db.get_job.return_value = JobPosting(
        company="Test Company",
        title="Software Engineer",
        description="Test description",
    )
    mock_db.get_latest_resume.return_value = None
    
    response = client.post("/api/v1/jobs/1/cover-letter")
    assert response.status_code == 404
