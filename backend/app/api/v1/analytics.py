"""Analytics API routes."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from backend.app.dependencies import get_db
from backend.app.models.analytics import (
    KeyMetricsResponse,
    SkillGapResponse,
    TimelineEventResponse,
    TimeToApplyStatsResponse,
    TimeToApplyDistributionResponse,
    ApplicationFunnelResponse,
    RecentActivityResponse,
)
from src.db.database import Database
from src.analytics.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/analytics/metrics", response_model=KeyMetricsResponse)
async def get_metrics(db: Database = Depends(get_db)):
    """Get key analytics metrics."""
    try:
        analytics = AnalyticsService(db)
        metrics = analytics.get_key_metrics()
        
        return KeyMetricsResponse(
            total_jobs=metrics.get('total_jobs', 0),
            applications_submitted=metrics.get('applications_submitted', 0),
            average_time_to_apply_seconds=metrics.get('average_time_to_apply_seconds'),
            resume_generation_count=metrics.get('resume_generation_count', 0),
            bullet_approval_rate=metrics.get('bullet_approval_rate', 0.0),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/skills", response_model=List[SkillGapResponse])
async def get_skill_gaps(
    db: Database = Depends(get_db),
    limit: int = 100,
    by: str = "priority",
):
    """Get skill gaps analysis."""
    try:
        analytics = AnalyticsService(db)
        
        if by == "priority":
            skills = analytics.get_missing_skills_ranked(limit=limit, by='priority')
        else:
            skills = analytics.get_missing_skills_ranked(limit=limit, by='frequency')
        
        result = []
        for skill in skills:
            result.append(SkillGapResponse(
                skill_name=skill.get('skill_name', ''),
                priority_score=skill.get('priority_score', 0.0),
                frequency_count=skill.get('frequency_count', 0),
                required_count=skill.get('required_count', 0),
                preferred_count=skill.get('preferred_count', 0),
                general_count=skill.get('general_count', 0),
                resume_coverage=skill.get('resume_coverage', 'none'),
                is_generic=skill.get('is_generic', False),
            ))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/timeline", response_model=List[TimelineEventResponse])
async def get_timeline(
    db: Database = Depends(get_db),
    days: int = 30,
):
    """Get application timeline events."""
    try:
        analytics = AnalyticsService(db)
        events = analytics.get_application_timeline(days=days)
        
        result = []
        for event in events:
            result.append(TimelineEventResponse(
                date=event.get('date', ''),
                event_type=event.get('event_type', ''),
                description=event.get('description', ''),
                metadata=event.get('metadata'),
            ))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/time-to-apply-stats", response_model=TimeToApplyStatsResponse)
async def get_time_to_apply_stats(db: Database = Depends(get_db)):
    """Get time-to-apply statistics."""
    try:
        analytics = AnalyticsService(db)
        stats = analytics.get_time_to_apply_stats()
        return TimeToApplyStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/time-to-apply-distribution", response_model=List[TimeToApplyDistributionResponse])
async def get_time_to_apply_distribution(db: Database = Depends(get_db)):
    """Get time-to-apply distribution."""
    try:
        analytics = AnalyticsService(db)
        distribution = analytics.get_time_to_apply_distribution()
        return [TimeToApplyDistributionResponse(**item) for item in distribution]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/application-funnel", response_model=ApplicationFunnelResponse)
async def get_application_funnel(db: Database = Depends(get_db)):
    """Get application funnel data."""
    try:
        analytics = AnalyticsService(db)
        funnel = analytics.get_application_funnel()
        return ApplicationFunnelResponse(**funnel)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/missing-skills-analysis")
async def get_missing_skills_analysis(db: Database = Depends(get_db)):
    """Get missing skills analysis."""
    try:
        analytics = AnalyticsService(db)
        analysis = analytics.get_missing_skills_by_category(limit=100)
        return analysis  # Return dict directly
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/recent-activity", response_model=List[RecentActivityResponse])
async def get_recent_activity(db: Database = Depends(get_db)):
    """Get recent activity events."""
    try:
        analytics = AnalyticsService(db)
        events = analytics.get_application_timeline(days=30)
        return [RecentActivityResponse(**event) for event in events[:20]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
