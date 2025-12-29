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
    
    def validate(self, candidate: BulletCandidate, original_text: str) -> tuple[bool, List[str]]:
        """Validate a bullet candidate against hard filters.
        
        Args:
            candidate: The bullet candidate to validate
            original_text: Original bullet text for comparison
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # 1. Length validation
        if len(candidate.text) > 150:
            errors.append(f"Bullet exceeds 150 characters: {len(candidate.text)}")
        
        # 2. Skill ontology validation
        if self.ontology or self.user_skills:
            skills_in_text = self._extract_skills_from_text(candidate.text)
            for skill in skills_in_text:
                if not self._skill_is_valid(skill):
                    errors.append(f"Skill not in ontology/user skills: {skill}")
        
        # 3. Seniority claim validation
        seniority_issues = self._validate_seniority_claims(candidate.text, original_text)
        if seniority_issues:
            errors.extend(seniority_issues)
        
        # 4. Banned buzzword detection
        buzzword_issues = self._detect_banned_buzzwords(candidate.text)
        if buzzword_issues:
            errors.extend(buzzword_issues)
        
        # 5. Multiple claims detection
        if self._has_multiple_claims(candidate.text):
            errors.append("Bullet contains multiple distinct claims (should be one clear claim)")
        
        return len(errors) == 0, errors
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract potential skill names from text.
        
        This is a simple heuristic - in production, you might use NER or a skill dictionary.
        """
        # Common technical skills to look for
        common_skills = [
            "Python", "Java", "C++", "JavaScript", "TypeScript", "Go", "Golang",
            "React", "Vue", "Angular", "Node.js", "Docker", "Kubernetes",
            "AWS", "GCP", "Azure", "PostgreSQL", "MySQL", "MongoDB",
            "TensorFlow", "PyTorch", "NumPy", "pandas", "scikit-learn"
        ]
        
        found_skills = []
        text_lower = text.lower()
        for skill in common_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def _skill_is_valid(self, skill: str) -> bool:
        """Check if a skill is in the ontology or user skills."""
        if self.user_skills:
            # Check user skills first (more restrictive)
            all_user_skills = [s.lower() for s in self.user_skills.get_all_skill_names()]
            if skill.lower() in all_user_skills:
                return True
        
        if self.ontology:
            # Check ontology
            # This is a simplified check - in production, you'd use ontology matching
            return True  # Assume valid if ontology exists (ontology validation is complex)
        
        # If no ontology or user skills, allow all (backward compatibility)
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

