"""Tests for SkillMatcher to prevent import/runtime regressions."""

from src.matching.skill_matcher import SkillMatcher
from src.models.resume import Resume, ExperienceItem, Bullet
from src.models.job import JobSkills
from src.models.skills import SkillOntology


def test_match_job_runs_without_import_errors():
    """Ensure SkillMatcher.match_job executes without NameError (e.g., missing json/time)."""
    ontology = SkillOntology()
    matcher = SkillMatcher(ontology)

    # Minimal resume with one bullet and one skill
    exp = ExperienceItem(
        organization="TestOrg",
        role="Engineer",
        location="Nowhere",
        start_date=None,
        end_date=None,
        bullets=[Bullet(text="Did things in Python.", skills=["Python"], evidence=None)],
    )
    resume = Resume(
        name="Test User",
        phone=None,
        email=None,
        linkedin=None,
        github=None,
        location=None,
        citizenship=None,
        experience=[exp],
        education=[],
        skills={"Languages": ["Python"]},
        projects=[],
        hobbies=[],
        courses=[],
    )

    job_skills = JobSkills(
        required_skills=["Python"],
        preferred_skills=[],
        soft_skills=[],
        seniority_indicators=[],
    )

    result = matcher.match_job(resume, job_skills)
    assert 0.0 <= result.fit_score <= 1.0


