"""Job list component for displaying jobs table."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
from src.db.database import Database


def render_job_list(db: Database):
    """Render jobs table and return selected job."""
    jobs = db.list_jobs()
    
    if not jobs:
        st.info("No jobs added yet. Add a job using the form on the left.")
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(jobs)
    df['Fit Score'] = 0.0  # Placeholder - would be calculated from matches
    df['Status'] = 'New'  # Placeholder
    
    # Display table
    selected_rows = st.dataframe(
        df[['company', 'title', 'Fit Score', 'Status', 'created_at']],
        column_config={
            "Fit Score": st.column_config.ProgressColumn(
                "Fit Score",
                min_value=0.0,
                max_value=1.0,
                format="%.1f",
            ),
            "created_at": st.column_config.DatetimeColumn("Date Added"),
        },
        on_select="rerun",
        selection_mode="single-row",
        use_container_width=True,
    )
    
    # Get selected job
    if selected_rows.selection.rows:
        selected_idx = selected_rows.selection.rows[0]
        selected_job = jobs[selected_idx]
        return selected_job
    
    return None

