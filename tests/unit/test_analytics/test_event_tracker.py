"""Unit tests for EventTracker."""

import pytest
from datetime import datetime
from src.analytics.event_tracker import EventTracker
from src.db.database import Database


def test_track_event(test_db):
    """Test tracking an event."""
    tracker = EventTracker(test_db)
    
    event_id = tracker.track_event(
        EventTracker.EVENT_JOB_ADDED,
        metadata={'job_id': 1, 'company': 'Test Co', 'title': 'Test Job'}
    )
    
    assert event_id > 0
    
    # Verify event was stored
    events = tracker.get_events(EventTracker.EVENT_JOB_ADDED, limit=1)
    assert len(events) == 1
    assert events[0]['event_type'] == EventTracker.EVENT_JOB_ADDED
    assert events[0]['metadata']['job_id'] == 1


def test_get_event_count(test_db):
    """Test getting event count."""
    tracker = EventTracker(test_db)
    
    # Track multiple events
    tracker.track_event(EventTracker.EVENT_JOB_ADDED, {'job_id': 1})
    tracker.track_event(EventTracker.EVENT_JOB_ADDED, {'job_id': 2})
    tracker.track_event(EventTracker.EVENT_RESUME_GENERATED, {'resume_id': 1})
    
    assert tracker.get_event_count(EventTracker.EVENT_JOB_ADDED) == 2
    assert tracker.get_event_count(EventTracker.EVENT_RESUME_GENERATED) == 1


def test_get_events_filtered(test_db):
    """Test getting events filtered by type."""
    tracker = EventTracker(test_db)
    
    tracker.track_event(EventTracker.EVENT_JOB_ADDED, {'job_id': 1})
    tracker.track_event(EventTracker.EVENT_RESUME_GENERATED, {'resume_id': 1})
    
    job_events = tracker.get_events(EventTracker.EVENT_JOB_ADDED)
    assert len(job_events) == 1
    assert job_events[0]['event_type'] == EventTracker.EVENT_JOB_ADDED

