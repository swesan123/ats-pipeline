"""Job input component for adding jobs."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from src.db.database import Database
from src.extractors.job_skills import JobSkillExtractor
from src.models.job import JobPosting


def render_job_input(db: Database):
    """Render job input form."""
    job_url = st.text_input("Job URL or Description", placeholder="Paste job URL or description here...")
    
    if st.button("Add Job", type="primary"):
        if not job_url:
            st.error("Please enter a job URL or description")
            return
        
        with st.spinner("Extracting skills from job description..."):
            try:
                # Create job posting
                job_posting = JobPosting(
                    company="Unknown",
                    title="Unknown",
                    description=job_url,
                    source_url=job_url if job_url.startswith("http") else None,
                )
                
                # Extract skills
                extractor = JobSkillExtractor()
                job_skills = extractor.extract_skills(job_posting)
                
                # Save to database
                job_id = db.save_job(job_posting, job_skills)
                
                st.success(f"✓ Job added successfully! (ID: {job_id})")
                st.rerun()
            except Exception as e:
                st.error(f"Error adding job: {e}")
    
    # File upload option
    uploaded_file = st.file_uploader("Or upload job description file", type=['txt', 'md'])
    if uploaded_file:
        job_text = uploaded_file.read().decode('utf-8')
        job_posting = JobPosting(
            company="Unknown",
            title="Unknown",
            description=job_text,
        )
        
        if st.button("Add Job from File"):
            with st.spinner("Extracting skills..."):
                try:
                    extractor = JobSkillExtractor()
                    job_skills = extractor.extract_skills(job_posting)
                    job_id = db.save_job(job_posting, job_skills)
                    st.success(f"✓ Job added from file! (ID: {job_id})")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

