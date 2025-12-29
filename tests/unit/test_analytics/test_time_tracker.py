"""Unit tests for TimeToApplyTracker."""

import pytest
from datetime import datetime, timedelta
from src.analytics.time_tracker import TimeToApplyTracker
from src.db.database import Database
from src.models.job import JobPosting


def test_start_tracking(test_db):
    """Test starting time-to-apply tracking."""
    tracker = TimeToApplyTracker(test_db)
    
    # Create a test job
    job = JobPosting(
        company="Test Co",
        title="Test Job",
        description="Test description"
    )
    job_id = test_db.save_job(job)
    
    # Start tracking
    tracking_id = tracker.start_tracking(job_id)
    assert tracking_id > 0
    
    # Verify tracking record exists
    cursor = test_db.conn.cursor()
    cursor.execute("SELECT * FROM time_to_apply WHERE job_id = ?", (job_id,))
    record = cursor.fetchone()
    assert record is not None
    assert record['applied_at'] is None


def test_complete_tracking(test_db):
    """Test completing time-to-apply tracking."""
    tracker = TimeToApplyTracker(test_db)
    
    # Create a test job
    job = JobPosting(
        company="Test Co",
        title="Test Job",
        description="Test description"
    )
    job_id = test_db.save_job(job)
    
    # Start tracking
    created_at = datetime.now() - timedelta(hours=2)
    tracker.start_tracking(job_id, created_at)
    
    # Complete tracking
    duration = tracker.complete_tracking(job_id)
    assert duration is not None
    assert duration.total_seconds() > 0
    
    # Verify duration was stored
    time_to_apply = tracker.get_time_to_apply(job_id)
    assert time_to_apply is not None
    assert time_to_apply.total_seconds() > 0


def test_get_stats(test_db):
    """Test getting time-to-apply statistics."""
    tracker = TimeToApplyTracker(test_db)
    
    # Create test jobs with different durations
    for i in range(3):
        job = JobPosting(
            company=f"Test Co {i}",
            title=f"Test Job {i}",
            description="Test"
        )
        job_id = test_db.save_job(job)
        
        created_at = datetime.now() - timedelta(hours=i+1)
        tracker.start_tracking(job_id, created_at)
        tracker.complete_tracking(job_id)
    
    stats = tracker.get_stats()
    assert stats['count'] == 3
    assert stats['average_seconds'] is not None
    assert stats['min_seconds'] is not None
    assert stats['max_seconds'] is not None

