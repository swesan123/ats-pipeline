"""Integration tests for time-to-apply tracking."""

import pytest
from datetime import datetime, timedelta
from src.db.database import Database
from src.models.job import JobPosting
from src.analytics.time_tracker import TimeToApplyTracker


def test_time_to_apply_full_workflow(test_db):
    """Test complete time-to-apply workflow."""
    tracker = TimeToApplyTracker(test_db)
    
    # Create job (this should start tracking automatically via hook)
    job = JobPosting(
        company="Test Co",
        title="Test Job",
        description="Test"
    )
    job_id = test_db.save_job(job)
    
    # Verify tracking started
    cursor = test_db.conn.cursor()
    cursor.execute("SELECT * FROM time_to_apply WHERE job_id = ?", (job_id,))
    record = cursor.fetchone()
    assert record is not None
    assert record['applied_at'] is None
    
    # Simulate time passing (update created_at)
    past_time = datetime.now() - timedelta(hours=5)
    cursor.execute("""
        UPDATE time_to_apply SET created_at = ? WHERE job_id = ?
    """, (past_time, job_id))
    test_db.conn.commit()
    
    # Change status to Applied (this should complete tracking)
    test_db.update_job_status(job_id, "Applied")
    
    # Verify time-to-apply was calculated
    time_to_apply = tracker.get_time_to_apply(job_id)
    assert time_to_apply is not None
    assert time_to_apply.total_seconds() > 0
    
    # Should be approximately 5 hours (within 1 minute tolerance)
    assert abs(time_to_apply.total_seconds() - 5 * 3600) < 60


def test_time_to_apply_stats_calculation(test_db):
    """Test time-to-apply statistics calculation."""
    tracker = TimeToApplyTracker(test_db)
    
    # Create multiple jobs with different durations
    durations = [1, 2, 3, 4, 5]  # hours
    for hours in durations:
        job = JobPosting(
            company=f"Test Co {hours}",
            title=f"Test Job {hours}",
            description="Test"
        )
        job_id = test_db.save_job(job)
        
        # Set created_at in the past
        past_time = datetime.now() - timedelta(hours=hours)
        cursor = test_db.conn.cursor()
        cursor.execute("""
            UPDATE time_to_apply SET created_at = ? WHERE job_id = ?
        """, (past_time, job_id))
        test_db.conn.commit()
        
        # Complete tracking
        test_db.update_job_status(job_id, "Applied")
    
    # Get stats
    stats = tracker.get_stats()
    
    assert stats['count'] == len(durations)
    assert stats['average_seconds'] is not None
    assert stats['min_seconds'] is not None
    assert stats['max_seconds'] is not None
    assert stats['median_seconds'] is not None
    
    # Average should be approximately 3 hours (middle of 1-5)
    avg_hours = stats['average_seconds'] / 3600
    assert 2.5 <= avg_hours <= 3.5

