"""Resume data models with Pydantic validation."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class Justification(BaseModel):
    """Justification for a bullet point change."""
    
    trigger: str = Field(..., description="Job requirement that prompted this change")
    skills_added: List[str] = Field(default_factory=list, description="Skills added or emphasized")
    ats_keywords_added: List[str] = Field(default_factory=list, description="ATS keywords added")


class Reasoning(BaseModel):
    """Enhanced reasoning chain for bullet point changes."""
    
    problem_identification: str = Field(..., description="What gap/issue prompted this change")
    analysis: str = Field(..., description="Analysis of current bullet vs job requirements")
    solution_approach: str = Field(..., description="Why this approach was chosen")
    evaluation: str = Field(..., description="Why this variation works better")
    alternatives_considered: List[str] = Field(default_factory=list, description="Other approaches considered")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in this change (0-1)")


class BulletCandidate(BaseModel):
    """A candidate bullet variation with metadata for ranking and approval."""
    
    candidate_id: str = Field(..., description="Unique identifier for this candidate")
    text: str = Field(..., description="Bullet text")
    score: Dict[str, float] = Field(..., description="Score components: job_skill_coverage, ats_keyword_gain, semantic_similarity, constraint_violations")
    diff_from_original: Dict[str, List[str]] = Field(..., description="What was added and removed from original")
    justification: Dict[str, Any] = Field(..., description="Justification: job_requirements_addressed, skills_mapped, why_this_version")
    risk_level: str = Field(..., description="Risk level: low, medium, or high")
    rewrite_intent: Optional[str] = Field(None, description="Rewrite intent: emphasize_skills, more_technical, more_concise, conservative")
    composite_score: float = Field(..., description="Composite score for ranking (0.0-1.0)")
    
    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, v: str) -> str:
        """Validate risk level."""
        if v not in ["low", "medium", "high"]:
            raise ValueError(f"Risk level must be 'low', 'medium', or 'high', got {v}")
        return v
    
    @field_validator("text")
    @classmethod
    def validate_text_length(cls, v: str) -> str:
        """Validate bullet text length."""
        if len(v) > 150:
            raise ValueError(f"Bullet text must be 150 characters or less, got {len(v)}")
        return v


class BulletHistory(BaseModel):
    """History of changes to a bullet point."""
    
    original_text: str = Field(..., description="Original bullet text")
    new_text: str = Field(..., description="New bullet text")
    justification: Justification = Field(..., description="Justification for the change")
    reasoning: Optional[Reasoning] = Field(None, description="Reasoning chain for the change")
    approved_by_human: bool = Field(False, description="Whether this change was approved by human")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the change was made")
    selected_variation_index: Optional[int] = Field(None, ge=0, le=3, description="Which variation was selected (0-3)")
    candidate_id: Optional[str] = Field(None, description="ID of the selected BulletCandidate")
    decision_metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata about the decision (score, risk_level, etc.)")


class Bullet(BaseModel):
    """A single bullet point in an experience item."""
    
    text: str = Field(..., description="Bullet point text")
    skills: List[str] = Field(default_factory=list, description="Skills mentioned in this bullet")
    evidence: Optional[str] = Field(None, description="Evidence supporting this bullet")
    history: List[BulletHistory] = Field(default_factory=list, description="History of changes to this bullet")
    
    @field_validator("text")
    @classmethod
    def validate_text_length(cls, v: str) -> str:
        """Validate bullet text length."""
        if len(v) > 150:
            raise ValueError(f"Bullet text must be 150 characters or less, got {len(v)}")
        return v
    
    @field_validator("skills")
    @classmethod
    def validate_skills(cls, v: List[str]) -> List[str]:
        """Normalize and deduplicate skills."""
        from src.utils.skill_categorizer import _deduplicate_skills
        if not v:
            return []
        return _deduplicate_skills(v)


class ExperienceItem(BaseModel):
    """A work experience entry."""
    
    organization: str = Field(..., description="Company or organization name")
    role: str = Field(..., description="Job title or role")
    location: str = Field(..., description="Location (city, state/country)")
    start_date: str = Field(..., description="Start date (e.g., 'Sep 2021')")
    end_date: Optional[str] = Field(None, description="End date (e.g., 'Apr 2026' or 'Present')")
    bullets: List[Bullet] = Field(default_factory=list, description="Bullet points describing the role")


class EducationItem(BaseModel):
    """An education entry."""
    
    institution: str = Field(..., description="School or university name")
    location: str = Field(..., description="Location")
    degree: str = Field(..., description="Degree name")
    start_date: Optional[str] = Field(None, description="Start date")
    end_date: Optional[str] = Field(None, description="End date or expected graduation")


class ProjectItem(BaseModel):
    """A project entry."""
    
    name: str = Field(..., description="Project name")
    tech_stack: List[str] = Field(default_factory=list, description="Technologies used")
    start_date: Optional[str] = Field(None, description="Start date")
    end_date: Optional[str] = Field(None, description="End date or 'Present'")
    bullets: List[Bullet] = Field(default_factory=list, description="Bullet points describing the project")
    
    @field_validator("tech_stack")
    @classmethod
    def validate_tech_stack(cls, v: List[str]) -> List[str]:
        """Normalize and deduplicate tech stack."""
        from src.utils.skill_categorizer import _deduplicate_skills
        if not v:
            return []
        return _deduplicate_skills(v)


class Resume(BaseModel):
    """Root resume model with all sections."""
    
    # Metadata
    name: str = Field(..., description="Full name")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    github: Optional[str] = Field(None, description="GitHub profile URL")
    location: Optional[str] = Field(None, description="Location")
    citizenship: Optional[str] = Field(None, description="Citizenship status")
    
    # Sections
    experience: List[ExperienceItem] = Field(default_factory=list, description="Work experience")
    education: List[EducationItem] = Field(default_factory=list, description="Education")
    skills: dict[str, List[str]] = Field(default_factory=dict, description="Skills by category")
    projects: List[ProjectItem] = Field(default_factory=list, description="Projects")
    hobbies: List[str] = Field(default_factory=list, description="Hobbies and interests")
    courses: List[str] = Field(default_factory=list, description="Relevant courses")
    
    @field_validator("skills")
    @classmethod
    def validate_skills_dict(cls, v: dict[str, List[str]]) -> dict[str, List[str]]:
        """Normalize and deduplicate skills in each category."""
        from src.utils.skill_categorizer import _deduplicate_skills
        normalized = {}
        for category, skills_list in v.items():
            if skills_list:
                normalized[category] = _deduplicate_skills(skills_list)
            else:
                normalized[category] = []
        return normalized
    
    # Versioning
    version: int = Field(1, description="Resume version number")
    date_created: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    date_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

