"""Tests for Google Sheets sync API endpoints."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database."""
    db = Mock()
    db.get_all_jobs.return_value = []
    return db


@pytest.fixture
def sample_sync_request():
    """Sample sync request."""
    return {
        "credentials_path": "/path/to/credentials.json",
        "spreadsheet_url": "https://docs.google.com/spreadsheets/d/123456789/edit",
        "sheet_name": "Sheet1"
    }


def test_sync_dry_run_success(client, sample_sync_request, mock_db):
    """Test dry run sync success."""
    with patch('backend.app.api.v1.google_sheets.get_db', return_value=mock_db), \
         patch('backend.app.api.v1.google_sheets.GoogleSheetsClient') as mock_client_class, \
         patch('backend.app.api.v1.google_sheets.SheetSyncService') as mock_service_class:
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_service = Mock()
        mock_service.sync_from_sheet.return_value = {
            'added': 5,
            'updated': 2,
            'errors': 0,
            'error_details': [],
            'sheet_name': 'Sheet1'
        }
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/v1/google-sheets/sync/dry-run", json=sample_sync_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data['added'] == 5
        assert data['updated'] == 2
        assert data['errors'] == 0
        assert data['sheet_name'] == 'Sheet1'
        mock_service.sync_from_sheet.assert_called_once_with(sheet_name='Sheet1', dry_run=True)


def test_sync_dry_run_invalid_url(client, mock_db):
    """Test dry run sync with invalid URL."""
    request_data = {
        "credentials_path": "/path/to/credentials.json",
        "spreadsheet_url": "invalid-url",
        "sheet_name": "Sheet1"
    }
    
    with patch('backend.app.api.v1.google_sheets.get_db', return_value=mock_db):
        response = client.post("/api/v1/google-sheets/sync/dry-run", json=request_data)
        
        assert response.status_code == 500
        detail = response.json()['detail']
        assert "Could not extract spreadsheet ID" in detail or "Credentials file not found" in detail


def test_sync_dry_run_spreadsheet_id_only(client, sample_sync_request, mock_db):
    """Test dry run sync with spreadsheet ID only."""
    request_data = {
        "credentials_path": "/path/to/credentials.json",
        "spreadsheet_url": "12345678901234567890",
        "sheet_name": "Sheet1"
    }
    
    with patch('backend.app.api.v1.google_sheets.get_db', return_value=mock_db), \
         patch('backend.app.api.v1.google_sheets.GoogleSheetsClient') as mock_client_class, \
         patch('backend.app.api.v1.google_sheets.SheetSyncService') as mock_service_class:
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_service = Mock()
        mock_service.sync_from_sheet.return_value = {
            'added': 0,
            'updated': 0,
            'errors': 0,
            'error_details': [],
            'sheet_name': 'Sheet1'
        }
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/v1/google-sheets/sync/dry-run", json=request_data)
        
        assert response.status_code == 200


def test_sync_dry_run_missing_dependencies(client, sample_sync_request, mock_db):
    """Test dry run sync when dependencies are missing."""
    with patch('backend.app.api.v1.google_sheets.get_db', return_value=mock_db), \
         patch('backend.app.api.v1.google_sheets.GoogleSheetsClient', side_effect=ImportError("No module named 'gspread'")):
        
        response = client.post("/api/v1/google-sheets/sync/dry-run", json=sample_sync_request)
        
        assert response.status_code == 500
        assert "Google Sheets dependencies not installed" in response.json()['detail']


def test_sync_success(client, sample_sync_request, mock_db):
    """Test sync success."""
    with patch('backend.app.api.v1.google_sheets.get_db', return_value=mock_db), \
         patch('backend.app.api.v1.google_sheets.GoogleSheetsClient') as mock_client_class, \
         patch('backend.app.api.v1.google_sheets.SheetSyncService') as mock_service_class:
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_service = Mock()
        mock_service.sync_from_sheet.return_value = {
            'added': 3,
            'updated': 1,
            'errors': 0,
            'error_details': [],
            'sheet_name': 'Sheet1'
        }
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/v1/google-sheets/sync", json=sample_sync_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data['added'] == 3
        assert data['updated'] == 1
        assert data['errors'] == 0
        mock_service.sync_from_sheet.assert_called_once_with(sheet_name='Sheet1', dry_run=False)


