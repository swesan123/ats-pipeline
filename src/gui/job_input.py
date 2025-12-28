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
    
    # Clean up text - remove extra whitespace but preserve structure
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text_clean = ' '.join(text.split())
    
    # Pattern 1: "Title at Company" (most common LinkedIn format)
    # Look for patterns like "AI Platform Engineer at Denvr" anywhere in text
    # This is the most reliable pattern
    match = re.search(r'([A-Z][a-zA-Z\s&]{5,50}?(?:Engineer|Developer|Manager|Analyst|Architect|Scientist|Specialist|Consultant|Lead|Director|VP|President|Designer|Coordinator))\s+at\s+([A-Z][a-zA-Z\s&]{2,40}?)(?:\s+·|\s*$|\n|Toronto|New York|\(Hybrid\)|\(Remote\)|Show)', text_clean, re.IGNORECASE)
    if match:
        title = match.group(1).strip()
        company = match.group(2).strip()
        # Clean up company name (remove location and other text if captured)
        company = re.sub(r'\s+(Toronto|New York|Hybrid|Remote|Show|Apply|Save).*$', '', company, flags=re.IGNORECASE).strip()
        # Clean up title (remove "Save Save" or other artifacts)
        title = re.sub(r'^(Save\s+)+', '', title, flags=re.IGNORECASE).strip()
        if title and company and company != "Unknown":
            return title, company
    
    # Pattern 2: Look for "at [Company]" anywhere in text and extract preceding title
    match = re.search(r'([A-Z][a-zA-Z\s&]{5,50}?)\s+at\s+([A-Z][a-zA-Z\s&]{2,40}?)(?:\s+·|\s*$|\n|Toronto|New York|\(Hybrid\)|\(Remote\)|Show)', text_clean, re.IGNORECASE)
    if match:
        potential_title = match.group(1).strip()
        company = match.group(2).strip()
        # Clean up
        company = re.sub(r'\s+(Toronto|New York|Hybrid|Remote|Show|Apply|Save).*$', '', company, flags=re.IGNORECASE).strip()
        potential_title = re.sub(r'^(Save\s+)+', '', potential_title, flags=re.IGNORECASE).strip()
        # Only use if it looks like a job title (has common keywords or is reasonable length)
        if len(potential_title) > 5 and len(potential_title) < 60:
            title = potential_title
            if company and company != "Unknown":
                return title, company
    
    # Pattern 3: Extract title from beginning - look for common job title patterns
    title_match = re.search(r'^([A-Z][a-zA-Z\s&]{5,50}?(?:Engineer|Developer|Manager|Analyst|Architect|Scientist|Specialist|Consultant|Lead|Director|VP|President|Designer|Coordinator))', text_clean, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()
        # Remove location if it's part of the title
        title = re.sub(r'\s+Toronto.*$', '', title, flags=re.IGNORECASE).strip()
        title = re.sub(r'\s+\d+\s+weeks?\s+ago.*$', '', title, flags=re.IGNORECASE).strip()
    
    # Pattern 4: Look for company in "About the job" or "Who We Are" sections
    if company == "Unknown":
        # Try to find company name in context like "Denvr is a..." or "At Denvr, we..."
        company_match = re.search(r'(?:^|\.|Who We Are)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s+(?:is|are|provides|offers|designs|has)', text_clean, re.IGNORECASE)
        if company_match:
            potential_company = company_match.group(1).strip()
            # Filter out common false positives
            if potential_company not in ['We', 'The', 'This', 'Our', 'They', 'These', 'Who'] and len(potential_company) < 30:
                company = potential_company
    
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

