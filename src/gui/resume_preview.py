"""Resume preview component for Streamlit GUI."""

import streamlit as st
from pathlib import Path
from typing import Optional
from datetime import datetime


def render_resume_preview(resume_path: Path, job: Optional[dict] = None):
    """Render resume preview with PDF viewer and download button.
    
    Args:
        resume_path: Path to the PDF file
        job: Optional job dictionary with company and title
    """
    if not resume_path.exists():
        st.error("Resume file not found")
        return
    
    # PDF Preview
    st.subheader("Resume Preview")
    with open(resume_path, "rb") as pdf_file:
        pdf_bytes = pdf_file.read()
    
    # Use iframe for PDF preview (works without extra components)
    import base64
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)
    
    # Download button
    st.download_button(
        label="Download Resume PDF",
        data=pdf_bytes,
        file_name=resume_path.name,
        mime="application/pdf"
    )
    
    # Metadata
    if job:
        st.write(f"**Company:** {job.get('company', 'N/A')}")
        st.write(f"**Job Title:** {job.get('title', 'N/A')}")
    
    # File metadata
    file_stat = resume_path.stat()
    created_time = datetime.fromtimestamp(file_stat.st_mtime)
    st.write(f"**Generated:** {created_time.strftime('%Y-%m-%d %H:%M:%S')}")