def test_sync_with_errors(client, sample_sync_request, mock_db):
    """Test sync with errors."""
    with patch('backend.app.api.v1.google_sheets.get_db', return_value=mock_db), \
         patch('backend.app.api.v1.google_sheets.GoogleSheetsClient') as mock_client_class, \
         patch('backend.app.api.v1.google_sheets.SheetSyncService') as mock_service_class:
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_service = Mock()
        mock_service.sync_from_sheet.return_value = {
            'added': 2,
            'updated': 1,
            'errors': 1,
            'error_details': ['Row 5: Invalid data'],
            'sheet_name': 'Sheet1'
        }
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/v1/google-sheets/sync", json=sample_sync_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data['errors'] == 1
        assert len(data['error_details']) == 1
        assert 'Row 5' in data['error_details'][0]


def test_push_to_sheets_success(client, sample_sync_request, mock_db):
    """Test push to sheets success."""
    with patch('backend.app.api.v1.google_sheets.get_db', return_value=mock_db), \
         patch('backend.app.api.v1.google_sheets.GoogleSheetsClient') as mock_client_class, \
         patch('backend.app.api.v1.google_sheets.SheetSyncService') as mock_service_class:
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_service = Mock()
        mock_service.push_to_sheet.return_value = {
            'created': 10,
            'updated': 5,
            'errors': 0,
            'error_details': []
        }
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/v1/google-sheets/push", json=sample_sync_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data['created'] == 10
        assert data['updated'] == 5
        assert data['errors'] == 0
        assert data['sheet_name'] == 'Sheet1'
        mock_service.push_to_sheet.assert_called_once_with(sheet_name='Sheet1')


def test_push_to_sheets_default_sheet_name(client, mock_db):
    """Test push to sheets with default sheet name."""
    request_data = {
        "credentials_path": "/path/to/credentials.json",
        "spreadsheet_url": "https://docs.google.com/spreadsheets/d/123456789/edit"
    }
    
    with patch('backend.app.api.v1.google_sheets.get_db', return_value=mock_db), \
         patch('backend.app.api.v1.google_sheets.GoogleSheetsClient') as mock_client_class, \
         patch('backend.app.api.v1.google_sheets.SheetSyncService') as mock_service_class:
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_service = Mock()
        mock_service.push_to_sheet.return_value = {
            'created': 0,
            'updated': 0,
            'errors': 0,
            'error_details': []
        }
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/v1/google-sheets/push", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['sheet_name'] == 'Sheet1'
        mock_service.push_to_sheet.assert_called_once_with(sheet_name='Sheet1')


def test_extract_spreadsheet_id_from_url():
    """Test spreadsheet ID extraction from URL."""
    from backend.app.api.v1.google_sheets import _extract_spreadsheet_id
    
    url = "https://docs.google.com/spreadsheets/d/123456789/edit"
    assert _extract_spreadsheet_id(url) == "123456789"
    
    url_with_gid = "https://docs.google.com/spreadsheets/d/123456789/edit#gid=193258797"
    assert _extract_spreadsheet_id(url_with_gid) == "123456789"
    
    direct_id = "12345678901234567890"
    assert _extract_spreadsheet_id(direct_id) == direct_id


def test_extract_spreadsheet_id_invalid():
    """Test spreadsheet ID extraction with invalid URL."""
    from backend.app.api.v1.google_sheets import _extract_spreadsheet_id
    
    with pytest.raises(ValueError):
        _extract_spreadsheet_id("http://example.com/not-a-sheet")
    
    with pytest.raises(ValueError):
        _extract_spreadsheet_id("short")
    
    with pytest.raises(ValueError):
        _extract_spreadsheet_id("")
