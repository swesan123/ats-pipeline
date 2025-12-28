"""Main Streamlit window for job management."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from src.db.database import Database
from src.gui.job_list import render_job_list
from src.gui.job_input import render_job_input
from src.gui.job_details import render_job_details


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="ATS Pipeline - Job Manager",
        page_icon=None,
        layout="wide",
    )
    
    st.title("ATS Pipeline - Job Application Manager")
    
    # Initialize database
    if 'db' not in st.session_state:
        st.session_state.db = Database()
    
    # Initialize selected job
    if 'selected_job_id' not in st.session_state:
        st.session_state.selected_job_id = None
    
    # Two-column layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("Add Job")
        render_job_input(st.session_state.db)
        
        st.header("Quick Actions")
        if st.button("Refresh Jobs"):
            st.rerun()
        if st.button("Settings"):
            st.info("Settings panel coming soon")
    
    with col2:
        st.header("Jobs")
        selected_job = render_job_list(st.session_state.db)
        
        if selected_job:
            st.session_state.selected_job_id = selected_job.get('id')
            st.divider()
            render_job_details(st.session_state.db, selected_job)


if __name__ == '__main__':
    main()

