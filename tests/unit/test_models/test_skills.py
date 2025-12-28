"""Unit tests for skill models."""

import pytest
from src.models.skills import Skill, SkillOntology


def test_skill_creation():
    """Test creating a Skill."""
    skill = Skill(
        name="Python",
        category="technical",
        proficiency_level="advanced",
        evidence=["bullet1", "bullet2"],
    )
    assert skill.name == "Python"
    assert skill.category == "technical"
    assert len(skill.evidence) == 2


def test_skill_ontology():
    """Test SkillOntology operations."""
    ontology = SkillOntology()
    
    skill = Skill(name="Python", category="technical")
    ontology.add_skill(skill)
    
    found = ontology.find_skill("Python")
    assert found is not None
    assert found.name == "Python"
    
    # Case insensitive
    found_lower = ontology.find_skill("python")
    assert found_lower is not None


def test_skill_normalization():
    """Test skill name normalization."""
    ontology = SkillOntology()
    normalized = ontology.normalize_skill_name("  Python  ")
    assert normalized == "python"


def test_skill_equality():
    """Test skill equality (case insensitive)."""
    skill1 = Skill(name="Python", category="technical")
    skill2 = Skill(name="python", category="technical")
    assert skill1 == skill2

