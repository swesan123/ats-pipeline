"""Analytics API models."""

from typing import List, Dict, Optional
from pydantic import BaseModel


class KeyMetricsResponse(BaseModel):
    """Key metrics response."""
    total_jobs: int
    applications_submitted: int
    average_time_to_apply_seconds: Optional[float] = None
    resume_generation_count: int
    bullet_approval_rate: float


class SkillGapResponse(BaseModel):
    """Skill gap response."""
    skill_name: str
    priority_score: float
    frequency_count: int
    required_count: int
    preferred_count: int
    general_count: int
    resume_coverage: str
    is_generic: bool


class TimelineEventResponse(BaseModel):
    """Timeline event response."""
    date: str
    event_type: str
    description: str
    metadata: Optional[Dict] = None


class TimeToApplyStatsResponse(BaseModel):
    """Time-to-apply statistics response."""
    count: int
    average_seconds: Optional[float] = None
    median_seconds: Optional[float] = None
    min_seconds: Optional[float] = None
    max_seconds: Optional[float] = None


class TimeToApplyDistributionResponse(BaseModel):
    """Time-to-apply distribution response."""
    duration_seconds: float


class ApplicationFunnelResponse(BaseModel):
    """Application funnel response."""
    status_counts: Dict[str, int]
    conversion_rates: Dict[str, float]
    total: int


class MissingSkillsAnalysisResponse(BaseModel):
    """Missing skills analysis response."""
    pass  # This is a dict mapping category -> list of skills


class RecentActivityResponse(BaseModel):
    """Recent activity response."""
    date: str
    event_type: str
    description: str
    metadata: Optional[Dict] = None
