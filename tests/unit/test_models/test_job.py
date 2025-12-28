"""Unit tests for job models."""

import pytest
from src.models.job import JobPosting, JobSkills, JobMatch


def test_job_posting_creation():
    """Test creating a JobPosting."""
    job = JobPosting(
        company="Test Company",
        title="Software Engineer",
        description="Job description here",
    )
    assert job.company == "Test Company"
    assert job.title == "Software Engineer"


def test_job_skills_creation():
    """Test creating JobSkills."""
    skills = JobSkills(
        required_skills=["Python", "React"],
        preferred_skills=["Docker"],
        soft_skills=["Communication"],
    )
    assert len(skills.required_skills) == 2
    assert len(skills.preferred_skills) == 1


def test_job_match_fit_score_validation():
    """Test JobMatch fit score validation."""
    # Valid fit score
    match = JobMatch(fit_score=0.85)
    assert match.fit_score == 0.85
    
    # Invalid fit score (too high)
    with pytest.raises(ValueError):
        JobMatch(fit_score=1.5)
    
    # Invalid fit score (negative)
    with pytest.raises(ValueError):
        JobMatch(fit_score=-0.1)

