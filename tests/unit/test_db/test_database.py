"""Unit tests for database operations."""

import pytest
from src.db.database import Database
from src.models.resume import Resume, Justification, Reasoning
from src.models.job import JobPosting, JobSkills


def test_database_creation(test_db):
    """Test database creation."""
    assert test_db is not None


def test_save_and_get_resume(test_db, sample_resume):
    """Test saving and retrieving resume."""
    resume_id = test_db.save_resume(sample_resume)
    assert resume_id > 0
    
    retrieved = test_db.get_resume(resume_id)
    assert retrieved is not None
    assert retrieved.name == sample_resume.name


def test_save_job(test_db, sample_job_posting, sample_job_skills):
    """Test saving job."""
    job_id = test_db.save_job(sample_job_posting, sample_job_skills)
    assert job_id > 0
    
    job = test_db.get_job(job_id)
    assert job is not None
    assert job.company == sample_job_posting.company


def test_save_bullet_change(test_db, sample_resume):
    """Test saving bullet change with reasoning."""
    resume_id = test_db.save_resume(sample_resume)
    
    justification = Justification(
        trigger="Job requires Python",
        skills_added=["Python"],
    )
    reasoning = Reasoning(
        problem_identification="Missing Python",
        analysis="Need to add Python",
        solution_approach="Add Python to bullet",
        evaluation="Better match",
        confidence_score=0.8,
    )
    
    change_id = test_db.save_bullet_change(
        resume_id=resume_id,
        bullet_id="test_bullet_1",
        original_text="Original text",
        new_text="New text with Python",
        justification=justification,
        reasoning=reasoning,
        selected_variation_index=0,
        approved_by_human=True,
    )
    
    assert change_id > 0
    
    changes = test_db.get_bullet_changes(resume_id)
    assert len(changes) == 1
    assert changes[0]["bullet_id"] == "test_bullet_1"

