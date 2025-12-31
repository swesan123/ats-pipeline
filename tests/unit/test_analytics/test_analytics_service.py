"""Tests for AnalyticsService."""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from src.analytics.analytics_service import AnalyticsService
from src.analytics.event_tracker import EventTracker


@pytest.fixture
def mock_db():
    """Create mock database."""
    db = Mock()
    db.conn = Mock()
    cursor_mock = Mock()
    cursor_mock.execute.return_value = None
    cursor_mock.fetchall.return_value = []
    cursor_mock.fetchone.return_value = {'count': 0}
    db.conn.cursor.return_value = cursor_mock
    return db


@pytest.fixture
def analytics_service(mock_db):
    """Create AnalyticsService instance with mocked dependencies."""
    service = AnalyticsService(mock_db)
    service.event_tracker = Mock(spec=EventTracker)
    service.time_tracker = Mock()
    service.skills_aggregator = Mock()
    return service


def test_get_application_timeline(analytics_service):
    """Test getting application timeline events."""
    # Mock events with various date formats
    mock_events = [
        {
            'id': 1,
            'event_type': EventTracker.EVENT_JOB_ADDED,
            'metadata': {'title': 'Software Engineer', 'company': 'TestCo'},
            'created_at': datetime.now() - timedelta(days=1),
        },
        {
            'id': 2,
            'event_type': EventTracker.EVENT_JOB_STATUS_CHANGED,
            'metadata': {'title': 'Engineer', 'old_status': 'New', 'new_status': 'Applied'},
            'created_at': datetime.now() - timedelta(days=2),
        },
        {
            'id': 3,
            'event_type': EventTracker.EVENT_RESUME_GENERATED,
            'metadata': {'job_title': 'Developer'},
            'created_at': datetime.now() - timedelta(days=35),  # Outside 30 day window
        },
    ]
    
    analytics_service.event_tracker.get_events.return_value = mock_events
    
    timeline = analytics_service.get_application_timeline(days=30)
    
    # Should only include events within 30 days
    assert len(timeline) == 2
    assert timeline[0]['event_type'] == EventTracker.EVENT_JOB_ADDED
    assert timeline[1]['event_type'] == EventTracker.EVENT_JOB_STATUS_CHANGED


def test_format_event_description_job_added(analytics_service):
    """Test formatting event description for job added."""
    metadata = {'title': 'Software Engineer', 'company': 'TestCo'}
    description = analytics_service._format_event_description(
        EventTracker.EVENT_JOB_ADDED,
        metadata
    )
    assert "Software Engineer" in description
    assert "TestCo" in description
    assert "added" in description.lower()


def test_format_event_description_job_status_changed(analytics_service):
    """Test formatting event description for job status changed."""
    metadata = {'title': 'Engineer', 'old_status': 'New', 'new_status': 'Applied'}
    description = analytics_service._format_event_description(
        EventTracker.EVENT_JOB_STATUS_CHANGED,
        metadata
    )
    assert "Engineer" in description
    assert "New" in description
    assert "Applied" in description


def test_format_event_description_resume_generated(analytics_service):
    """Test formatting event description for resume generated."""
    metadata = {'job_title': 'Developer'}
    description = analytics_service._format_event_description(
        EventTracker.EVENT_RESUME_GENERATED,
        metadata
    )
    assert "Developer" in description
    assert "generated" in description.lower()


def test_format_event_description_bullet_approved(analytics_service):
    """Test formatting event description for bullet approved."""
    description = analytics_service._format_event_description(
        EventTracker.EVENT_BULLET_APPROVED,
        {}
    )
    assert "approved" in description.lower()


def test_format_event_description_unknown_type(analytics_service):
    """Test formatting event description for unknown event type."""
    description = analytics_service._format_event_description(
        'unknown_event_type',
        {}
    )
    # Unknown types are formatted by replacing underscores with spaces and title casing
    assert description == 'Unknown Event Type'


def test_get_time_to_apply_distribution(analytics_service, mock_db):
    """Test getting time-to-apply distribution."""
    mock_db.conn.cursor.return_value.fetchall.return_value = [
        {'duration_seconds': 1800.0},
        {'duration_seconds': 3600.0},
        {'duration_seconds': 7200.0},
    ]
    
    distribution = analytics_service.get_time_to_apply_distribution()
    
    assert len(distribution) == 3
    assert distribution[0]['duration_seconds'] == 1800.0
    assert distribution[1]['duration_seconds'] == 3600.0
    assert distribution[2]['duration_seconds'] == 7200.0


def test_get_application_funnel(analytics_service, mock_db):
    """Test getting application funnel."""
    mock_db.conn.cursor.return_value.fetchall.return_value = [
        {'status': 'New', 'count': 10},
        {'status': 'Applied', 'count': 5},
        {'status': 'Interview', 'count': 2},
    ]
    
    funnel = analytics_service.get_application_funnel()
    
    assert funnel['status_counts']['New'] == 10
    assert funnel['status_counts']['Applied'] == 5
    assert funnel['status_counts']['Interview'] == 2
    assert funnel['total'] == 17
    assert 'conversion_rates' in funnel
