"""Main Streamlit window for job management."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from src.db.database import Database
from src.gui.jobs_page import render_jobs_page
from src.gui.experience_section import render_experience_section
from src.gui.projects_section import render_projects_section
from src.gui.skills_section import render_skills_section
from src.gui.resumes_page import render_resumes_page
from src.gui.resume_template_section import render_resume_template_section


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="ATS Pipeline",
        page_icon=None,
        layout="wide",
    )
    
    # Initialize database
    if 'db' not in st.session_state:
        st.session_state.db = Database()
    
    # Initialize selected job
    if 'selected_job_id' not in st.session_state:
        st.session_state.selected_job_id = None
    
    # Initialize page selection
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Jobs"
    
    # Navigation bar
    nav_cols = st.columns(6)
    pages = ["Jobs", "Experience", "Projects", "Skills", "Resumes", "Settings"]
    
    for i, page in enumerate(pages):
        with nav_cols[i]:
            if st.button(page, use_container_width=True, 
                        type="primary" if st.session_state.current_page == page else "secondary",
                        key=f"nav_{page}"):
                st.session_state.current_page = page
                st.rerun()
    
    st.divider()
    
    # Render current page - use empty container to clear any previous content/context
    # This ensures clean page transitions without column context leakage
    page_container = st.empty()
    with page_container.container():
        if st.session_state.current_page == "Jobs":
            render_jobs_page(st.session_state.db)
        elif st.session_state.current_page == "Experience":
            render_experience_section()
        elif st.session_state.current_page == "Projects":
            render_projects_section()
        elif st.session_state.current_page == "Skills":
            render_skills_section()
        elif st.session_state.current_page == "Resumes":
            render_resumes_page(st.session_state.db)
        elif st.session_state.current_page == "Settings":
            st.header("Settings")
            st.info("Settings panel coming soon")


if __name__ == '__main__':
    main()

