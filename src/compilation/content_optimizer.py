"""Content optimizer for reordering resume sections by job relevance."""

from typing import List, Dict, Set
from src.models.resume import Resume, ExperienceItem, ProjectItem
from src.models.job import JobMatch, JobSkills


class ResumeContentOptimizer:
    """Optimize resume content order within sections by job relevance."""
    
    def __init__(self, job_match: JobMatch, job_skills: JobSkills):
        """Initialize optimizer with job context.
        
        Args:
            job_match: Job match information
            job_skills: Job skills for relevance scoring
        """
        self.job_match = job_match
        self.job_skills = job_skills
        
        # Create set of job-relevant skills for fast lookup
        self.job_skill_set = {
            skill.lower().strip() 
            for skill in (job_skills.required_skills + job_skills.preferred_skills)
            if skill.strip()
        }
    
    def optimize_experience_order(self, resume: Resume) -> Resume:
        """Reorder experience items by job relevance.
        
        Args:
            resume: Resume to optimize
        
        Returns: Resume with reordered experience items
        """
        # Score each experience item
        scored_experience = []
        for exp in resume.experience:
            score = self._score_experience(exp)
            scored_experience.append((score, exp))
        
        # Sort by score (highest first)
        scored_experience.sort(key=lambda x: x[0], reverse=True)
        
        # Create new resume with reordered experience
        updated_resume = resume.model_copy(deep=True)
        updated_resume.experience = [exp for _, exp in scored_experience]
        
        return updated_resume
    
    def optimize_projects_order(self, resume: Resume) -> Resume:
        """Reorder projects by job relevance.
        
        Args:
            resume: Resume to optimize
        
        Returns: Resume with reordered projects
        """
        # Score each project
        scored_projects = []
        for proj in resume.projects:
            score = self._score_project(proj)
            scored_projects.append((score, proj))
        
        # Sort by score (highest first)
        scored_projects.sort(key=lambda x: x[0], reverse=True)
        
        # Create new resume with reordered projects
        updated_resume = resume.model_copy(deep=True)
        updated_resume.projects = [proj for _, proj in scored_projects]
        
        return updated_resume
    
    def optimize_skills_order(self, resume: Resume) -> Resume:
        """Reorder skills within categories by job relevance.
        
        Args:
            resume: Resume to optimize
        
        Returns: Resume with reordered skills
        """
        updated_resume = resume.model_copy(deep=True)
        
        # Reorder skills within each category
        for category, skills_list in updated_resume.skills.items():
            # Score each skill
            scored_skills = []
            for skill in skills_list:
                score = self._score_skill(skill)
                scored_skills.append((score, skill))
            
            # Sort by score (highest first)
            scored_skills.sort(key=lambda x: x[0], reverse=True)
            
            # Update category with reordered skills
            updated_resume.skills[category] = [skill for _, skill in scored_skills]
        
        return updated_resume
    
    def optimize_all(self, resume: Resume) -> Resume:
        """Optimize all sections: experience, projects, and skills.
        
        Args:
            resume: Resume to optimize
        
        Returns: Resume with all sections optimized
        """
        updated_resume = self.optimize_experience_order(resume)
        updated_resume = self.optimize_projects_order(updated_resume)
        updated_resume = self.optimize_skills_order(updated_resume)
        
        return updated_resume
    
    def _score_experience(self, exp: ExperienceItem) -> float:
        """Score an experience item by job relevance.
        
        Args:
            exp: Experience item to score
        
        Returns: Relevance score (0.0-1.0)
        """
        score = 0.0
        
        # Count job-relevant skills in bullets
        job_relevant_count = 0
        total_skills = 0
        
        for bullet in exp.bullets:
            for skill in bullet.skills:
                total_skills += 1
                if self._is_job_relevant(skill):
                    job_relevant_count += 1
        
        # Skill relevance ratio
        if total_skills > 0:
            score += (job_relevant_count / total_skills) * 0.6
        
        # Check if organization/role mentions job-relevant terms
        org_lower = exp.organization.lower()
        role_lower = exp.role.lower()
        
        for job_skill in self.job_skill_set:
            if job_skill in org_lower or job_skill in role_lower:
                score += 0.2
                break
        
        # Boost score if experience matches job requirements
        matching_skills = set(skill.lower() for skill in self.job_match.matching_skills)
        exp_skills = set(skill.lower() for bullet in exp.bullets for skill in bullet.skills)
        overlap = len(matching_skills & exp_skills)
        if len(matching_skills) > 0:
            score += (overlap / len(matching_skills)) * 0.2
        
        return min(score, 1.0)
    
    def _score_project(self, proj: ProjectItem) -> float:
        """Score a project by job relevance.
        
        Args:
            proj: Project item to score
        
        Returns: Relevance score (0.0-1.0)
        """
        score = 0.0
        
        # Count job-relevant skills in tech stack
        job_relevant_tech = 0
        total_tech = len(proj.tech_stack)
        
        for tech in proj.tech_stack:
            if self._is_job_relevant(tech):
                job_relevant_tech += 1
        
        # Tech stack relevance ratio
        if total_tech > 0:
            score += (job_relevant_tech / total_tech) * 0.5
        
        # Count job-relevant skills in bullets
        job_relevant_bullets = 0
        total_bullet_skills = 0
        
        for bullet in proj.bullets:
            for skill in bullet.skills:
                total_bullet_skills += 1
                if self._is_job_relevant(skill):
                    job_relevant_bullets += 1
        
        # Bullet skill relevance ratio
        if total_bullet_skills > 0:
            score += (job_relevant_bullets / total_bullet_skills) * 0.3
        
        # Check if project name mentions job-relevant terms
        proj_name_lower = proj.name.lower()
        for job_skill in self.job_skill_set:
            if job_skill in proj_name_lower:
                score += 0.2
                break
        
        return min(score, 1.0)
    
    def _score_skill(self, skill: str) -> float:
        """Score a skill by job relevance.
        
        Args:
            skill: Skill to score
        
        Returns: Relevance score (0.0-1.0)
        """
        if self._is_job_relevant(skill):
            return 1.0
        
        # Check if skill is in matching skills
        skill_lower = skill.lower().strip()
        if skill_lower in {s.lower().strip() for s in self.job_match.matching_skills}:
            return 0.8
        
        # Check if skill is related to job skills (partial match)
        for job_skill in self.job_skill_set:
            if job_skill in skill_lower or skill_lower in job_skill:
                return 0.5
        
        return 0.0
    
    def _is_job_relevant(self, skill: str) -> bool:
        """Check if a skill is job-relevant.
        
        Args:
            skill: Skill to check
        
        Returns: True if skill is job-relevant
        """
        skill_lower = skill.lower().strip()
        
        # Direct match
        if skill_lower in self.job_skill_set:
            return True
        
        # Partial match (skill contains or is contained in job skill)
        for job_skill in self.job_skill_set:
            if skill_lower in job_skill or job_skill in skill_lower:
                return True
        
        return False

