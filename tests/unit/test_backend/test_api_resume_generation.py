"""Tests for resume generation API endpoints."""

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
from src.models.resume import Resume, Bullet, Reasoning, BulletCandidate
from src.models.job import JobPosting, JobSkills, JobMatch
from src.compilation.resume_rewriter import ResumeRewriter
from src.matching.skill_matcher import SkillMatcher
from src.models.skills import SkillOntology, UserSkills


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


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
def sample_resume():
    """Sample resume for testing."""
    return Resume(
        version="1",
        name="Test User",
        email="test@example.com",
        phone="123-456-7890",
        experience=[],
        projects=[],
        skills={},
    )


@pytest.fixture
def sample_job():
    """Sample job for testing."""
    return JobPosting(
        company="Test Company",
        title="Software Engineer",
        description="Test description",
    )


@pytest.fixture
def sample_job_skills():
    """Sample job skills for testing."""
    return JobSkills(
        required_skills=["Python", "React"],
        preferred_skills=["Docker"],
        soft_skills=[],
        seniority_indicators=[],
    )


@pytest.fixture
def sample_variations():
    """Sample variations for testing."""
    reasoning = Reasoning(
        problem_identification="Test problem",
        analysis="Test analysis",
        solution_approach="Test approach",
        evaluation="Test evaluation",
        alternatives_considered=[],
        confidence_score=0.85,
    )
    candidate = BulletCandidate(
        candidate_id="test-1",
        text="Test bullet text",
        score={"job_skill_coverage": 0.9, "ats_keyword_gain": 2, "semantic_similarity": 0.85, "constraint_violations": 0},
        diff_from_original={"added": ["Python"], "removed": []},
        justification={"why_this_version": "Test justification"},
        risk_level="low",
        composite_score=0.88,
    )
    return {"exp_TestOrg_0": (reasoning, [candidate])}


def test_start_resume_generation_success(client, mock_db, sample_resume, sample_job, sample_job_skills, sample_variations):
    """Test successful resume generation start."""
    app.dependency_overrides[get_db] = lambda: mock_db
    
    mock_db.get_job.return_value = sample_job
    mock_db.get_latest_resume.return_value = sample_resume
    mock_db.get_job_skills.return_value = sample_job_skills
    
    with patch('backend.app.api.v1.resume_generation.SkillMatcher') as mock_matcher_class, \
         patch('backend.app.api.v1.resume_generation.ResumeRewriter') as mock_rewriter_class, \
         patch('pathlib.Path.exists', return_value=False):
        
        mock_matcher = Mock()
        mock_match = JobMatch(
            job_id=1,
            fit_score=0.85,
            matching_skills=["Python"],
            missing_skills=["React"],
        )
        mock_matcher.match_job.return_value = mock_match
        mock_matcher_class.return_value = mock_matcher
        
        mock_rewriter = Mock()
        mock_rewriter.generate_variations.return_value = sample_variations
        mock_rewriter_class.return_value = mock_rewriter
        
        response = client.post(
            "/api/v1/resume-generation/start",
            json={"job_id": 1, "rewrite_intent": "emphasize_skills"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "variations" in data
        assert "total_bullets" in data
        assert data["job_id"] == 1
    
    app.dependency_overrides = {}


def test_start_resume_generation_job_not_found(client, mock_db):
    """Test resume generation with non-existent job."""
    app.dependency_overrides[get_db] = lambda: mock_db
    mock_db.get_job.return_value = None
    
    response = client.post(
        "/api/v1/resume-generation/start",
        json={"job_id": 999, "rewrite_intent": "emphasize_skills"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    
    app.dependency_overrides = {}


def test_start_resume_generation_no_resume(client, mock_db, sample_job):
    """Test resume generation with no resume."""
    app.dependency_overrides[get_db] = lambda: mock_db
    mock_db.get_job.return_value = sample_job
    mock_db.get_latest_resume.return_value = None
    
    response = client.post(
        "/api/v1/resume-generation/start",
        json={"job_id": 1, "rewrite_intent": "emphasize_skills"}
    )
    
    assert response.status_code == 404
    assert "no resume" in response.json()["detail"].lower()
    
    app.dependency_overrides = {}


def test_regenerate_bullet_success(client, mock_db, sample_resume, sample_job, sample_job_skills, sample_variations):
    """Test successful bullet regeneration."""
    app.dependency_overrides[get_db] = lambda: mock_db
    
    mock_db.get_job.return_value = sample_job
    mock_db.get_latest_resume.return_value = sample_resume
    mock_db.get_job_skills.return_value = sample_job_skills
    
    with patch('backend.app.api.v1.resume_generation.SkillMatcher') as mock_matcher_class, \
         patch('backend.app.api.v1.resume_generation.ResumeRewriter') as mock_rewriter_class, \
         patch('pathlib.Path.exists', return_value=False):
        
        mock_matcher = Mock()
        mock_match = JobMatch(
            job_id=1,
            fit_score=0.85,
            matching_skills=["Python"],
            missing_skills=["React"],
        )
        mock_matcher.match_job.return_value = mock_match
        mock_matcher_class.return_value = mock_matcher
        
        mock_rewriter = Mock()
        mock_rewriter.generate_variations.return_value = sample_variations
        mock_rewriter_class.return_value = mock_rewriter
        
        response = client.post(
            "/api/v1/resume-generation/regenerate-bullet?bullet_id=exp_TestOrg_0",
            json={"job_id": 1, "rewrite_intent": "more_technical"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "bullet_id" in data
        assert "reasoning" in data
        assert "candidates" in data
    
    app.dependency_overrides = {}


def test_complete_resume_generation_success(client, mock_db, sample_resume, sample_job, sample_job_skills, sample_variations):
    """Test successful resume generation completion."""
    app.dependency_overrides[get_db] = lambda: mock_db
    
    mock_db.get_job.return_value = sample_job
    mock_db.get_latest_resume.return_value = sample_resume
    mock_db.get_job_skills.return_value = sample_job_skills
    mock_db.save_resume.return_value = 1
    
    with patch('backend.app.api.v1.resume_generation.SkillMatcher') as mock_matcher_class, \
         patch('backend.app.api.v1.resume_generation.ResumeRewriter') as mock_rewriter_class, \
         patch('pathlib.Path.exists', return_value=False):
        
        mock_matcher = Mock()
        mock_match = JobMatch(
            job_id=1,
            fit_score=0.85,
            matching_skills=["Python"],
            missing_skills=["React"],
        )
        mock_matcher.match_job.return_value = mock_match
        mock_matcher_class.return_value = mock_matcher
        
        mock_rewriter = Mock()
        mock_rewriter.generate_variations.return_value = sample_variations
        mock_rewriter_class.return_value = mock_rewriter
        
        response = client.post(
            "/api/v1/resume-generation/complete",
            json={
                "job_id": 1,
                "approved_bullets": {"exp_TestOrg_0": 0}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "resume_id" in data
        assert "resume" in data
    
    app.dependency_overrides = {}
