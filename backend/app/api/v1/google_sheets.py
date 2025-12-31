"""Google Sheets sync API routes."""

import re
import sys
from pathlib import Path
from typing import Optional, List

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.app.dependencies import get_db
from src.db.database import Database
from src.sync.google_sheets_client import GoogleSheetsClient
from src.sync.sheet_sync import SheetSyncService

router = APIRouter()


class GoogleSheetsSyncRequest(BaseModel):
    """Request model for Google Sheets sync."""
    credentials_path: str
    spreadsheet_url: str
    sheet_name: Optional[str] = None


class GoogleSheetsSyncResponse(BaseModel):
    """Response model for Google Sheets sync."""
    added: Optional[int] = None
    updated: Optional[int] = None
    created: Optional[int] = None
    errors: Optional[int] = None
    error_details: Optional[List[str]] = None
    sheet_name: Optional[str] = None


def _extract_spreadsheet_id(url: str) -> str:
    """Extract spreadsheet ID from URL."""
    if not url or len(url.strip()) == 0:
        raise ValueError("Could not extract spreadsheet ID from URL: empty string")
    
    spreadsheet_id_match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    if spreadsheet_id_match:
        return spreadsheet_id_match.group(1)
    if '/' not in url and len(url) > 10:
        return url
    raise ValueError(f"Could not extract spreadsheet ID from URL: {url}")


@router.post("/google-sheets/sync/dry-run", response_model=GoogleSheetsSyncResponse)
async def sync_dry_run(request: GoogleSheetsSyncRequest, db: Database = Depends(get_db)):
    """Dry run sync from Google Sheets (no changes made)."""
    try:
        spreadsheet_id = _extract_spreadsheet_id(request.spreadsheet_url)
        client = GoogleSheetsClient(request.credentials_path, spreadsheet_id)
        sync_service = SheetSyncService(db, client)
        result = sync_service.sync_from_sheet(sheet_name=request.sheet_name, dry_run=True)
        
        return GoogleSheetsSyncResponse(
            added=result.get('added', 0),
            updated=result.get('updated', 0),
            errors=result.get('errors', 0),
            error_details=result.get('error_details', []),
            sheet_name=result.get('sheet_name'),
        )
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Google Sheets dependencies not installed: {e}. Install with: pip install gspread google-auth"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/google-sheets/sync", response_model=GoogleSheetsSyncResponse)
async def sync_from_sheets(request: GoogleSheetsSyncRequest, db: Database = Depends(get_db)):
    """Sync jobs from Google Sheets to database."""
    try:
        spreadsheet_id = _extract_spreadsheet_id(request.spreadsheet_url)
        client = GoogleSheetsClient(request.credentials_path, spreadsheet_id)
        sync_service = SheetSyncService(db, client)
        result = sync_service.sync_from_sheet(sheet_name=request.sheet_name, dry_run=False)
        
        return GoogleSheetsSyncResponse(
            added=result.get('added', 0),
            updated=result.get('updated', 0),
            errors=result.get('errors', 0),
            error_details=result.get('error_details', []),
            sheet_name=result.get('sheet_name'),
        )
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Google Sheets dependencies not installed: {e}. Install with: pip install gspread google-auth"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/google-sheets/push", response_model=GoogleSheetsSyncResponse)
async def push_to_sheets(request: GoogleSheetsSyncRequest, db: Database = Depends(get_db)):
    """Push jobs from database to Google Sheets."""
    try:
        spreadsheet_id = _extract_spreadsheet_id(request.spreadsheet_url)
        client = GoogleSheetsClient(request.credentials_path, spreadsheet_id)
        sync_service = SheetSyncService(db, client)
        sheet_name = request.sheet_name or "Sheet1"
        result = sync_service.push_to_sheet(sheet_name=sheet_name)
        
        return GoogleSheetsSyncResponse(
            created=result.get('created', 0),
            updated=result.get('updated', 0),
            errors=result.get('errors', 0),
            error_details=result.get('error_details', []),
            sheet_name=sheet_name,
        )
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Google Sheets dependencies not installed: {e}. Install with: pip install gspread google-auth"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
