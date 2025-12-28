"""Resume reuse checker for finding existing resumes that match new job requirements."""

from typing import Optional, Tuple
from src.db.database import Database
from src.matching.skill_matcher import SkillMatcher
from src.matching.job_similarity import JobSimilarityMatcher
from src.models.job import JobSkills
from src.models.resume import Resume


class ResumeReuseChecker:
    """Check if existing resumes can be reused for new job applications."""
    
    def __init__(self, db: Database, skill_matcher: SkillMatcher):
        """Initialize reuse checker with database and skill matcher."""
        self.db = db
        self.skill_matcher = skill_matcher
        self.similarity_matcher = JobSimilarityMatcher()
    
    def find_reusable_resume(
        self,
        target_job_skills: JobSkills,
        target_job_id: Optional[int] = None,
        min_fit_score: float = 0.90,
        min_similarity: float = 0.85,
    ) -> Optional[Tuple[int, Resume, float, float]]:
        """Find a reusable resume for target job.
        
        Args:
            target_job_skills: Skills required for target job
            target_job_id: ID of target job (to exclude from similarity search)
            min_fit_score: Minimum fit score required (0-1)
            min_similarity: Minimum job similarity required (0-1)
        
        Returns:
            Tuple of (resume_id, Resume, fit_score, similarity_score) if found, None otherwise
        """
        # Get all jobs from database
        all_jobs_data = self.db.get_all_jobs()
        
        # Convert to (job_id, JobSkills) tuples
        all_jobs = []
        for job_data in all_jobs_data:
            job_id = job_data.get('id')
            if not job_id:
                continue  # Skip if no ID
            
            if target_job_id and job_id == target_job_id:
                continue  # Skip target job
            
            # Try to get job_skills from the dict first, then fallback to database
            if 'job_skills' in job_data and job_data['job_skills']:
                job_skills = job_data['job_skills']
            else:
                job_skills = self.db.get_job_skills(job_id)
            
            if job_skills:
                all_jobs.append((job_id, job_skills))
        
        # Find similar jobs
        similar_jobs = self.similarity_matcher.find_similar_jobs(
            target_job_skills,
            all_jobs,
            similarity_threshold=min_similarity,
        )
        
        # For each similar job, check for reusable resumes
        for similar_job_id, similar_job_skills, similarity_score in similar_jobs:
            # Get resumes customized for this similar job
            resume_ids = self.db.get_resumes_for_job(similar_job_id)
            
            for resume_id in resume_ids:
                resume = self.db.get_resume(resume_id)
                if not resume:
                    continue
                
                # Calculate fit score against target job
                job_match = self.skill_matcher.match_job(resume, target_job_skills)
                
                if job_match.fit_score >= min_fit_score:
                    # Found a reusable resume!
                    return (resume_id, resume, job_match.fit_score, similarity_score)
        
        return None

