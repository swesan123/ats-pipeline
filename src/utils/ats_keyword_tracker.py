"""Utility for tracking ATS keywords in resume customization."""

from typing import Dict, List, Set, Optional, Tuple
from src.models.resume import Bullet, Resume
from src.models.job import JobSkills


class ATSKeywordTracker:
    """Track original vs new keywords and job-relevant keywords."""
    
    def __init__(self, original_resume: Resume, job_skills: Optional[JobSkills] = None):
        """Initialize tracker with original resume and job skills.
        
        Args:
            original_resume: Original resume before customization
            job_skills: Optional job skills to identify job-relevant keywords
        """
        self.original_bullets: Dict[str, Bullet] = {}
        self.job_relevant_keywords: Set[str] = set()
        
        # Store original bullets by key
        bullet_id = 0
        for exp in original_resume.experience:
            for bullet in exp.bullets:
                bullet_key = f"exp_{exp.organization}_{bullet_id}"
                self.original_bullets[bullet_key] = bullet
                bullet_id += 1
        
        bullet_id = 0
        for proj in original_resume.projects:
            for bullet in proj.bullets:
                bullet_key = f"proj_{proj.name}_{bullet_id}"
                self.original_bullets[bullet_key] = bullet
                bullet_id += 1
        
        # Extract job-relevant keywords
        if job_skills:
            all_job_skills = (
                job_skills.required_skills + 
                job_skills.preferred_skills
            )
            # Normalize to lowercase for comparison
            self.job_relevant_keywords = {
                skill.lower().strip() 
                for skill in all_job_skills 
                if skill.strip()
            }
    
    def get_keyword_changes(
        self, 
        bullet_key: str, 
        new_bullet: Bullet
    ) -> Tuple[Set[str], Set[str], Set[str]]:
        """Get added, removed, and unchanged keywords for a bullet.
        
        Args:
            bullet_key: Key identifying the bullet (e.g., "exp_Company_0")
            new_bullet: New bullet after customization
        
        Returns:
            Tuple of (added_keywords, removed_keywords, unchanged_keywords)
        """
        original_bullet = self.original_bullets.get(bullet_key)
        if not original_bullet:
            # New bullet, all keywords are added
            return (set(new_bullet.skills), set(), set())
        
        original_skills = {s.lower().strip() for s in original_bullet.skills}
        new_skills = {s.lower().strip() for s in new_bullet.skills}
        
        added = new_skills - original_skills
        removed = original_skills - new_skills
        unchanged = original_skills & new_skills
        
        return (added, removed, unchanged)
    
    def is_job_relevant(self, keyword: str) -> bool:
        """Check if a keyword is job-relevant.
        
        Args:
            keyword: Skill/keyword to check
        
        Returns:
            True if keyword is job-relevant
        """
        keyword_lower = keyword.lower().strip()
        
        # Direct match
        if keyword_lower in self.job_relevant_keywords:
            return True
        
        # Partial match (keyword contains or is contained in job skill)
        for job_skill in self.job_relevant_keywords:
            if keyword_lower in job_skill or job_skill in keyword_lower:
                return True
        
        return False
    
    def get_highlighting_info(
        self,
        bullet_key: str,
        new_bullet: Bullet
    ) -> Dict[str, List[str]]:
        """Get information about which keywords should be highlighted.
        
        Args:
            bullet_key: Key identifying the bullet
            new_bullet: New bullet after customization
        
        Returns:
            Dict with keys:
            - "bold": List of keywords that should be bolded
            - "unbold": List of keywords that should not be bolded (were bolded before)
        """
        added, removed, unchanged = self.get_keyword_changes(bullet_key, new_bullet)
        
        # Keywords to bold:
        # - Job-relevant AND newly added
        # - Job-relevant AND unchanged (keep bolded)
        to_bold = []
        for keyword in new_bullet.skills:
            keyword_lower = keyword.lower().strip()
            keyword_added = keyword_lower in {s.lower().strip() for s in added}
            keyword_unchanged = keyword_lower in {s.lower().strip() for s in unchanged}
            
            if self.is_job_relevant(keyword):
                if keyword_added or keyword_unchanged:
                    to_bold.append(keyword)
        
        # Keywords to unbold:
        # - Not job-relevant AND were in original (remove bold)
        # - Removed from bullets
        to_unbold = []
        original_bullet = self.original_bullets.get(bullet_key)
        if original_bullet:
            for keyword in original_bullet.skills:
                keyword_lower = keyword.lower().strip()
                keyword_removed = keyword_lower in {s.lower().strip() for s in removed}
                
                if keyword_removed or not self.is_job_relevant(keyword):
                    to_unbold.append(keyword)
        
        return {
            "bold": to_bold,
            "unbold": to_unbold
        }

