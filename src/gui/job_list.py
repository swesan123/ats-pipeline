"""Job list component for displaying jobs table."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
from src.db.database import Database
from src.matching.skill_matcher import SkillMatcher
from src.models.skills import SkillOntology


def render_job_list(db: Database):
    """Render jobs table and return selected job."""
    jobs = db.list_jobs()
    
    if not jobs:
        st.info("No jobs added yet. Add a job using the form on the left.")
        return None
    
    # Calculate fit scores if resume exists
    fit_scores = {}
    try:
        resume = db.get_latest_resume()
        if resume:
            ontology = SkillOntology()
            matcher = SkillMatcher(ontology)
            for job in jobs:
                job_id = job.get('id')
                # Try to get from database first
                cached_score = db.get_latest_job_match_fit_score(job_id)
                if cached_score is not None:
                    fit_scores[job_id] = cached_score
                else:
                    # Calculate on the fly
                    job_skills = db.get_job_skills(job_id)
                    if job_skills:
                        job_match = matcher.match_job(resume, job_skills)
                        fit_scores[job_id] = job_match.fit_score
                        # Cache the result
                        resume_id = db.get_latest_resume_id()
                        if resume_id:
                            db.save_job_match(job_match, job_id, resume_id)
                    else:
                        fit_scores[job_id] = 0.0
        else:
            # No resume, set all to 0
            for job in jobs:
                fit_scores[job.get('id')] = 0.0
    except Exception as e:
        # If calculation fails, set all to 0
        st.error(f"Error calculating fit scores: {e}")
        for job in jobs:
            fit_scores[job.get('id')] = 0.0
    
    # Convert to DataFrame
    df = pd.DataFrame(jobs)
    df['Fit Score'] = df['id'].map(fit_scores).fillna(0.0)
    # Use status from database, default to 'New'
    if 'status' not in df.columns:
        df['status'] = 'New'
    df['Status'] = df['status'].fillna('New')
    
    # Status options
    status_options = ['New', 'Interested', 'Applied', 'Interview', 'Offer', 'Rejected', 'Withdrawn']
    
    # Create a copy for display with status as selectbox
    display_df = df[['company', 'title', 'Fit Score', 'Status', 'created_at']].copy()
    
    # Display table with editable status
    selected_rows = st.dataframe(
        display_df,
        column_config={
            "Fit Score": st.column_config.ProgressColumn(
                "Fit Score",
                min_value=0.0,
                max_value=1.0,
                format="%.1f%%",
            ),
            "Status": st.column_config.SelectboxColumn(
                "Status",
                options=status_options,
                width="medium",
                required=True,
            ),
            "created_at": st.column_config.DatetimeColumn("Date Added"),
        },
        on_select="rerun",
        selection_mode="single-row",
        width='stretch',
        key="job_list_table",
    )
    
    # Handle status updates from edited rows
    if hasattr(selected_rows, 'edited_rows') and selected_rows.edited_rows:
        for idx, changes in selected_rows.edited_rows.items():
            if 'Status' in changes:
                job_id = df.iloc[idx]['id']
                new_status = changes['Status']
                db.update_job_status(job_id, new_status)
                st.success(f"Updated status to: {new_status}")
                st.rerun()
    
    # Get selected job
    if selected_rows.selection.rows:
        selected_idx = selected_rows.selection.rows[0]
        selected_job = jobs[selected_idx]
        return selected_job
    
    return None

