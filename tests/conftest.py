"""Pytest fixtures and configuration."""

import pytest
from pathlib import Path
from src.models.resume import Resume, ExperienceItem, Bullet, EducationItem
from src.models.job import JobPosting, JobSkills
from src.models.skills import SkillOntology
from src.db.database import Database


@pytest.fixture
def sample_resume():
    """Sample resume for testing."""
    return Resume(
        name="Test User",
        email="test@example.com",
        phone="+1-123-456-7890",
        experience=[
            ExperienceItem(
                organization="Test Company",
                role="Software Engineer",
                location="San Francisco, CA",
                start_date="Jan 2020",
                end_date="Present",
                bullets=[
                    Bullet(text="Developed web applications using Python and React", skills=["Python", "React"]),
                    Bullet(text="Implemented REST APIs with Flask", skills=["Flask", "REST"]),
                ],
            )
        ],
        education=[
            EducationItem(
                institution="Test University",
                location="Test City",
                degree="BS Computer Science",
                start_date="2016",
                end_date="2020",
            )
        ],
        skills={"Languages": ["Python", "JavaScript"], "Frameworks": ["React", "Flask"]},
    )


@pytest.fixture
def sample_job_skills():
    """Sample job skills for testing."""
    return JobSkills(
        required_skills=["Python", "React", "REST"],
        preferred_skills=["Docker", "Kubernetes"],
        soft_skills=["Communication", "Teamwork"],
        seniority_indicators=["3+ years", "Senior"],
    )


@pytest.fixture
def sample_job_posting():
    """Sample job posting for testing."""
    return JobPosting(
        company="Test Company",
        title="Senior Software Engineer",
        location="San Francisco, CA",
        description="We are looking for a Senior Software Engineer with Python and React experience.",
    )


@pytest.fixture
def empty_ontology():
    """Empty skill ontology for testing."""
    return SkillOntology()


@pytest.fixture
def test_db(tmp_path):
    """Test database instance."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    yield db
    db.close()

