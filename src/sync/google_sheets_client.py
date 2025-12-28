"""Google Sheets API client for reading job data."""

import json
from typing import List, Dict, Optional
from pathlib import Path

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False


class GoogleSheetsClient:
    """Client for reading data from Google Sheets."""
    
    def __init__(self, credentials_path: str, spreadsheet_id: str):
        """Initialize Google Sheets client.
        
        Args:
            credentials_path: Path to Google service account JSON credentials
            spreadsheet_id: Google Sheets spreadsheet ID
        """
        if not GSPREAD_AVAILABLE:
            raise ImportError(
                "gspread and google-auth are required for Google Sheets sync. "
                "Install with: pip install gspread google-auth"
            )
        
        credentials_path = Path(credentials_path)
        if not credentials_path.exists():
            raise FileNotFoundError(f"Credentials file not found: {credentials_path}")
        
        # Authenticate with service account
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_file(
            str(credentials_path),
            scopes=scope
        )
        
        self.client = gspread.authorize(creds)
        self.spreadsheet_id = spreadsheet_id
        self.spreadsheet = self.client.open_by_key(spreadsheet_id)
    
    def read_sheet(self, sheet_name: str = "Sheet1") -> List[Dict[str, str]]:
        """Read all rows from sheet as dictionaries.
        
        Args:
            sheet_name: Name of the sheet to read
            
        Returns:
            List of dictionaries, one per row, with column headers as keys
        """
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            records = worksheet.get_all_records()
            return records
        except gspread.exceptions.WorksheetNotFound:
            raise ValueError(f"Sheet '{sheet_name}' not found in spreadsheet")
        except Exception as e:
            raise RuntimeError(f"Error reading sheet: {e}")
    
    def find_sheet_with_columns(self) -> Optional[str]:
        """Find the first sheet that has the required columns.
        
        Returns:
            Name of the sheet with required columns, or None if not found
        """
        try:
            worksheets = self.spreadsheet.worksheets()
            if not worksheets:
                return None
            
            for worksheet in worksheets:
                try:
                    # Get first row (headers)
                    headers = worksheet.row_values(1)
                    if not headers:
                        continue
                    
                    headers_lower = [str(h).lower().strip() if h else '' for h in headers]
                    
                    # Check if we have at least Company Name and Job Title (case-insensitive)
                    company_variations = ['company name', 'company', 'company_name']
                    title_variations = ['job title', 'title', 'job_title']
                    
                    has_company = any(variation in headers_lower for variation in company_variations)
                    has_title = any(variation in headers_lower for variation in title_variations)
                    
                    if has_company and has_title:
                        return worksheet.title
                except Exception:
                    # Skip sheets that can't be read
                    continue
            
            return None
        except Exception as e:
            raise RuntimeError(f"Error finding sheet with required columns: {e}")
    
    def get_jobs_from_sheet(self, sheet_name: Optional[str] = None) -> List[Dict[str, str]]:
        """Parse sheet rows into job format matching database schema.
        
        Expected columns:
        - Company Name
        - Job Title
        - Job Link / Source
        - Location
        - Date Added
        - Date Applied
        - Status
        - Notes
        - Job Description
        - Contact Name
        - Contact Info
        - Interview Date(s)
        - Offer / Outcome
        
        Args:
            sheet_name: Name of the sheet to read (if None, auto-detects)
            
        Returns:
            List of job dictionaries with standardized keys
        """
        # Auto-detect sheet if not provided
        if sheet_name is None:
            sheet_name = self.find_sheet_with_columns()
            if sheet_name is None:
                # List available sheets for better error message
                try:
                    worksheets = self.spreadsheet.worksheets()
                    sheet_names = [ws.title for ws in worksheets]
                    raise ValueError(
                        f"No sheet found with required columns (Company Name, Job Title). "
                        f"Available sheets: {', '.join(sheet_names) if sheet_names else 'None'}"
                    )
                except Exception:
                    raise ValueError("No sheet found with required columns (Company Name, Job Title)")
        
        if not sheet_name:
            raise ValueError("Sheet name cannot be empty")
        
        rows = self.read_sheet(sheet_name)
        
        # Map column names (handle variations)
        column_mapping = {
            'Company Name': ['Company Name', 'Company', 'company_name', 'company'],
            'Job Title': ['Job Title', 'Title', 'job_title', 'title'],
            'Job Link / Source': ['Job Link / Source', 'Job Link', 'Source', 'URL', 'Link', 'job_link', 'source_url'],
            'Location': ['Location', 'location'],
            'Date Added': ['Date Added', 'Added', 'date_added', 'created_at'],
            'Date Applied': ['Date Applied', 'Applied', 'date_applied', 'applied_at'],
            'Status': ['Status', 'status'],
            'Interested': ['Interested', 'interested'],
            'Notes': ['Notes', 'notes'],
            'Job Description': ['Job Description', 'Job Description Link', 'Description Link', 'Description', 'job_description', 'job_description_link'],
            'Contact Name': ['Contact Name', 'Contact', 'contact_name', 'name'],
            'Contact Info': ['Contact Info', 'Contact Information', 'contact_info', 'email', 'phone'],
            'Interview Date(s)': ['Interview Date(s)', 'Interview Date', 'Interview', 'interview_date'],
            'Offer / Outcome': ['Offer / Outcome', 'Outcome', 'Offer', 'offer', 'outcome'],
        }
        
        jobs = []
        for row in rows:
            if not row:  # Skip empty rows
                continue
            
            # Find matching columns (case-insensitive)
            job_data = {}
            for standard_key, possible_keys in column_mapping.items():
                for key in possible_keys:
                    # Check both exact match and case-insensitive match
                    row_keys_lower = {k.lower().strip() if k else '' for k in row.keys()}
                    key_lower = key.lower().strip()
                    if key in row or key_lower in row_keys_lower:
                        # Find the actual key in row (case-insensitive)
                        actual_key = key if key in row else next((k for k in row.keys() if k.lower().strip() == key_lower), None)
                        if actual_key and row[actual_key]:
                            job_data[standard_key] = row[actual_key]
                            break
            
            # Only add if we have at least company and title
            company = job_data.get('Company Name', '').strip() if job_data.get('Company Name') else ''
            title = job_data.get('Job Title', '').strip() if job_data.get('Job Title') else ''
            
            if company and title:
                jobs.append(job_data)
        
        return jobs

