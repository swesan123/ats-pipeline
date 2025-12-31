"""Resumes API models."""

from typing import Optional
from pydantic import BaseModel


class ResumeResponse(BaseModel):
    """Resume response model."""
    id: int
    version: str
    file_path: Optional[str] = None
    job_id: Optional[int] = None
    is_customized: bool = False
    updated_at: Optional[str] = None


class ResumeRewriteRequest(BaseModel):
    """Request model for rewriting a resume."""
    job_id: int
    rewrite_intent: Optional[str] = "emphasize_skills"


class ResumeRenderRequest(BaseModel):
    """Request model for rendering a resume to PDF."""
    resume_id: int
