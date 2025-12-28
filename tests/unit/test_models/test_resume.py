"""Unit tests for resume models."""

import pytest
from datetime import datetime
from src.models.resume import Resume, ExperienceItem, Bullet, BulletHistory, Justification, Reasoning


def test_resume_creation():
    """Test creating a Resume."""
    resume = Resume(name="Test User", email="test@example.com")
    assert resume.name == "Test User"
    assert resume.email == "test@example.com"
    assert resume.version == 1


def test_bullet_text_length_validation():
    """Test bullet text length validation."""
    # Valid bullet
    bullet = Bullet(text="Short bullet")
    assert bullet.text == "Short bullet"
    
    # Invalid bullet (too long)
    with pytest.raises(ValueError):
        Bullet(text="x" * 151)


def test_bullet_history_creation():
    """Test creating BulletHistory."""
    justification = Justification(
        trigger="Job requires Python",
        skills_added=["Python"],
        ats_keywords_added=["Python", "API"],
    )
    reasoning = Reasoning(
        problem_identification="Missing Python skill",
        analysis="Current bullet doesn't mention Python",
        solution_approach="Add Python to bullet text",
        evaluation="Better match for job requirements",
        alternatives_considered=["Alternative 1", "Alternative 2"],
        confidence_score=0.85,
    )
    
    history = BulletHistory(
        original_text="Developed web applications",
        new_text="Developed web applications using Python",
        justification=justification,
        reasoning=reasoning,
        approved_by_human=True,
        selected_variation_index=0,
    )
    
    assert history.original_text == "Developed web applications"
    assert history.approved_by_human is True
    assert history.selected_variation_index == 0


def test_resume_serialization(sample_resume):
    """Test resume JSON serialization."""
    json_data = sample_resume.model_dump_json()
    assert isinstance(json_data, str)
    
    # Deserialize
    resume_from_json = Resume.model_validate_json(json_data)
    assert resume_from_json.name == sample_resume.name

