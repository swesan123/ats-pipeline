"""Job similarity matching for resume reuse."""

from typing import List, Tuple
from src.models.job import JobSkills


class JobSimilarityMatcher:
    """Match jobs by similarity for resume reuse."""
    
    def find_similar_jobs(
        self,
        target_job_skills: JobSkills,
        all_jobs: List[Tuple[int, JobSkills]],
        similarity_threshold: float = 0.85,
    ) -> List[Tuple[int, JobSkills, float]]:
        """Find similar jobs.
        
        Args:
            target_job_skills: Target job skills to match against
            all_jobs: List of (job_id, JobSkills) tuples
            similarity_threshold: Minimum similarity score (0-1)
        
        Returns:
            List of (job_id, JobSkills, similarity_score) tuples, sorted by similarity (highest first)
        """
        similar_jobs = []
        
        for job_id, job_skills in all_jobs:
            similarity = self._calculate_similarity(target_job_skills, job_skills)
            if similarity >= similarity_threshold:
                similar_jobs.append((job_id, job_skills, similarity))
        
        # Sort by similarity (highest first)
        similar_jobs.sort(key=lambda x: x[2], reverse=True)
        
        return similar_jobs
    
    def _calculate_similarity(self, job1: JobSkills, job2: JobSkills) -> float:
        """Calculate weighted similarity score between two jobs.
        
        Uses Jaccard similarity (intersection / union) for each skill category.
        Returns weighted average.
        """
        # Normalize skills (lowercase, strip)
        def normalize_skills(skills: List[str]) -> set:
            return {s.lower().strip() for s in skills if s.strip()}
        
        required1 = normalize_skills(job1.required_skills)
        required2 = normalize_skills(job2.required_skills)
        preferred1 = normalize_skills(job1.preferred_skills)
        preferred2 = normalize_skills(job2.preferred_skills)
        soft1 = normalize_skills(job1.soft_skills)
        soft2 = normalize_skills(job2.soft_skills)
        
        # Calculate Jaccard similarity for each category
        def jaccard_similarity(set1: set, set2: set) -> float:
            if not set1 and not set2:
                return 1.0
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            return intersection / union if union > 0 else 0.0
        
        required_sim = jaccard_similarity(required1, required2)
        preferred_sim = jaccard_similarity(preferred1, preferred2)
        soft_sim = jaccard_similarity(soft1, soft2)
        
        # Weighted average: required × 2.0, preferred × 1.0, soft × 0.5
        total_weight = 2.0 + 1.0 + 0.5
        weighted_score = (
            required_sim * 2.0 +
            preferred_sim * 1.0 +
            soft_sim * 0.5
        ) / total_weight
        
        return weighted_score

