"""Job posting and job matching models."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class JobPosting(BaseModel):
    """A job posting."""
    
    company: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title")
    location: Optional[str] = Field(None, description="Job location")
    description: str = Field(..., description="Full job description text")
    source_url: Optional[str] = Field(None, description="URL where job was found")
    date_posted: Optional[datetime] = Field(None, description="Date job was posted")
    raw_text: Optional[str] = Field(None, description="Raw job posting text")


class JobSkills(BaseModel):
    """Extracted skills from a job posting."""
    
    required_skills: List[str] = Field(default_factory=list, description="Required skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Preferred skills")
    soft_skills: List[str] = Field(default_factory=list, description="Soft skills mentioned")
    seniority_indicators: List[str] = Field(default_factory=list, description="Seniority level indicators")


class JobMatch(BaseModel):
    """Job matching results and gap analysis."""
    
    job_id: Optional[int] = Field(None, description="Foreign key to job posting")
    fit_score: float = Field(..., ge=0.0, le=1.0, description="Overall fit score (0-1)")
    skill_gaps: Dict[str, List[str]] = Field(default_factory=dict, description="Skill gaps by category")
    missing_skills: List[str] = Field(default_factory=list, description="Skills genuinely missing (not in ontology)")
    matching_skills: List[str] = Field(default_factory=list, description="Skills that match job requirements")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improving fit")
    
    @field_validator("fit_score")
    @classmethod
    def validate_fit_score(cls, v: float) -> float:
        """Validate fit score is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Fit score must be between 0 and 1, got {v}")
        return v

