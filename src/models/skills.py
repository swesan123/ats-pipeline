"""Skill ontology and skill models."""

from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field


class Skill(BaseModel):
    """A single skill with metadata."""
    
    name: str = Field(..., description="Canonical skill name")
    category: str = Field(..., description="Skill category (technical/soft/domain)")
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


class SkillEvidence(BaseModel):
    """Evidence source for a skill."""
    
    source_type: str = Field(..., description="Type of evidence: 'experience', 'project', 'certification', 'coursework'")
    source_name: str = Field(..., description="Name of the source (e.g., project name, company name, course name)")
    evidence_text: Optional[str] = Field(None, description="Optional text snippet demonstrating the skill")
    date: Optional[str] = Field(None, description="Optional date when this evidence was acquired")


class UserSkill(BaseModel):
    """A user-provided skill with project associations and evidence sources."""
    
    name: str = Field(..., description="Skill name")
    category: str = Field(..., description="Skill category (e.g., Languages, ML/AI, Backend/DB)")
    projects: List[str] = Field(default_factory=list, description="List of project names that use this skill (deprecated - use evidence_sources instead)")
    evidence_sources: List[SkillEvidence] = Field(default_factory=list, description="List of evidence sources (experience, projects, certifications, coursework)")


class UserSkills(BaseModel):
    """User-provided skills library to prevent skill fabrication."""
    
    skills: List[UserSkill] = Field(default_factory=list, description="List of user skills")
    
    def get_all_skill_names(self) -> Set[str]:
        """Get all skill names as a set (normalized)."""
        return {skill.name.lower().strip() for skill in self.skills}
    
    def get_skills_for_project(self, project_name: str) -> List[str]:
        """Get all skills associated with a specific project."""
        project_skills = []
        for skill in self.skills:
            # Check legacy projects list
            if project_name in skill.projects:
                if skill.name not in project_skills:
                    project_skills.append(skill.name)
            # Check evidence sources
            for evidence in skill.evidence_sources:
                if evidence.source_type == "project" and evidence.source_name == project_name:
                    if skill.name not in project_skills:
                        project_skills.append(skill.name)
        return project_skills
    
    def has_skill(self, skill_name: str) -> bool:
        """Check if user has this skill (case-insensitive)."""
        normalized = skill_name.lower().strip()
        return normalized in self.get_all_skill_names()
    
    def get_skill(self, skill_name: str) -> Optional[UserSkill]:
        """Get a skill by name (case-insensitive)."""
        normalized = skill_name.lower().strip()
        for skill in self.skills:
            if skill.name.lower().strip() == normalized:
                return skill
        return None

