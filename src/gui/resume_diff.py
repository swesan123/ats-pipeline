"""Resume diff view component for comparing original vs customized resumes."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from src.models.resume import Resume
from src.models.job import JobPosting
from src.rendering.latex_renderer import LaTeXRenderer
from src.gui.resume_preview import render_resume_preview
import tempfile


def render_resume_diff(original_resume: Resume, customized_resume: Resume, job: JobPosting = None):
    """Render side-by-side diff view of original vs customized resume.
    
    Args:
        original_resume: Original resume object
        customized_resume: Customized resume object
        job: Optional job posting for context
    """
    st.subheader("Resume Changes Comparison")
    
    # Text diff section - bullets comparison
    st.write("**Bullet Changes:**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Original Resume")
        _render_bullets(original_resume, "original")
    
    with col2:
        st.markdown("### Customized Resume")
        _render_bullets(customized_resume, "customized")
    
    st.divider()
    
    # PDF preview section
    st.subheader("PDF Comparison")
    pdf_col1, pdf_col2 = st.columns(2)
    
    with pdf_col1:
        st.write("**Original PDF:**")
        try:
            renderer = LaTeXRenderer()
            import time
            original_pdf = Path(tempfile.gettempdir()) / f"resume_original_{int(time.time())}.pdf"
            renderer.render_pdf(original_resume, original_pdf)
            if original_pdf.exists():
                render_resume_preview(original_pdf)
        except Exception as e:
            st.error(f"Error generating original PDF: {e}")
            import traceback
            st.exception(e)
    
    with pdf_col2:
        st.write("**Customized PDF:**")
        try:
            renderer = LaTeXRenderer()
            import time
            customized_pdf = Path(tempfile.gettempdir()) / f"resume_customized_{int(time.time())}.pdf"
            renderer.render_pdf(customized_resume, customized_pdf)
            if customized_pdf.exists():
                render_resume_preview(customized_pdf)
        except Exception as e:
            st.error(f"Error generating customized PDF: {e}")
            import traceback
            st.exception(e)


def _render_bullets(resume: Resume, prefix: str):
    """Render bullets from a resume with highlighting."""
    # Experience bullets
    if resume.experience:
        st.write("**Experience:**")
        for exp in resume.experience:
            st.write(f"*{exp.role} at {exp.organization}*")
            for i, bullet in enumerate(exp.bullets):
                st.write(f"{i+1}. {bullet.text}")
            st.write("")
    
    # Project bullets
    if resume.projects:
        st.write("**Projects:**")
        for proj in resume.projects:
            st.write(f"*{proj.name}*")
            for i, bullet in enumerate(proj.bullets):
                st.write(f"{i+1}. {bullet.text}")
            st.write("")

