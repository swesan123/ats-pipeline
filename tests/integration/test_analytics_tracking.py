"""Integration tests for analytics tracking."""

import pytest
from datetime import datetime
from src.db.database import Database
from src.models.job import JobPosting, JobSkills
from src.analytics.analytics_service import AnalyticsService
from src.analytics.event_tracker import EventTracker


def test_job_added_event_tracking(test_db):
    """Test that job_added event is tracked when saving a job."""
    analytics = AnalyticsService(test_db)
    
    # Save a job
    job = JobPosting(
        company="Test Co",
        title="Test Job",
        description="Test description"
    )
    job_id = test_db.save_job(job)
    
    # Verify event was tracked
    event_count = analytics.event_tracker.get_event_count(EventTracker.EVENT_JOB_ADDED)
    assert event_count >= 1
    
    # Verify time-to-apply tracking started
    time_to_apply = analytics.time_tracker.get_time_to_apply(job_id)
    # Should be None since not applied yet
    assert time_to_apply is None
    
    # Check that tracking record exists
    cursor = test_db.conn.cursor()
    cursor.execute("SELECT * FROM time_to_apply WHERE job_id = ?", (job_id,))
    record = cursor.fetchone()
    assert record is not None


def test_status_change_to_applied_tracking(test_db):
    """Test that time-to-apply is completed when status changes to Applied."""
    analytics = AnalyticsService(test_db)
    
    # Create and save job
    job = JobPosting(
        company="Test Co",
        title="Test Job",
        description="Test"
    )
    job_id = test_db.save_job(job)
    
    # Change status to Applied
    test_db.update_job_status(job_id, "Applied")
    
    # Verify time-to-apply was calculated
    time_to_apply = analytics.time_tracker.get_time_to_apply(job_id)
    assert time_to_apply is not None
    assert time_to_apply.total_seconds() >= 0
    
    # Verify status change event was tracked
    event_count = analytics.event_tracker.get_event_count(EventTracker.EVENT_JOB_STATUS_CHANGED)
    assert event_count >= 1


def test_analytics_service_key_metrics(test_db):
    """Test AnalyticsService key metrics calculation."""
    analytics = AnalyticsService(test_db)
    
    # Create some test data
    for i in range(3):
        job = JobPosting(
            company=f"Test Co {i}",
            title=f"Test Job {i}",
            description="Test"
        )
        job_id = test_db.save_job(job)
        if i == 0:
            test_db.update_job_status(job_id, "Applied")
    
    metrics = analytics.get_key_metrics()
    
    assert 'total_jobs' in metrics
    assert 'applications_submitted' in metrics
    assert metrics['total_jobs'] >= 3
    assert metrics['applications_submitted'] >= 1

