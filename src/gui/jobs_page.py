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
        # Google Sheets Sync (collapsible)
        with st.expander("Google Sheets Sync", expanded=False):
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
            
            # Push to Google Sheets button
            if st.button("Push to Google Sheets", help="Push all jobs from database to Google Sheets", key="gs_push"):
                if credentials_path and spreadsheet_id:
                    try:
                        from src.sync.google_sheets_client import GoogleSheetsClient
                        from src.sync.sheet_sync import SheetSyncService
                        
                        with st.spinner("Pushing jobs to Google Sheets..."):
                            client = GoogleSheetsClient(credentials_path, spreadsheet_id)
                            sync_service = SheetSyncService(db, client)
                            stats = sync_service.push_to_sheet()
                            
                            st.success(f"Push complete!")
                            st.write(f"- Created/Updated: {stats.get('created', 0) + stats.get('updated', 0)} rows")
                            st.write(f"- Errors: {stats.get('errors', 0)}")
                            
                            if stats.get('error_details'):
                                with st.expander("Error Details", expanded=True):
                                    for error in stats['error_details'][:20]:
                                        st.error(error)
                                    if len(stats['error_details']) > 20:
                                        st.write(f"... and {len(stats['error_details']) - 20} more errors")
                    except ImportError as e:
                        st.error(f"Missing dependencies: {e}\n\nInstall with: pip install gspread google-auth")
                    except Exception as e:
                        st.error(f"Error: {e}")
                        import traceback
                        st.exception(e)
                else:
                    st.warning("Please provide credentials path and spreadsheet link")
        
        # Full-width Jobs table
        st.header("Jobs")
        
        # Add Job Dialog - using modal or conditional rendering (placed here to be near buttons)
        if st.session_state.get('show_add_job_dialog', False):
            # Try st.modal() first (Streamlit 1.28+), fallback to conditional rendering
            try:
                # Check if st.modal exists
                if hasattr(st, 'modal'):
                    with st.modal("Add Job"):
                        st.write("**Add a new job posting**")
                        
                        # Job input options
                        input_method = st.radio(
                            "Input method:",
                            ["Job URL", "Job Description", "Upload File"],
                            horizontal=True,
                            key="job_input_method"
                        )
                        
                        job_url = None
                        job_description = None
                        uploaded_file = None
                        
                        if input_method == "Job URL":
                            job_url = st.text_input("Job URL", key="dialog_job_url")
                        elif input_method == "Job Description":
                            # Allow manual entry of company and title for better accuracy
                            col_title, col_company = st.columns(2)
                            with col_title:
                                manual_title = st.text_input("Job Title (optional - will auto-detect if blank)", key="dialog_manual_title", placeholder="e.g., Software Engineer")
                            with col_company:
                                manual_company = st.text_input("Company (optional - will auto-detect if blank)", key="dialog_manual_company", placeholder="e.g., Lemurian Labs")
                            job_description = st.text_area("Job Description", height=200, key="dialog_job_desc")
                        else:  # Upload File
                            # Allow manual entry of company and title for uploaded files too
                            col_title, col_company = st.columns(2)
                            with col_title:
                                manual_title = st.text_input("Job Title (optional - will auto-detect if blank)", key="dialog_manual_title_file", placeholder="e.g., Software Engineer")
                            with col_company:
                                manual_company = st.text_input("Company (optional - will auto-detect if blank)", key="dialog_manual_company_file", placeholder="e.g., Lemurian Labs")
                            uploaded_file = st.file_uploader("Upload job description file", type=['txt', 'md'], key="dialog_job_file")
                            if uploaded_file:
                                job_description = uploaded_file.read().decode('utf-8')
                        
                        col_submit, col_cancel = st.columns(2)
                        with col_submit:
                            if st.button("Add Job", type="primary", key="dialog_add_job"):
                                try:
                                    from src.gui.job_input import _extract_job_info_from_text, _save_job_from_text
                                    
                                    if job_url:
                                        # Extract from URL
                                        from src.extractors.job_url_scraper import JobURLScraper
                                        from src.models.job import JobPosting
                                        scraper = JobURLScraper()
                                        job_data = scraper.extract_job_content(job_url)
                                        if job_data and job_data.get('description'):
                                            # Create JobPosting from dict
                                            job_posting = JobPosting(
                                                company=job_data.get('company', 'Unknown'),
                                                title=job_data.get('title', 'Unknown'),
                                                location=job_data.get('location'),
                                                description=job_data.get('description', ''),
                                                source_url=job_data.get('source_url', job_url),
                                            )
                                            # Save using the job posting object
                                            from src.extractors.job_skills import JobSkillExtractor
                                            extractor = JobSkillExtractor()
                                            job_skills = extractor.extract_skills(job_posting)
                                            db.save_job(job_posting, job_skills=job_skills)
                                            st.success("Job added successfully!")
                                            st.session_state['show_add_job_dialog'] = False
                                            st.rerun()
                                        else:
                                            st.error("Could not extract job content from URL")
                                    elif job_description:
                                        # Use manual title/company if provided, otherwise auto-detect
                                        manual_title_val = st.session_state.get('dialog_manual_title', '').strip()
                                        manual_company_val = st.session_state.get('dialog_manual_company', '').strip()
                                        _save_job_from_text(db, job_description, source_url=None, 
                                                          manual_title=manual_title_val if manual_title_val else None,
                                                          manual_company=manual_company_val if manual_company_val else None)
                                        st.success("Job added successfully!")
                                        st.session_state['show_add_job_dialog'] = False
                                        st.rerun()
                                    else:
                                        st.warning("Please provide a job URL or description")
                                except Exception as e:
                                    st.error(f"Error adding job: {e}")
                                    import traceback
                                    st.exception(e)
                        
                        with col_cancel:
                            if st.button("Cancel", key="dialog_cancel"):
                                st.session_state['show_add_job_dialog'] = False
                                st.rerun()
                else:
                    # Fallback: use expander for dialog-like behavior
                    raise AttributeError("st.modal not available")
            except (AttributeError, Exception):
                # Fallback: use expander with conditional rendering
                with st.expander("Add Job", expanded=True):
                    st.write("**Add a new job posting**")
                    
                    # Job input options
                    input_method = st.radio(
                        "Input method:",
                        ["Job URL", "Job Description", "Upload File"],
                        horizontal=True,
                        key="job_input_method"
                    )
                    
                    job_url = None
                    job_description = None
                    uploaded_file = None
                    
                    if input_method == "Job URL":
                        job_url = st.text_input("Job URL", key="dialog_job_url_fallback")
                    elif input_method == "Job Description":
                        # Allow manual entry of company and title for better accuracy
                        col_title, col_company = st.columns(2)
                        with col_title:
                            manual_title = st.text_input("Job Title (optional - will auto-detect if blank)", key="dialog_manual_title_fallback", placeholder="e.g., Software Engineer")
                        with col_company:
                            manual_company = st.text_input("Company (optional - will auto-detect if blank)", key="dialog_manual_company_fallback", placeholder="e.g., Lemurian Labs")
                        job_description = st.text_area("Job Description", height=200, key="dialog_job_desc_fallback")
                    else:  # Upload File
                        # Allow manual entry of company and title for uploaded files too
                        col_title, col_company = st.columns(2)
                        with col_title:
                            manual_title = st.text_input("Job Title (optional - will auto-detect if blank)", key="dialog_manual_title_file_fallback", placeholder="e.g., Software Engineer")
                        with col_company:
                            manual_company = st.text_input("Company (optional - will auto-detect if blank)", key="dialog_manual_company_file_fallback", placeholder="e.g., Lemurian Labs")
                        uploaded_file = st.file_uploader("Upload job description file", type=['txt', 'md'], key="dialog_job_file_fallback")
                        if uploaded_file:
                            job_description = uploaded_file.read().decode('utf-8')
                    
                    col_submit, col_cancel = st.columns(2)
                    with col_submit:
                        if st.button("Add Job", type="primary", key="dialog_add_job"):
                            try:
                                from src.gui.job_input import _extract_job_info_from_text, _save_job_from_text
                                
                                if job_url:
                                    # Extract from URL
                                    from src.extractors.job_url_scraper import JobURLScraper
                                    from src.models.job import JobPosting
                                    scraper = JobURLScraper()
                                    job_data = scraper.extract_job_content(job_url)
                                    if job_data and job_data.get('description'):
                                        # Create JobPosting from dict
                                        job_posting = JobPosting(
                                            company=job_data.get('company', 'Unknown'),
                                            title=job_data.get('title', 'Unknown'),
                                            location=job_data.get('location'),
                                            description=job_data.get('description', ''),
                                            source_url=job_data.get('source_url', job_url),
                                        )
                                        # Save using the job posting object
                                        from src.extractors.job_skills import JobSkillExtractor
                                        extractor = JobSkillExtractor()
                                        job_skills = extractor.extract_skills(job_posting)
                                        db.save_job(job_posting, job_skills=job_skills)
                                        st.success("Job added successfully!")
                                        st.session_state['show_add_job_dialog'] = False
                                        st.rerun()
                                    else:
                                        st.error("Could not extract job content from URL")
                                elif job_description:
                                    # Use manual title/company if provided, otherwise auto-detect
                                    manual_title_val = st.session_state.get('dialog_manual_title_fallback', '').strip()
                                    manual_company_val = st.session_state.get('dialog_manual_company_fallback', '').strip()
                                    _save_job_from_text(db, job_description, source_url=None,
                                                      manual_title=manual_title_val if manual_title_val else None,
                                                      manual_company=manual_company_val if manual_company_val else None)
                                    st.success("Job added successfully!")
                                    st.session_state['show_add_job_dialog'] = False
                                    st.rerun()
                                else:
                                    st.warning("Please provide a job URL or description")
                            except Exception as e:
                                st.error(f"Error adding job: {e}")
                                import traceback
                                st.exception(e)
                    
                    with col_cancel:
                        if st.button("Cancel", key="dialog_cancel"):
                            st.session_state['show_add_job_dialog'] = False
                            st.rerun()
        
        try:
            selected_job = render_job_list(db)
        except Exception as e:
            st.error(f"Error rendering job list: {e}")
            import traceback
            st.exception(e)
            selected_job = None
