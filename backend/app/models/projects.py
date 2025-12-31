"""Projects API models."""

from typing import List, Optional
from pydantic import BaseModel, Field
from src.models.resume import Bullet


class BulletRequest(BaseModel):
    """Bullet point request model."""
    text: str = Field(..., max_length=150)
    skills: List[str] = Field(default_factory=list)
    evidence: Optional[str] = None


class ProjectCreateRequest(BaseModel):
    """Request model for creating a project."""
    name: str
    tech_stack: List[str] = Field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    bullets: List[BulletRequest] = Field(default_factory=list)


class ProjectUpdateRequest(BaseModel):
    """Request model for updating a project."""
    name: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    bullets: Optional[List[BulletRequest]] = None


class GitHubImportRequest(BaseModel):
    """Request model for importing project from GitHub."""
    url: str = Field(..., description="GitHub repository URL")


class ProjectResponse(BaseModel):
    """Project response model."""
    name: str
    tech_stack: List[str] = []
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    bullets: List[BulletRequest] = []
