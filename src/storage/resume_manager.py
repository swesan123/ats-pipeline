"""Resume storage manager for organized file structure."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.models.resume import Resume
from src.models.job import JobPosting


class ResumeManager:
    """Manages organized resume storage with date-based folders."""
    
    def __init__(self, base_dir: Path = Path("resumes")):
        """Initialize resume manager.
        
        Args:
            base_dir: Base directory for storing resumes (default: "resumes")
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True, parents=True)
    
    def save_resume(
        self,
        resume: Resume,
        job: Optional[JobPosting] = None,
        is_customized: bool = False
    ) -> Path:
        """Save resume to organized folder structure.
        
        Structure:
        - resumes/
          - resume_2025-12-28_14-30-45/
            - Denvr_AI_Platform_Engineer.json
            - Denvr_AI_Platform_Engineer.pdf
        
        Args:
            resume: Resume model to save
            job: Optional job posting for filename generation
            is_customized: Whether this resume was customized for a specific job
            
        Returns:
            Path to the resume directory
        """
        # Generate folder name: resume_YYYY-MM-DD_HH-MM-SS
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = f"resume_{timestamp}"
        resume_dir = self.base_dir / folder_name
        resume_dir.mkdir(exist_ok=True, parents=True)
        
        # Generate human-readable filename
        if job:
            filename = self._sanitize_filename(f"{job.company}_{job.title}")
        else:
            filename = "resume_general"
        
        # Save JSON
        json_path = resume_dir / f"{filename}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(resume.model_dump(), f, indent=2, default=str)
        
        # Generate and save PDF
        from src.rendering.latex_renderer import LaTeXRenderer
        renderer = LaTeXRenderer()
        pdf_path = resume_dir / f"{filename}.pdf"
        try:
            renderer.render_pdf(resume, pdf_path)
            
            # Track resume generated event (if db available)
            # Note: This requires db to be passed or accessed differently
            # Tracking will be done at the calling code level
        except Exception as e:
            # If PDF generation fails, still save JSON
            import warnings
            warnings.warn(f"PDF generation failed: {e}")
        
        return resume_dir
    
    def _sanitize_filename(self, name: str, max_length: int = 100) -> str:
        """Sanitize filename for filesystem compatibility.
        
        Args:
            name: Original filename
            max_length: Maximum length for filename
            
        Returns:
            Sanitized filename safe for filesystem
        """
        # Remove special characters, keep alphanumeric, spaces, hyphens, underscores
        sanitized = re.sub(r'[^\w\s-]', '', name)
        # Replace spaces and multiple hyphens/underscores with single underscore
        sanitized = re.sub(r'[-\s]+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length].rstrip('_')
        return sanitized if sanitized else "resume"
    
    def get_resume_paths(self, job_id: Optional[int] = None) -> list[Path]:
        """Get resume directory paths, optionally filtered by job_id.
        
        Args:
            job_id: Optional job ID to filter by (requires database lookup)
            
        Returns:
            List of resume directory paths
        """
        if not self.base_dir.exists():
            return []
        
        # Get all resume directories sorted by name (which includes timestamp)
        resume_dirs = sorted(
            [d for d in self.base_dir.iterdir() if d.is_dir() and d.name.startswith("resume_")],
            reverse=True
        )
        
        return resume_dirs
    
    def list_resumes(self) -> list[dict]:
        """List all saved resumes with metadata.
        
        Returns:
            List of dictionaries with resume metadata:
            - path: Path to resume directory
            - folder_name: Name of the folder
            - json_path: Path to JSON file
            - pdf_path: Path to PDF file (if exists)
            - created_at: Creation timestamp from folder name
        """
        resume_dirs = self.get_resume_paths()
        resumes = []
        
        for resume_dir in resume_dirs:
            # Extract timestamp from folder name
            folder_name = resume_dir.name
            timestamp_str = folder_name.replace("resume_", "")
            
            try:
                created_at = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
            except ValueError:
                created_at = datetime.fromtimestamp(resume_dir.stat().st_mtime)
            
            # Find JSON and PDF files
            json_files = list(resume_dir.glob("*.json"))
            pdf_files = list(resume_dir.glob("*.pdf"))
            
            for json_file in json_files:
                # Find corresponding PDF
                pdf_file = None
                json_stem = json_file.stem
                for pdf in pdf_files:
                    if pdf.stem == json_stem:
                        pdf_file = pdf
                        break
                
                resumes.append({
                    "path": resume_dir,
                    "folder_name": folder_name,
                    "json_path": json_file,
                    "pdf_path": pdf_file,
                    "created_at": created_at,
                    "filename": json_stem,
                })
        
        return resumes
    
    def get_resume_by_job(self, job: JobPosting) -> Optional[Path]:
        """Get resume PDF path for a specific job.
        
        Args:
            job: Job posting to find resume for
            
        Returns:
            Path to PDF file if found, None otherwise
        """
        expected_filename = self._sanitize_filename(f"{job.company}_{job.title}")
        resume_dirs = self.get_resume_paths()
        
        # Search most recent first
        for resume_dir in resume_dirs:
            pdf_path = resume_dir / f"{expected_filename}.pdf"
            if pdf_path.exists():
                return pdf_path
        
        return None

