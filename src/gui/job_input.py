"""Job input component for adding jobs."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import re
import streamlit as st
from src.db.database import Database
from src.extractors.job_skills import JobSkillExtractor
from src.extractors.job_url_scraper import JobURLScraper
from src.models.job import JobPosting


def _extract_job_info_from_text(text: str) -> tuple[str, str]:
    """Extract company and title from job description text.
    
    Returns: (title, company)
    """
    title = "Unknown"
    company = "Unknown"
    
    # Pattern 1: "Title at Company" or "Title at Company ·"
    match = re.search(r'^([^·\n]+?)\s+at\s+([^·\n]+?)(?:\s*·|$)', text, re.IGNORECASE | re.MULTILINE)
    if match:
        title = match.group(1).strip()
        company = match.group(2).strip()
        return title, company
    
    # Pattern 2: "Company · Title" format
    match = re.search(r'^([^·\n]+?)\s+·\s+([^·\n]+?)(?:\s*·|$)', text, re.IGNORECASE | re.MULTILINE)
    if match:
        company = match.group(1).strip()
        title = match.group(2).strip()
        return title, company
    
    # Pattern 3: Look for "About the job" or "Who We Are" sections - extract from context
    # Try to find company name after "at [Company]" patterns
    match = re.search(r'at\s+([A-Z][a-zA-Z\s&]+?)(?:\s+·|\s*$|\n)', text, re.IGNORECASE)
    if match:
        company = match.group(1).strip()
    
    # Try to find title - look for common patterns like "AI Platform Engineer" at start
    title_match = re.search(r'^([A-Z][a-zA-Z\s]+Engineer|[A-Z][a-zA-Z\s]+Developer|[A-Z][a-zA-Z\s]+Manager)', text, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()
    
    return title, company


def render_job_input(db: Database):
    """Render job input form."""
    job_url = st.text_input("Job URL or Description", placeholder="Paste job URL or description here...")
    
    if st.button("Add Job", type="primary"):
        if not job_url:
            st.error("Please enter a job URL or description")
            return
        
        with st.spinner("Extracting job information..."):
            try:
                # Check if it's a URL
                if job_url.startswith(('http://', 'https://')):
                    # Use URL scraper
                    scraper = JobURLScraper(use_playwright=False)
                    job_data = scraper.extract_job_content(job_url)
                    job_posting = JobPosting(
                        company=job_data.get('company', 'Unknown'),
                        title=job_data.get('title', 'Unknown'),
                        location=job_data.get('location'),
                        description=job_data.get('description', job_url),
                        source_url=job_data.get('source_url', job_url),
                    )
                else:
                    # Extract from text
                    title, company = _extract_job_info_from_text(job_url)
                    job_posting = JobPosting(
                        company=company,
                        title=title,
                        description=job_url,
                        source_url=None,
                    )
                
                # Extract skills
                with st.spinner("Extracting skills from job description..."):
                    extractor = JobSkillExtractor()
                    job_skills = extractor.extract_skills(job_posting)
                
                # Save to database
                job_id = db.save_job(job_posting, job_skills)
                
                st.success(f"✓ Job added successfully! (ID: {job_id})")
                st.rerun()
            except Exception as e:
                st.error(f"Error adding job: {e}")
                import traceback
                st.exception(e)
    
    # File upload option
    uploaded_file = st.file_uploader("Or upload job description file", type=['txt', 'md'])
    if uploaded_file:
        job_text = uploaded_file.read().decode('utf-8')
        title, company = _extract_job_info_from_text(job_text)
        job_posting = JobPosting(
            company=company,
            title=title,
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

