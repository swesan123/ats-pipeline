"""Helper functions for job-related operations."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.db.database import Database
from src.models.resume import Resume
from src.matching.skill_matcher import SkillMatcher
from src.models.skills import SkillOntology
from src.extractors.job_skills import JobSkillExtractor
from src.models.job import JobPosting


def auto_match_skills(db: Database, job_id: int, resume: Resume) -> float:
    """Auto-match skills for a job and cache the result.
    
    Args:
        db: Database instance
        job_id: Job ID to match
        resume: Resume to match against
        
    Returns:
        Fit score (0.0 to 1.0)
    """
    # Check if skills are already extracted
    job_skills = db.get_job_skills(job_id)
    
    if not job_skills:
        # Extract skills from job description
        job = db.get_job(job_id)
        if job:
            extractor = JobSkillExtractor()
            job_skills = extractor.extract_skills(job)
            # Save extracted skills
            db.save_job(job, job_skills=job_skills)
    
    if not job_skills:
        return 0.0
    
    # Match skills
    ontology = SkillOntology()
    matcher = SkillMatcher(ontology)
    job_match = matcher.match_job(resume, job_skills)
    
    # Cache the result
    resume_id = db.get_latest_resume_id()
    if resume_id:
        db.save_job_match(job_match, job_id, resume_id)
    
    return job_match.fit_score

