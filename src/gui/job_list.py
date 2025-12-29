"""Job list component for displaying jobs table."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
from pathlib import Path
from src.db.database import Database
from src.matching.skill_matcher import SkillMatcher
from src.models.skills import SkillOntology
from src.models.resume import Resume
from src.storage.resume_manager import ResumeManager
from src.gui.job_helpers import auto_match_skills


def render_job_list(db: Database):
    """Render jobs table and return selected job."""
    try:
        jobs = db.list_jobs()
    except Exception as e:
        st.error(f"Error loading jobs: {e}")
        import traceback
        st.exception(e)
        return None
    
    if not jobs:
        st.info("No jobs added yet. Add a job using the form on the left.")
        return None
    
    # Get resume for matching
    resume = db.get_latest_resume()
    if not resume:
        resume_path = Path("data/resume.json")
        if resume_path.exists():
            try:
                import json
                with open(resume_path, 'r', encoding='utf-8') as f:
                    resume_data = json.load(f)
                resume = Resume.model_validate(resume_data)
            except Exception as e:
                st.warning(f"Could not load resume from file: {e}")
                resume = None
    
    # Refresh and Add Job buttons in same row (below Jobs header)
    col_refresh, col_add, col_spacer = st.columns([1, 1, 10])
    with col_refresh:
        # Simple refresh button
        if st.button("↻", help="Re-run skill matching for all jobs", key="refresh_jobs", width='stretch'):
            st.session_state['refreshing_jobs'] = True
            st.rerun()
    with col_add:
        # Add Job button - opens dialog
        # Use "Add (+)" since Streamlit has a bug rendering plain ASCII "+" alone in buttons
        if st.button("Add (+)", help="Add a new job posting", key="add_job_btn", width='stretch'):
            st.session_state['show_add_job_dialog'] = True
    
    # Auto-match skills if refreshing or if jobs don't have cached matches
    if resume:
        if st.session_state.get('refreshing_jobs', False):
            with st.spinner("Refreshing fit scores..."):
                ontology = SkillOntology()
                matcher = SkillMatcher(ontology)
                for job in jobs:
                    job_id = job.get('id')
                    # Force re-match
                    job_skills = db.get_job_skills(job_id)
                    if job_skills:
                        job_match = matcher.match_job(resume, job_skills)
                        resume_id = db.get_latest_resume_id()
                        if resume_id:
                            db.save_job_match(job_match, job_id, resume_id)
                st.session_state['refreshing_jobs'] = False
                st.success("Fit scores refreshed!")
                st.rerun()
        else:
            # Auto-match jobs that don't have cached scores - limit to first 10 to avoid blocking
            # The rest will be matched on-demand or via refresh button
            jobs_to_match = [job for job in jobs[:10]]  # Limit to first 10 jobs
            for job in jobs_to_match:
                job_id = job.get('id')
                cached_score = db.get_latest_job_match_fit_score(job_id)
                if cached_score is None:
                    try:
                        auto_match_skills(db, job_id, resume)
                    except Exception:
                        pass  # Continue with other jobs
    
    # Calculate fit scores
    fit_scores = {}
    if resume:
        ontology = SkillOntology()
        matcher = SkillMatcher(ontology)
        for job in jobs:
            job_id = job.get('id')
            cached_score = db.get_latest_job_match_fit_score(job_id)
            if cached_score is not None:
                fit_scores[job_id] = cached_score
            else:
                job_skills = db.get_job_skills(job_id)
                if job_skills:
                    job_match = matcher.match_job(resume, job_skills)
                    fit_scores[job_id] = job_match.fit_score
                    resume_id = db.get_latest_resume_id()
                    if resume_id:
                        db.save_job_match(job_match, job_id, resume_id)
                else:
                    fit_scores[job_id] = 0.0
    else:
        for job in jobs:
            fit_scores[job.get('id')] = 0.0
    
    # Convert to DataFrame - ensure we have the required columns
    if not jobs:
        st.info("No jobs added yet. Add a job using the form on the left.")
        return None
    
    try:
        df = pd.DataFrame(jobs)
        
        # Ensure required columns exist
        if 'id' not in df.columns:
            st.error("Jobs data missing 'id' column")
            return None
        
        df['Fit Score'] = df['id'].map(fit_scores).fillna(0.0)
        if 'status' not in df.columns:
            df['status'] = 'New'
        df['Status'] = df['status'].fillna('New')
        
        # Add download column - check if resume exists for each job
        try:
            resume_manager = ResumeManager()
            download_links = []
            for idx, job in enumerate(jobs):
                # Create JobPosting from job dict
                from src.models.job import JobPosting
                try:
                    job_obj = JobPosting(
                        company=job.get('company', ''),
                        title=job.get('title', ''),
                        location=job.get('location'),
                        description=job.get('description', ''),
                        source_url=job.get('source_url'),
                    )
                    resume_path = resume_manager.get_resume_by_job(job_obj)
                    download_links.append("📥" if resume_path and resume_path.exists() else "")
                except Exception:
                    # If error creating job object, just add empty
                    download_links.append("")
            df['Download'] = download_links
        except Exception:
            # If error, just add empty download column
            df['Download'] = [""] * len(df)
    except Exception as e:
        st.error(f"Error creating jobs DataFrame: {e}")
        import traceback
        st.exception(e)
        return None
    
    # Status options
    status_options = ['New', 'Interested', 'Applied', 'Interview', 'Offer', 'Rejected', 'Withdrawn']
    
    # Prepare display columns - include Google Sheets columns
    # Start with required columns
    display_cols = ['company', 'title', 'Fit Score', 'Status', 'created_at']
    
    # Add optional columns if they exist
    if 'date_applied' in df.columns:
        display_cols.append('date_applied')
    
    # Always add Download column
    display_cols.append('Download')
    
    # Filter to only include columns that exist in df
    display_cols = [col for col in display_cols if col in df.columns]
    
    display_df = df[display_cols].copy()
    
    # Build column config dynamically
    column_config = {
        "Fit Score": st.column_config.ProgressColumn(
            "Fit Score",
            min_value=0.0,
            max_value=1.0,
            format="%.2f%%",
        ),
        "created_at": st.column_config.DatetimeColumn("Date Added"),
        "Download": st.column_config.TextColumn("Download", width="small"),
    }
    
    # Add date_applied config if column exists
    if 'date_applied' in display_df.columns:
        column_config["date_applied"] = st.column_config.DatetimeColumn("Date Applied")
    
    # Add status-based row styling using pandas styling
    status_color_map = {
        "Rejected": "background-color: #ffebee",  # Light red
        "Withdrawn": "background-color: #ffebee",  # Light red
        "Offer": "background-color: #e8f5e9",  # Light green
        "Applied": "background-color: #fff9c4",  # Light yellow
        "Interview": "background-color: #fff9c4",  # Light yellow
    }
    
    def get_row_style(row):
        """Get styling for a row based on status."""
        status_str = str(row.get('Status', 'New')) if 'Status' in row else 'New'
        style = status_color_map.get(status_str, "")
        return [style] * len(row)
    
    # Display table - ensure it always shows
    try:
        if display_df.empty or len(display_df) == 0:
            st.warning("No jobs to display (DataFrame is empty)")
            return None
        
        # Show row count
        st.caption(f"Showing {len(display_df)} job(s)")
        
        # Calculate height based on row count (min 400, max 800)
        row_count = len(display_df)
        table_height = min(max(400, row_count * 35), 800)
        
        # Apply row styling
        try:
            styled_df = display_df.style.apply(get_row_style, axis=1)
            selected_rows = st.dataframe(
                styled_df,
                column_config=column_config,
                on_select="rerun",
                selection_mode="single-row",
                width='stretch',  # Full width
                height=table_height,
                key="job_list_table",
            )
        except Exception:
            # Fallback if styling doesn't work
            selected_rows = st.dataframe(
                display_df,
                column_config=column_config,
                on_select="rerun",
                selection_mode="single-row",
                width='stretch',  # Full width
                height=table_height,
                key="job_list_table",
            )
    except Exception as e:
        st.error(f"Error displaying jobs table: {e}")
        import traceback
        st.exception(e)
        # Fallback: show simple table without advanced config
        try:
            st.dataframe(display_df, width='stretch')
        except:
            st.write("Unable to display jobs table. Please check the console for errors.")
        # Create a dummy selected_rows object
        class DummySelection:
            def __init__(self):
                self.rows = []
        class DummyRows:
            def __init__(self):
                self.selection = DummySelection()
        selected_rows = DummyRows()
    
    # Handle download clicks (check if download column was clicked)
    if selected_rows.selection.rows:
        selected_idx = selected_rows.selection.rows[0]
        selected_job_id = int(df.iloc[selected_idx]['id'])
        selected_job = jobs[selected_idx]
        
        # Get job object for download
        from src.models.job import JobPosting
        job_obj = JobPosting(
            company=selected_job.get('company', ''),
            title=selected_job.get('title', ''),
            location=selected_job.get('location'),
            description=selected_job.get('description', ''),
            source_url=selected_job.get('source_url'),
        )
        resume_path = resume_manager.get_resume_by_job(job_obj)
        
        # Status editor
        st.divider()
        current_status = str(df.iloc[selected_idx]['Status'])
        
        col1, col2 = st.columns([2, 1])
        with col1:
            try:
                current_index = status_options.index(current_status)
            except ValueError:
                current_index = 0
            
            new_status = st.selectbox(
                "Change Status",
                options=status_options,
                index=current_index,
                key=f"status_select_{selected_job_id}",
            )
        with col2:
            st.write("")
            st.write("")
            update_button = st.button("Update Status", key=f"update_status_{selected_job_id}", type="primary")
        
        if update_button:
            try:
                if new_status != current_status:
                    db.update_job_status(selected_job_id, new_status)
                    st.success(f"Status updated to: **{new_status}**")
                    st.rerun()
            except Exception as e:
                st.error(f"Error updating status: {e}")
        
        # Download button if resume exists
        if resume_path and resume_path.exists():
            st.download_button(
                "Download Resume PDF",
                data=resume_path.read_bytes(),
                file_name=resume_path.name,
                mime="application/pdf",
                key=f"download_resume_{selected_job_id}"
            )
        
        # Job details in expander (popup-like)
        with st.expander(f"📋 {selected_job.get('company')} - {selected_job.get('title')}", expanded=True):
            # Import and render job details
            from src.gui.job_details import render_job_details
            render_job_details(db, selected_job)
        
        # Ensure description is included
        if 'description' not in selected_job or not selected_job.get('description'):
            job_obj_db = db.get_job(selected_job.get('id'))
            if job_obj_db:
                selected_job['description'] = job_obj_db.description
        
        return selected_job
    
    return None
