"""Job details component for displaying job information."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from src.db.database import Database
from src.matching.skill_matcher import SkillMatcher
from src.models.skills import SkillOntology
from src.models.resume import Resume


def render_job_details(db: Database, job: dict):
    """Render job details panel."""
    st.header("Job Details")
    
    st.write(f"**Company:** {job['company']}")
    st.write(f"**Title:** {job['title']}")
    if job.get('location'):
        st.write(f"**Location:** {job['location']}")
    
    # Get job skills
    job_skills = db.get_job_skills(job['id'])
    if job_skills:
        st.subheader("Required Skills")
        st.write(", ".join(job_skills.required_skills[:10]))
        
        if job_skills.preferred_skills:
            st.subheader("Preferred Skills")
            st.write(", ".join(job_skills.preferred_skills[:10]))
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎯 Generate Resume", type="primary"):
            st.session_state['generate_resume_job_id'] = job['id']
            st.rerun()
    
    with col2:
        if st.button("📊 View Match Details"):
            st.session_state['view_match_job_id'] = job['id']
            st.rerun()
    
    with col3:
        if st.button("📝 Generate Cover Letter"):
            st.info("Cover letter generation coming soon (P1)")
    
    # Handle generate resume action
    if 'generate_resume_job_id' in st.session_state:
        _handle_generate_resume(db, st.session_state['generate_resume_job_id'])
        del st.session_state['generate_resume_job_id']


def _handle_generate_resume(db: Database, job_id: int):
    """Handle resume generation workflow."""
    from src.matching.resume_reuse_checker import ResumeReuseChecker
    
    # Get job and skills
    job = db.get_job(job_id)
    if not job:
        st.error("Job not found.")
        return
    
    job_skills = db.get_job_skills(job_id)
    if not job_skills:
        st.error("Job skills not found. Please extract skills first.")
        return
    
    # Check for reusable resume
    ontology = SkillOntology()
    matcher = SkillMatcher(ontology)
    reuse_checker = ResumeReuseChecker(db, matcher)
    
    reusable = reuse_checker.find_reusable_resume(
        job_skills,
        target_job_id=job_id,
        min_fit_score=0.90,
        min_similarity=0.85,
    )
    
    if reusable:
        resume_id, reused_resume, fit_score, similarity = reusable
        st.success(f"Found reusable resume! (ID: {resume_id}, Fit: {fit_score:.1%}, Similarity: {similarity:.1%})")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Use Existing Resume", type="primary"):
                st.session_state['selected_resume_id'] = resume_id
                st.rerun()
        with col2:
            if st.button("🔄 Generate New Resume"):
                st.session_state['generate_new'] = True
                st.rerun()
    else:
        # Get latest resume
        resume = db.get_latest_resume()
        if not resume:
            st.error("No resume found. Please convert LaTeX resume to JSON first.")
            return
        
        # Match job
        job_match = matcher.match_job(resume, job_skills)
        
        st.info(f"Job fit score: {job_match.fit_score:.1%}")
        st.info("Resume rewrite workflow would start here...")

