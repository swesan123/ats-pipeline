"""Tests for analytics API endpoints."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.dependencies import get_db
from src.db.database import Database


@pytest.fixture
def mock_db():
    """Create mock database."""
    db = Mock(spec=Database)
    db.conn = Mock()
    cursor_mock = Mock()
    cursor_mock.execute.return_value = None
    cursor_mock.fetchall.return_value = []
    cursor_mock.fetchone.return_value = None
    db.conn.cursor.return_value = cursor_mock
    return db


@pytest.fixture
def client(mock_db):
    """Create test client with mocked database."""
    app.dependency_overrides[get_db] = lambda: mock_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_get_metrics(client, mock_db):
    """Test getting key metrics."""
    with patch('backend.app.api.v1.analytics.AnalyticsService') as mock_service_class:
        mock_service = Mock()
        mock_service.get_key_metrics.return_value = {
            'total_jobs': 10,
            'applications_submitted': 5,
            'average_time_to_apply_seconds': 3600,
            'resume_generation_count': 3,
            'bullet_approval_rate': 0.85,
        }
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/v1/analytics/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data['total_jobs'] == 10
        assert data['applications_submitted'] == 5


def test_get_skill_gaps(client, mock_db):
    """Test getting skill gaps."""
    with patch('backend.app.api.v1.analytics.AnalyticsService') as mock_service_class:
        mock_service = Mock()
        mock_service.get_missing_skills_ranked.return_value = [
            {
                'skill_name': 'Python',
                'priority_score': 0.9,
                'frequency_count': 5,
                'required_count': 3,
                'preferred_count': 2,
                'general_count': 0,
                'resume_coverage': 'none',
                'is_generic': False,
            }
        ]
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/v1/analytics/skills")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['skill_name'] == 'Python'


def test_get_skill_gaps_with_params(client, mock_db):
    """Test getting skill gaps with limit and sort parameters."""
    with patch('backend.app.api.v1.analytics.AnalyticsService') as mock_service_class:
        mock_service = Mock()
        mock_service.get_missing_skills_ranked.return_value = []
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/v1/analytics/skills?limit=50&by=frequency")
        assert response.status_code == 200
        mock_service.get_missing_skills_ranked.assert_called_once_with(limit=50, by='frequency')


def test_get_timeline(client, mock_db):
    """Test getting timeline events."""
    with patch('backend.app.api.v1.analytics.AnalyticsService') as mock_service_class:
        mock_service = Mock()
        mock_service.get_application_timeline.return_value = [
            {
                'date': '2024-01-01',
                'event_type': 'job_added',
                'description': 'Added new job',
                'metadata': None,
            }
        ]
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/v1/analytics/timeline")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['event_type'] == 'job_added'


def test_get_timeline_with_days(client, mock_db):
    """Test getting timeline events with custom days parameter."""
    with patch('backend.app.api.v1.analytics.AnalyticsService') as mock_service_class:
        mock_service = Mock()
        mock_service.get_application_timeline.return_value = []
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/v1/analytics/timeline?days=60")
        assert response.status_code == 200
        mock_service.get_application_timeline.assert_called_once_with(days=60)


def test_get_time_to_apply_stats(client, mock_db):
    """Test getting time-to-apply statistics."""
    with patch('backend.app.api.v1.analytics.AnalyticsService') as mock_service_class:
        mock_service = Mock()
        mock_service.get_time_to_apply_stats.return_value = {
            'count': 5,
            'average_seconds': 3600.0,
            'median_seconds': 3000.0,
            'min_seconds': 1800.0,
            'max_seconds': 7200.0,
        }
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/v1/analytics/time-to-apply-stats")
        assert response.status_code == 200
        data = response.json()
        assert data['count'] == 5
        assert data['average_seconds'] == 3600.0


def test_get_time_to_apply_distribution(client, mock_db):
    """Test getting time-to-apply distribution."""
    with patch('backend.app.api.v1.analytics.AnalyticsService') as mock_service_class:
        mock_service = Mock()
        mock_service.get_time_to_apply_distribution.return_value = [
            {'duration_seconds': 1800.0},
            {'duration_seconds': 3600.0},
            {'duration_seconds': 7200.0},
        ]
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/v1/analytics/time-to-apply-distribution")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]['duration_seconds'] == 1800.0


def test_get_application_funnel(client, mock_db):
    """Test getting application funnel data."""
    with patch('backend.app.api.v1.analytics.AnalyticsService') as mock_service_class:
        mock_service = Mock()
        mock_service.get_application_funnel.return_value = {
            'status_counts': {'New': 10, 'Applied': 5, 'Interview': 2},
            'conversion_rates': {'new_to_interested': 0.5},
            'total': 17,
        }
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/v1/analytics/application-funnel")
        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 17
        assert 'status_counts' in data
        assert 'conversion_rates' in data


def test_get_missing_skills_analysis(client, mock_db):
    """Test getting missing skills analysis."""
    with patch('backend.app.api.v1.analytics.AnalyticsService') as mock_service_class:
        mock_service = Mock()
        mock_service.get_missing_skills_by_category.return_value = {
            'Languages': [
                {'skill_name': 'Python', 'priority_score': 0.9},
            ],
            'Backend/DB': [
                {'skill_name': 'PostgreSQL', 'priority_score': 0.8},
            ],
        }
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/v1/analytics/missing-skills-analysis")
        assert response.status_code == 200
        data = response.json()
        assert 'Languages' in data
        assert 'Backend/DB' in data


def test_get_recent_activity(client, mock_db):
    """Test getting recent activity."""
    with patch('backend.app.api.v1.analytics.AnalyticsService') as mock_service_class:
        mock_service = Mock()
        mock_service.get_application_timeline.return_value = [
            {
                'date': '2024-01-01',
                'event_type': 'job_added',
                'description': 'Job added',
                'metadata': {'job_id': 1},
            },
            {
                'date': '2024-01-02',
                'event_type': 'resume_generated',
                'description': 'Resume generated',
                'metadata': None,
            },
        ]
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/v1/analytics/recent-activity")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]['event_type'] == 'job_added'
