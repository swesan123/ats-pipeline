"""Automatic validation filters for bullet candidates."""

from typing import List, Optional
from src.models.resume import BulletCandidate
from src.models.skills import SkillOntology, UserSkills


class BulletValidator:
    """Validate bullet candidates against hard constraints."""
    
    # Banned buzzwords that indicate fabrication or overstatement
    BANNED_BUZZWORDS = [
        "revolutionary", "game-changing", "cutting-edge", "state-of-the-art",
        "world-class", "industry-leading", "best-in-class", "top-tier",
        "unprecedented", "groundbreaking", "innovative solution", "disruptive"
    ]
    
    # Seniority claim keywords that should be validated
    SENIORITY_CLAIMS = [
        "led", "managed", "architected", "designed system", "built team",
        "established", "founded", "directed", "oversaw", "supervised"
    ]
    
    def __init__(self, ontology: Optional[SkillOntology] = None, user_skills: Optional[UserSkills] = None):
        """Initialize validator.
        
        Args:
            ontology: Skill ontology for validation
            user_skills: User-defined skills for validation
        """
        self.ontology = ontology
        self.user_skills = user_skills
    
    def validate(self, candidate: BulletCandidate, original_text: str, job_skills: Optional[List[str]] = None, rewrite_intent: Optional[str] = None) -> tuple[bool, List[str]]:
        """Validate a bullet candidate against hard filters.
        
        Args:
            candidate: The bullet candidate to validate
            original_text: Original bullet text for comparison
            job_skills: Optional list of job skills for intersection validation
            rewrite_intent: Optional rewrite intent ("reword_only" enforces no skill changes)
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # 1. Length validation
        if len(candidate.text) > 150:
            errors.append(f"Bullet exceeds 150 characters: {len(candidate.text)}")
        
        # 2. Skill whitelist validation (user skills first, then ontology)
        if self.ontology or self.user_skills:
            skills_in_text = self._extract_skills_from_text(candidate.text)
            for skill in skills_in_text:
                if not self._skill_is_valid(skill, job_skills):
                    errors.append(f"Skill not in allowed set (or not job-relevant): {skill}")
        
        # 3. For reword_only mode: ensure skill set is preserved
        if rewrite_intent == "reword_only":
            original_skills = self._extract_skills_from_text(original_text)
            new_skills = self._extract_skills_from_text(candidate.text)
            # Normalize for comparison
            original_skills_normalized = {s.lower().strip() for s in original_skills}
            new_skills_normalized = {s.lower().strip() for s in new_skills}
            
            # Check if any new skills were added
            added_skills = new_skills_normalized - original_skills_normalized
            if added_skills:
                errors.append(f"Reword-only mode: Cannot add new skills. Added: {', '.join(added_skills)}")
        
        # 4. Seniority claim validation
        seniority_issues = self._validate_seniority_claims(candidate.text, original_text)
        if seniority_issues:
            errors.extend(seniority_issues)
        
        # 5. Banned buzzword detection
        buzzword_issues = self._detect_banned_buzzwords(candidate.text)
        if buzzword_issues:
            errors.extend(buzzword_issues)
        
        # 6. Multiple claims detection
        if self._has_multiple_claims(candidate.text):
            errors.append("Bullet contains multiple distinct claims (should be one clear claim)")
        
        return len(errors) == 0, errors
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract potential skill names from text.
        
        This focuses on skills that exist in the user's Skills page or ontology.
        Uses a more comprehensive approach to match skills from allowed sets.
        """
        found_skills = []
        text_lower = text.lower()
        
        # First, check against user skills if available
        if self.user_skills:
            user_skill_names = self.user_skills.get_all_skill_names()
            for skill_name in user_skill_names:
                skill_lower = skill_name.lower()
                # Check for exact word match or skill name as a word in text
                import re
                # Match whole words only (case-insensitive)
                pattern = re.compile(r'\b' + re.escape(skill_lower) + r'\b', re.IGNORECASE)
                if pattern.search(text_lower):
                    found_skills.append(skill_name)
        
        # Also check against ontology if available (but prioritize user skills)
        if self.ontology and not found_skills:
            # Use ontology canonical skills
            for skill_name in self.ontology.canonical_skills.keys():
                skill_lower = skill_name.lower()
                import re
                pattern = re.compile(r'\b' + re.escape(skill_lower) + r'\b', re.IGNORECASE)
                if pattern.search(text_lower):
                    found_skills.append(skill_name)
        
        return found_skills
    
    def _skill_is_valid(self, skill: str, job_skills: Optional[List[str]] = None) -> bool:
        """Check if a skill is valid (in user skills and optionally job-relevant).
        
        Args:
            skill: Skill name to validate
            job_skills: Optional list of job skills to intersect with (for strict job-relevance)
        
        Returns:
            True if skill is valid (in user skills and optionally in job skills)
        """
        if self.user_skills:
            # Strict mode: only allow skills explicitly listed by the user.
            all_user_skills = {s.lower() for s in self.user_skills.get_all_skill_names()}
            skill_lower = skill.lower().strip()
            
            # Must be in user skills
            if skill_lower not in all_user_skills:
                return False
            
            # If job_skills provided, also require skill to be job-relevant
            if job_skills:
                job_skills_lower = {s.lower().strip() for s in job_skills}
                # Check for exact match or partial match (skill contains job skill or vice versa)
                for job_skill in job_skills_lower:
                    if skill_lower == job_skill or skill_lower in job_skill or job_skill in skill_lower:
                        return True
                # Not in job skills - reject
                return False
            
            # In user skills and no job filter - valid
            return True
        
        if self.ontology:
            # If we have an ontology but no user skills, fall back to ontology-only validation.
            # (Currently treated as permissive; ontology-specific checks can be added later.)
            return True
        
        # If no ontology or user skills, allow all (backward compatibility).
        return True
    
    def _validate_seniority_claims(self, candidate_text: str, original_text: str) -> List[str]:
        """Validate that seniority claims are not newly introduced."""
        errors = []
        candidate_lower = candidate_text.lower()
        original_lower = original_text.lower()
        
        for claim in self.SENIORITY_CLAIMS:
            if claim in candidate_lower and claim not in original_lower:
                errors.append(f"New seniority claim introduced: '{claim}'")
        
        return errors
    
    def _detect_banned_buzzwords(self, text: str) -> List[str]:
        """Detect banned buzzwords in text."""
        errors = []
        text_lower = text.lower()
        
        for buzzword in self.BANNED_BUZZWORDS:
            if buzzword in text_lower:
                errors.append(f"Banned buzzword detected: '{buzzword}'")
        
        return errors
    
    def _has_multiple_claims(self, text: str) -> bool:
        """Check if bullet contains multiple distinct claims.
        
        Simple heuristic: count action verbs and coordinating conjunctions.
        """
        # Count action verbs (simple heuristic)
        action_verbs = ["developed", "built", "created", "designed", "implemented", "optimized", "improved", "reduced", "increased"]
        text_lower = text.lower()
        
        verb_count = sum(1 for verb in action_verbs if verb in text_lower)
        
        # Count coordinating conjunctions
        conjunctions = [" and ", " while ", " also ", " plus ", " as well as "]
        conjunction_count = sum(1 for conj in conjunctions if conj in text_lower)
        
        # If more than 2 action verbs or coordinating conjunctions, likely multiple claims
        return verb_count > 2 or conjunction_count > 1

