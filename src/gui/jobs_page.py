"""Jobs page component with job list, add job, and Google Sheets sync."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import re
from src.db.database import Database
from src.gui.job_list import render_job_list
from src.gui.job_input import render_job_input


def render_jobs_page(db: Database):
    """Render the jobs page with job list, add job, and sync."""
    # Clear any previous column context by using a fresh container
    # This prevents column context leakage from other pages
    page_wrapper = st.container()
    with page_wrapper:
        # Two-column layout - ensure proper scoping
        left_col, right_col = st.columns([1, 2])
        
        # Left column: Add Job and Google Sheets Sync
        with left_col:
            st.header("Add Job")
            render_job_input(db)
        
        st.divider()
        
        # Google Sheets Sync
        st.header("Google Sheets Sync")
        with st.expander("Sync from Google Sheets", expanded=False):
            st.write("**Sync (Dry Run)**: Preview what would be synced without making any changes to the database.")
            st.write("**Sync (Apply)**: Actually sync the data from Google Sheets to the database.")
            st.write("")
            
            # Initialize session state for persistent values
            if 'gs_credentials_path' not in st.session_state:
                st.session_state.gs_credentials_path = ""
            if 'gs_spreadsheet_url' not in st.session_state:
                st.session_state.gs_spreadsheet_url = ""
            
            credentials_path = st.text_input(
                "Credentials Path",
                value=st.session_state.gs_credentials_path,
                help="Path to Google service account JSON file",
                key="gs_credentials"
            )
            # Update session state
            if credentials_path != st.session_state.gs_credentials_path:
                st.session_state.gs_credentials_path = credentials_path
            
            spreadsheet_url = st.text_input(
                "Spreadsheet Link",
                value=st.session_state.gs_spreadsheet_url,
                help="Full Google Sheets URL (e.g., https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit)",
                key="gs_spreadsheet_url"
            )
            # Update session state
            if spreadsheet_url != st.session_state.gs_spreadsheet_url:
                st.session_state.gs_spreadsheet_url = spreadsheet_url
            
            # Extract spreadsheet ID from URL
            spreadsheet_id = None
            if spreadsheet_url:
                match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', spreadsheet_url)
                if match:
                    spreadsheet_id = match.group(1)
                else:
                    # If it's just an ID, use it directly
                    if '/' not in spreadsheet_url and len(spreadsheet_url) > 10:
                        spreadsheet_id = spreadsheet_url
                    else:
                        st.warning("Could not extract spreadsheet ID from URL. Please provide the full URL or just the ID.")
            
            sync_btn_col1, sync_btn_col2 = st.columns(2)
            with sync_btn_col1:
                if st.button("Sync (Dry Run)", help="Preview changes without applying", key="gs_dry_run"):
                    if credentials_path and spreadsheet_id:
                        try:
                            from src.sync.google_sheets_client import GoogleSheetsClient
                            from src.sync.sheet_sync import SheetSyncService
                            
                            client = GoogleSheetsClient(credentials_path, spreadsheet_id)
                            sync_service = SheetSyncService(db, client)
                            stats = sync_service.sync_from_sheet(sheet_name=None, dry_run=True)
                            
                            st.success(f"Dry run complete!")
                            st.write(f"**Sheet used:** {stats.get('sheet_name', 'Unknown')}")
                            st.write(f"- Would add: {stats['added']} jobs")
                            st.write(f"- Would update: {stats['updated']} jobs")
                            st.write(f"- Errors: {stats['errors']}")
                            
                            if stats.get('error_details'):
                                with st.expander("Error Details", expanded=True):
                                    for error in stats['error_details'][:20]:
                                        st.error(error)
                                    if len(stats['error_details']) > 20:
                                        st.write(f"... and {len(stats['error_details']) - 20} more errors")
                        except Exception as e:
                            st.error(f"Error: {e}")
                            import traceback
                            st.exception(e)
                    else:
                        st.warning("Please provide credentials path and spreadsheet link")
            
            with sync_btn_col2:
                if st.button("Sync (Apply)", type="primary", help="Sync and apply changes", key="gs_apply"):
                    if credentials_path and spreadsheet_id:
                        try:
                            from src.sync.google_sheets_client import GoogleSheetsClient
                            from src.sync.sheet_sync import SheetSyncService
                            
                            with st.spinner("Syncing from Google Sheets..."):
                                client = GoogleSheetsClient(credentials_path, spreadsheet_id)
                                sync_service = SheetSyncService(db, client)
                                stats = sync_service.sync_from_sheet(sheet_name=None, dry_run=False)
                                
                                st.success(f"Sync complete!")
                                st.write(f"**Sheet used:** {stats.get('sheet_name', 'Unknown')}")
                                st.write(f"- Added: {stats['added']} jobs")
                                st.write(f"- Updated: {stats['updated']} jobs")
                                st.write(f"- Errors: {stats['errors']}")
                                
                                if stats.get('error_details'):
                                    with st.expander("Error Details", expanded=True):
                                        for error in stats['error_details'][:20]:
                                            st.error(error)
                                        if len(stats['error_details']) > 20:
                                            st.write(f"... and {len(stats['error_details']) - 20} more errors")
                                
                                st.rerun()
                        except ImportError as e:
                            st.error(f"Missing dependencies: {e}\n\nInstall with: pip install gspread google-auth")
                        except Exception as e:
                            st.error(f"Error: {e}")
                            import traceback
                            st.exception(e)
                    else:
                        st.warning("Please provide credentials path and spreadsheet link")
        
        # Right column: Jobs table
        with right_col:
            st.header("Jobs")
            try:
                selected_job = render_job_list(db)
            except Exception as e:
                st.error(f"Error rendering job list: {e}")
                import traceback
                st.exception(e)
                selected_job = None
