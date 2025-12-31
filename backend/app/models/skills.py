"""Skills API models."""

from typing import List, Optional
from pydantic import BaseModel, Field


class SkillEvidenceRequest(BaseModel):
    """Skill evidence request model."""
    source_type: str
    source_name: str
    evidence_text: Optional[str] = None


class UserSkillRequest(BaseModel):
    """User skill request model."""
    name: str
    category: str
    projects: List[str] = Field(default_factory=list)
    evidence_sources: List[SkillEvidenceRequest] = Field(default_factory=list)


class UserSkillsRequest(BaseModel):
    """Request model for updating user skills."""
    skills: List[UserSkillRequest]


class UserSkillsResponse(BaseModel):
    """Response model for user skills."""
    skills: List[UserSkillRequest]
