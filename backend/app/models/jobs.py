"""Job API models."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class JobCreateRequest(BaseModel):
    """Request model for creating a job."""
    url: Optional[str] = Field(None, description="Job URL to scrape")
    description: Optional[str] = Field(None, description="Job description text")
    title: Optional[str] = Field(None, description="Manual job title (overrides auto-detection)")
    company: Optional[str] = Field(None, description="Manual company name (overrides auto-detection)")
    status: Optional[str] = Field(None, description="Job status")
    notes: Optional[str] = Field(None, description="Notes")


class JobUpdateRequest(BaseModel):
    """Request model for updating a job."""
    status: Optional[str] = None
    notes: Optional[str] = None
    contact_name: Optional[str] = None
    date_applied: Optional[datetime] = None


class ExtractSkillsRequest(BaseModel):
    """Request model for extracting skills."""
    url: Optional[str] = Field(None, description="Job URL to extract skills from")
    description: Optional[str] = Field(None, description="Job description text to extract skills from")


class JobSkillsResponse(BaseModel):
    """Job skills response model."""
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    soft_skills: List[str] = []
    seniority_indicators: List[str] = []


class JobMatchResponse(BaseModel):
    """Job match response model."""
    fit_score: float
    matched_skills: List[str] = []
    missing_skills: List[str] = []


class JobResponse(BaseModel):
    """Job response model."""
    id: int
    company: str
    title: str
    location: Optional[str] = None
    description: str
    source_url: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    contact_name: Optional[str] = None
    date_applied: Optional[datetime] = None
    date_added: Optional[datetime] = None
    job_skills: Optional[JobSkillsResponse] = None
    match: Optional[JobMatchResponse] = None
    has_resume: Optional[bool] = Field(None, description="Whether this job has a generated resume")
    latest_resume_id: Optional[int] = Field(None, description="ID of the latest resume for this job")