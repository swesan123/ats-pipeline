"""Service for syncing Google Sheets data to database."""

from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from src.db.database import Database
from src.models.job import JobPosting
from src.sync.google_sheets_client import GoogleSheetsClient


class SheetSyncService:
    """Service for syncing jobs from Google Sheets to database."""
    
    def __init__(self, db: Database, sheets_client: GoogleSheetsClient):
        """Initialize sync service.
        
        Args:
            db: Database instance
            sheets_client: Google Sheets client instance
        """
        self.db = db
        self.client = sheets_client
    
    def sync_from_sheet(self, sheet_name: Optional[str] = None, dry_run: bool = False) -> Dict[str, int]:
        """Sync jobs from Google Sheet to database.
        
        Column mapping:
        - Company Name → company
        - Job Title → title
        - Job Link / Source → source_url
        - Location → location
        - Date Added → created_at
        - Date Applied → (store in applications table)
        - Status → status (direct mapping)
        - Notes → notes
        - Job Description → description
        - Contact Name → (store in contacts table)
        - Contact Info → (store in contacts table)
        - Interview Date(s) → (store in applications table)
        - Offer / Outcome → status (map to "Offer", "Rejected", etc.)
        
        Args:
            sheet_name: Name of the sheet to sync from (if None, auto-detects)
            dry_run: If True, don't make changes, just return what would be done
            
        Returns:
            Dictionary with counts: {'added': int, 'updated': int, 'errors': int, 'sheet_name': str}
        """
        # Auto-detect sheet if not provided
        if sheet_name is None:
            detected_sheet = self.client.find_sheet_with_columns()
            if detected_sheet is None:
                # List available sheets for better error message
                try:
                    worksheets = self.client.spreadsheet.worksheets()
                    sheet_names = [ws.title for ws in worksheets]
                    raise ValueError(
                        f"No sheet found with required columns (Company Name, Job Title). "
                        f"Available sheets: {', '.join(sheet_names) if sheet_names else 'None'}"
                    )
                except Exception:
                    raise ValueError("No sheet found with required columns (Company Name, Job Title)")
            sheet_name = detected_sheet
        
        # Get jobs from the sheet
        rows = self.client.get_jobs_from_sheet(sheet_name)
        
        stats = {'added': 0, 'updated': 0, 'errors': 0, 'sheet_name': sheet_name, 'error_details': []}
        
        for idx, row in enumerate(rows, start=2):  # Start at 2 because row 1 is headers
            try:
                # Skip empty rows
                if not row or (not row.get('Company Name') and not row.get('Company') and not row.get('company_name') and not row.get('company')):
                    continue
                
                # Check if job already exists (by company + title or source_url)
                existing_job = self._find_existing_job(row)
                
                if existing_job:
                    if not dry_run:
                        self._update_job_from_sheet(existing_job['id'], row)
                    stats['updated'] += 1
                else:
                    if not dry_run:
                        self._create_job_from_sheet(row)
                    stats['added'] += 1
            except Exception as e:
                stats['errors'] += 1
                error_msg = f"Row {idx}: {str(e)}"
                stats['error_details'].append(error_msg)
                if not dry_run:
                    print(f"Error processing row {idx}: {e}")
                import traceback
                if not dry_run:
                    traceback.print_exc()
        
        return stats
    
    def _map_sheet_row_to_job(self, row: Dict[str, str]) -> JobPosting:
        """Convert sheet row to JobPosting model.
        
        Args:
            row: Dictionary with sheet column values
            
        Returns:
            JobPosting model
        """
        # Parse date added
        date_added = None
        if row.get('Date Added'):
            try:
                # Try parsing various date formats
                date_str = row['Date Added']
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        date_added = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
            except Exception:
                pass
        
        # Map status - prefer "Status" column, then "Offer / Outcome", then "Interested"
        status = 'New'
        if row.get('Status'):
            # Use Status column directly if available
            status_val = row.get('Status', '').strip()
            if status_val:
                status = status_val
        elif row.get('Offer / Outcome'):
            outcome = row['Offer / Outcome'].lower()
            if 'offer' in outcome:
                status = 'Offer'
            elif 'reject' in outcome:
                status = 'Rejected'
            elif 'interview' in outcome:
                status = 'Interview'
            elif 'withdraw' in outcome:
                status = 'Withdrawn'
            else:
                status = outcome.title()  # Use as-is, capitalized
        elif row.get('Interested', '').lower() in ['yes', 'y', 'true', '1']:
            status = 'Interested'
        
        # Get description - prefer Job Description, then Job Description Link, fallback to Notes
        description = row.get('Job Description', '') or row.get('Job Description Link', '') or row.get('Notes', '')
        if not description:
            description = f"Job posting for {row.get('Job Title', 'Unknown')} at {row.get('Company Name', 'Unknown')}"
        
        job = JobPosting(
            company=row.get('Company Name', '').strip(),
            title=row.get('Job Title', '').strip(),
            location=row.get('Location', '').strip() or None,
            description=description,
            source_url=row.get('Job Link / Source', '').strip() or None,
            date_posted=date_added,
        )
        
        return job
    
    def _find_existing_job(self, row: Dict[str, str]) -> Optional[Dict]:
        """Match sheet row to existing DB job.
        
        Args:
            row: Dictionary with sheet column values
            
        Returns:
            Dictionary with job data if found, None otherwise
        """
        company = row.get('Company Name', '').strip()
        title = row.get('Job Title', '').strip()
        source_url = row.get('Job Link / Source', '').strip()
        
        # Try to find by company + title
        all_jobs = self.db.get_all_jobs()
        for job in all_jobs:
            # get_all_jobs() returns dictionaries
            job_company = job.get('company', '').strip() if job.get('company') else ''
            job_title = job.get('title', '').strip() if job.get('title') else ''
            job_id = job.get('id')
            
            if (job_company and job_title and 
                job_company.lower() == company.lower() and 
                job_title.lower() == title.lower()):
                return {'id': job_id, 'job': job}
        
        # Try to find by source_url if available
        if source_url:
            for job in all_jobs:
                job_source_url = job.get('source_url', '').strip() if job.get('source_url') else ''
                job_id = job.get('id')
                
                if job_source_url and job_source_url == source_url:
                    return {'id': job_id, 'job': job}
        
        return None
    
    def _update_job_from_sheet(self, job_id: int, row: Dict[str, str]):
        """Update existing job with sheet data.
        
        Args:
            job_id: Database job ID
            row: Dictionary with sheet column values
        """
        # Map status - prefer "Status" column, then "Offer / Outcome", then "Interested"
        status = 'New'
        if row.get('Status'):
            # Use Status column directly if available
            status_val = row.get('Status', '').strip()
            if status_val:
                status = status_val
        elif row.get('Offer / Outcome'):
            outcome = row['Offer / Outcome'].lower()
            if 'offer' in outcome:
                status = 'Offer'
            elif 'reject' in outcome:
                status = 'Rejected'
            elif 'interview' in outcome:
                status = 'Interview'
            elif 'withdraw' in outcome:
                status = 'Withdrawn'
            else:
                status = outcome.title()
        elif row.get('Interested', '').lower() in ['yes', 'y', 'true', '1']:
            status = 'Interested'
        
        # Update job status
        self.db.update_job_status(job_id, status)
        
        # Update or create contact
        if row.get('Contact Name') or row.get('Contact Info'):
            self._save_contact(job_id, row)
        
        # Update or create application record
        if row.get('Date Applied') or row.get('Interview Date(s)'):
            self._save_application(job_id, row)
    
    def _create_job_from_sheet(self, row: Dict[str, str]):
        """Create new job from sheet data.
        
        Args:
            row: Dictionary with sheet column values
        """
        job = self._map_sheet_row_to_job(row)
        
        # Determine status - prefer "Status" column, then "Offer / Outcome", then "Interested"
        status = 'New'
        if row.get('Status'):
            # Use Status column directly if available
            status_val = row.get('Status', '').strip()
            if status_val:
                status = status_val
        elif row.get('Offer / Outcome'):
            outcome = row['Offer / Outcome'].lower()
            if 'offer' in outcome:
                status = 'Offer'
            elif 'reject' in outcome:
                status = 'Rejected'
            elif 'interview' in outcome:
                status = 'Interview'
            elif 'withdraw' in outcome:
                status = 'Withdrawn'
            else:
                status = outcome.title()
        elif row.get('Interested', '').lower() in ['yes', 'y', 'true', '1']:
            status = 'Interested'
        
        # Save job to database with status
        job_id = self.db.save_job(job, status=status)
        
        # Save contact if provided
        if row.get('Contact Name') or row.get('Contact Info'):
            self._save_contact(job_id, row)
        
        # Save application if date applied provided
        if row.get('Date Applied') or row.get('Interview Date(s)'):
            self._save_application(job_id, row)
    
    def _save_contact(self, job_id: int, row: Dict[str, str]):
        """Save contact information to contacts table.
        
        Args:
            job_id: Database job ID
            row: Dictionary with sheet column values
        """
        contact_name = row.get('Contact Name', '').strip()
        contact_info = row.get('Contact Info', '').strip()
        
        if not contact_name and not contact_info:
            return
        
        # Parse contact info (could be email, phone, LinkedIn, etc.)
        email = None
        phone = None
        linkedin = None
        
        if contact_info:
            # Simple parsing - could be enhanced
            if '@' in contact_info:
                email = contact_info
            elif any(char.isdigit() for char in contact_info):
                phone = contact_info
            elif 'linkedin.com' in contact_info.lower():
                linkedin = contact_info
        
        # Check if contact already exists
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id FROM contacts WHERE job_id = ?
        """, (job_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing contact
            cursor.execute("""
                UPDATE contacts 
                SET name = ?, email = ?, phone = ?, linkedin = ?, notes = ?
                WHERE job_id = ?
            """, (contact_name or None, email, phone, linkedin, row.get('Notes'), job_id))
        else:
            # Create new contact
            cursor.execute("""
                INSERT INTO contacts (job_id, name, email, phone, linkedin, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (job_id, contact_name or None, email, phone, linkedin, row.get('Notes')))
        
        self.db.conn.commit()
    
    def _save_application(self, job_id: int, row: Dict[str, str]):
        """Save application information to applications table.
        
        Args:
            job_id: Database job ID
            row: Dictionary with sheet column values
        """
        # Parse date applied
        applied_at = None
        if row.get('Date Applied'):
            try:
                date_str = row['Date Applied']
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        applied_at = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
            except Exception:
                pass
        
        # Determine status
        status = 'pending'
        if row.get('Offer / Outcome'):
            outcome = row['Offer / Outcome'].lower()
            if 'offer' in outcome:
                status = 'offer'
            elif 'reject' in outcome:
                status = 'rejected'
            elif 'interview' in outcome:
                status = 'interview'
            elif 'withdraw' in outcome:
                status = 'withdrawn'
        
        # Check if application already exists
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id FROM applications WHERE job_id = ?
        """, (job_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing application
            cursor.execute("""
                UPDATE applications 
                SET status = ?, applied_at = ?, notes = ?
                WHERE job_id = ?
            """, (status, applied_at, row.get('Notes'), job_id))
        else:
            # Create new application
            cursor.execute("""
                INSERT INTO applications (job_id, status, applied_at, notes)
                VALUES (?, ?, ?, ?)
            """, (job_id, status, applied_at, row.get('Notes')))
        
        self.db.conn.commit()

