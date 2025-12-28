"""Project selection based on job relevance."""

from typing import List, Optional
from src.models.resume import ProjectItem
from src.models.job import JobSkills
from src.projects.project_library import ProjectLibrary


class ProjectSelector:
    """Select most relevant projects for a job posting."""
    
    def __init__(self, library: Optional[ProjectLibrary] = None):
        """Initialize project selector.
        
        Args:
            library: Project library instance. If None, creates a new one.
        """
        if library is None:
            library = ProjectLibrary()
        self.library = library
    
    def select_projects(
        self,
        job_skills: JobSkills,
        max_projects: int = 4,
        min_score: float = 0.3
    ) -> List[ProjectItem]:
        """Select most relevant projects for a job.
        
        Args:
            job_skills: Job skills requirements
            max_projects: Maximum number of projects to select
            min_score: Minimum relevance score (0-1) to include a project
        
        Returns:
            List of selected projects, sorted by relevance (highest first)
        """
        all_projects = self.library.get_all_projects()
        
        if not all_projects:
            return []
        
        # Score all projects
        scored_projects = []
        for project in all_projects:
            score = self._score_project(project, job_skills)
            if score >= min_score:
                scored_projects.append((score, project))
        
        # Sort by score (highest first)
        scored_projects.sort(key=lambda x: x[0], reverse=True)
        
        # Return top N projects
        return [project for _, project in scored_projects[:max_projects]]
    
    def _score_project(self, project: ProjectItem, job_skills: JobSkills) -> float:
        """Calculate relevance score for a project (0-1).
        
        Scoring factors:
        - Tech stack overlap with required skills (weight: 2.0)
        - Tech stack overlap with preferred skills (weight: 1.0)
        - Skills mentioned in bullets (weight: 1.5)
        - Keyword matching in project name/description (weight: 0.5)
        """
        score = 0.0
        total_weight = 0.0
        
        # Normalize tech stack and bullet skills to lowercase for comparison
        project_tech_lower = [t.lower() for t in project.tech_stack]
        project_skills_lower = set()
        for bullet in project.bullets:
            project_skills_lower.update(s.lower() for s in bullet.skills)
        
        # Score: Tech stack vs required skills (weight: 2.0)
        if job_skills.required_skills:
            required_lower = [s.lower() for s in job_skills.required_skills]
            overlap = self._calculate_overlap(project_tech_lower, required_lower)
            score += overlap * 2.0
            total_weight += 2.0
        
        # Score: Tech stack vs preferred skills (weight: 1.0)
        if job_skills.preferred_skills:
            preferred_lower = [s.lower() for s in job_skills.preferred_skills]
            overlap = self._calculate_overlap(project_tech_lower, preferred_lower)
            score += overlap * 1.0
            total_weight += 1.0
        
        # Score: Bullet skills vs required skills (weight: 1.5)
        if job_skills.required_skills and project_skills_lower:
            required_lower = [s.lower() for s in job_skills.required_skills]
            overlap = self._calculate_overlap(list(project_skills_lower), required_lower)
            score += overlap * 1.5
            total_weight += 1.5
        
        # Score: Bullet skills vs preferred skills (weight: 1.0)
        if job_skills.preferred_skills and project_skills_lower:
            preferred_lower = [s.lower() for s in job_skills.preferred_skills]
            overlap = self._calculate_overlap(list(project_skills_lower), preferred_lower)
            score += overlap * 1.0
            total_weight += 1.0
        
        # Score: Keyword matching in project name (weight: 0.5)
        project_name_lower = project.name.lower()
        all_job_skills_lower = []
        if job_skills.required_skills:
            all_job_skills_lower.extend(s.lower() for s in job_skills.required_skills)
        if job_skills.preferred_skills:
            all_job_skills_lower.extend(s.lower() for s in job_skills.preferred_skills)
        
        keyword_matches = sum(1 for skill in all_job_skills_lower if skill in project_name_lower)
        if all_job_skills_lower:
            keyword_score = min(keyword_matches / len(all_job_skills_lower), 1.0)
            score += keyword_score * 0.5
            total_weight += 0.5
        
        # Normalize score
        if total_weight > 0:
            score = score / total_weight
        else:
            score = 0.0
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _calculate_overlap(self, list1: List[str], list2: List[str]) -> float:
        """Calculate Jaccard similarity between two lists (case-insensitive)."""
        if not list1 or not list2:
            return 0.0
        
        set1 = set(list1)
        set2 = set(list2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
        
        return intersection / union

