"""Experience API models."""

from typing import List, Optional
from pydantic import BaseModel, Field


class BulletRequest(BaseModel):
    """Bullet point request model."""
    text: str = Field(..., max_length=150)
    skills: List[str] = Field(default_factory=list)
    evidence: Optional[str] = None


class ExperienceCreateRequest(BaseModel):
    """Request model for creating experience."""
    organization: str
    role: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    bullets: List[BulletRequest] = Field(default_factory=list)


class ExperienceUpdateRequest(BaseModel):
    """Request model for updating experience."""
    organization: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    bullets: Optional[List[BulletRequest]] = None


class ExperienceResponse(BaseModel):
    """Experience response model."""
    organization: str
    role: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    bullets: List[BulletRequest] = []
