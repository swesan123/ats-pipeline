"""Skill ontology and skill models."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class Skill(BaseModel):
    """A single skill with metadata."""
    
    name: str = Field(..., description="Canonical skill name")
    category: str = Field(..., description="Skill category (technical/soft/domain)")
    proficiency_level: Optional[str] = Field(None, description="Proficiency level (beginner/intermediate/advanced/expert)")
    evidence: List[str] = Field(default_factory=list, description="Bullet IDs or text snippets demonstrating this skill")
    
    def __hash__(self) -> int:
        """Make Skill hashable for use in sets."""
        return hash(self.name.lower())
    
    def __eq__(self, other) -> bool:
        """Compare skills by name (case-insensitive)."""
        if isinstance(other, Skill):
            return self.name.lower() == other.name.lower()
        return False


class SkillOntology(BaseModel):
    """Canonical skill ontology with taxonomy."""
    
    canonical_skills: Dict[str, Skill] = Field(default_factory=dict, description="Canonical skills by name")
    taxonomy: Dict[str, List[str]] = Field(default_factory=dict, description="Skill taxonomy by category")
    
    def find_skill(self, skill_name: str) -> Optional[Skill]:
        """Find a skill by name (case-insensitive, with normalization)."""
        normalized = self.normalize_skill_name(skill_name)
        return self.canonical_skills.get(normalized)
    
    def normalize_skill_name(self, skill_name: str) -> str:
        """Normalize skill name for matching (lowercase, strip whitespace)."""
        return skill_name.lower().strip()
    
    def get_evidence_for_skill(self, skill_name: str) -> List[str]:
        """Get evidence bullets for a skill."""
        skill = self.find_skill(skill_name)
        if skill:
            return skill.evidence
        return []
    
    def add_skill(self, skill: Skill) -> None:
        """Add a skill to the ontology."""
        normalized = self.normalize_skill_name(skill.name)
        self.canonical_skills[normalized] = skill
        
        # Update taxonomy
        if skill.category not in self.taxonomy:
            self.taxonomy[skill.category] = []
        if normalized not in self.taxonomy[skill.category]:
            self.taxonomy[skill.category].append(normalized)
    
    def get_skills_by_category(self, category: str) -> List[Skill]:
        """Get all skills in a category."""
        skill_names = self.taxonomy.get(category, [])
        return [self.canonical_skills[name] for name in skill_names if name in self.canonical_skills]

