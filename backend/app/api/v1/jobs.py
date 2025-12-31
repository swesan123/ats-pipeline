"""Jobs API routes."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from backend.app.dependencies import get_db
from backend.app.models.jobs import (
    JobCreateRequest,
    JobUpdateRequest,
    JobResponse,
    JobSkillsResponse,
    JobMatchResponse,
    ExtractSkillsRequest,
)
from src.db.database import Database
from src.extractors.job_skills import JobSkillExtractor
from src.extractors.job_url_scraper import JobURLScraper
from src.models.job import JobPosting
from src.gui.job_input import _extract_job_info_from_text, _save_job_from_text

router = APIRouter()


@router.get("/jobs", response_model=List[JobResponse])
async def list_jobs(
    db: Database = Depends(get_db),
    status: Optional[str] = None,
):
    """List all jobs, optionally filtered by status."""
    try:
        jobs = db.list_jobs()
        
        # Filter by status if provided
        if status:
            jobs = [j for j in jobs if j.get("status") == status]
        
        # Convert to response models
        result = []
        for job in jobs:
            job_response = _job_dict_to_response(job, db)
            result.append(job_response)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(
    request: JobCreateRequest,
    db: Database = Depends(get_db),
):
    """Create a new job from URL or description."""
    try:
        if request.url:
            # Extract from URL
            scraper = JobURLScraper()
            job_data = scraper.extract_job_content(request.url)
            
            if not job_data or not job_data.get('description'):
                raise HTTPException(status_code=400, detail="Could not extract job content from URL")
            
            job_posting = JobPosting(
                company=job_data.get('company', 'Unknown'),
                title=job_data.get('title', 'Unknown'),
                location=job_data.get('location'),
                description=job_data.get('description', ''),
                source_url=job_data.get('source_url', request.url),
            )
            
            # Extract skills
            extractor = JobSkillExtractor()
            job_skills = extractor.extract_skills(job_posting)
            
            # Save to database
            job_id = db.save_job(job_posting, job_skills=job_skills, status=request.status)
        elif request.description:
            # Extract from text
            job_id = _save_job_from_text(
                db,
                request.description,
                source_url=None,
                manual_title=request.title,
                manual_company=request.company,
                status=request.status,
            )
        else:
            raise HTTPException(status_code=400, detail="Either URL or description must be provided")
        
        # Get the created job
        job = db.get_job_full(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found after creation")
        
        return _job_dict_to_response(job, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: Database = Depends(get_db),
):
    """Get a specific job by ID."""
    try:
        job = db.get_job_full(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return _job_dict_to_response(job, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/jobs/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    request: JobUpdateRequest,
    db: Database = Depends(get_db),
):
    """Update a job."""
    try:
        job = db.get_job_full(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Update job fields
        if request.status is not None:
            db.update_job_status(job_id, request.status)
        
        # Update other fields via direct SQL (since Database doesn't have general update method)
        if request.notes is not None or request.contact_name is not None or request.date_applied is not None:
            cursor = db.conn.cursor()
            updates = []
            params = []
            
            if request.notes is not None:
                updates.append("notes = ?")
                params.append(request.notes)
            if request.contact_name is not None:
                updates.append("contact_name = ?")
                params.append(request.contact_name)
            if request.date_applied is not None:
                updates.append("date_applied = ?")
                params.append(request.date_applied)
            
            if updates:
                params.append(job_id)
                cursor.execute(
                    f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?",
                    params
                )
                db.conn.commit()
        
        # Get updated job
        updated_job = db.get_job_full(job_id)
        return _job_dict_to_response(updated_job, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(
    job_id: int,
    db: Database = Depends(get_db),
):
    """Delete a job."""
    try:
        job = db.get_job_full(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        db.delete_job(job_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/extract-skills", response_model=JobSkillsResponse)
async def extract_skills(request: ExtractSkillsRequest):
    """Extract skills from a job URL or description."""
    try:
        if request.url:
            scraper = JobURLScraper()
            job_data = scraper.extract_job_content(request.url)
            
            if not job_data or not job_data.get('description'):
                raise HTTPException(status_code=400, detail="Could not extract job content from URL")
            
            job_posting = JobPosting(
                company=job_data.get('company', 'Unknown'),
                title=job_data.get('title', 'Unknown'),
                location=job_data.get('location'),
                description=job_data.get('description', ''),
                source_url=job_data.get('source_url', request.url),
            )
        elif request.description:
            title, company = _extract_job_info_from_text(request.description)
            job_posting = JobPosting(
                company=company,
                title=title,
                description=request.description,
            )
        else:
            raise HTTPException(status_code=400, detail="Either URL or description must be provided")
        
        extractor = JobSkillExtractor()
        job_skills = extractor.extract_skills(job_posting)
        
        return JobSkillsResponse(
            required_skills=job_skills.required_skills,
            preferred_skills=job_skills.preferred_skills,
            soft_skills=job_skills.soft_skills,
            seniority_indicators=job_skills.seniority_indicators,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/match", response_model=JobMatchResponse)
async def match_job(
    job_id: int,
    db: Database = Depends(get_db),
):
    """Match a job with the latest resume."""
    try:
        from src.matching.skill_matcher import SkillMatcher
        from src.models.skills import SkillOntology
        
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        resume = db.get_latest_resume()
        if not resume:
            raise HTTPException(status_code=404, detail="No resume found")
        
        # Get job skills
        job_skills_data = db.get_job_skills(job_id)
        if not job_skills_data:
            raise HTTPException(status_code=400, detail="Job skills not found")
        
        from src.models.job import JobSkills
        # Handle both dict and JobSkills object
        if isinstance(job_skills_data, dict):
            job_skills = JobSkills.model_validate(job_skills_data)
        else:
            job_skills = job_skills_data
        
        # Match
        matcher = SkillMatcher(SkillOntology())
        match = matcher.match_job(resume, job_skills)
        
        return JobMatchResponse(
            fit_score=match.fit_score,
            matched_skills=match.matching_skills,  # JobMatch uses matching_skills, not matched_skills
            missing_skills=match.missing_skills,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/cover-letter")
async def generate_cover_letter(
    job_id: int,
    db: Database = Depends(get_db),
):
    """Generate a cover letter for a job."""
    try:
        from src.generators.cover_letter_generator import CoverLetterGenerator
        
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        resume = db.get_latest_resume()
        if not resume:
            raise HTTPException(status_code=404, detail="No resume found")
        
        generator = CoverLetterGenerator()
        cover_letter = generator.generate(resume, job)
        
        return {"cover_letter": cover_letter}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _job_dict_to_response(job: dict, db: Optional[Database] = None) -> JobResponse:
    """Convert job dict to JobResponse model."""
    # Get job skills if available
    job_skills = None
    job_id = job.get("id")
    if job_id and db:
        try:
            skills = db.get_job_skills(job_id)
            if skills:
                # Handle both JobSkills object and dict
                if isinstance(skills, dict):
                    job_skills = JobSkillsResponse(
                        required_skills=skills.get("required_skills", []),
                        preferred_skills=skills.get("preferred_skills", []),
                        soft_skills=skills.get("soft_skills", []),
                        seniority_indicators=skills.get("seniority_indicators", []),
                    )
                else:
                    job_skills = JobSkillsResponse(
                        required_skills=skills.required_skills,
                        preferred_skills=skills.preferred_skills,
                        soft_skills=skills.soft_skills,
                        seniority_indicators=skills.seniority_indicators,
                    )
        except Exception:
            pass
    
    # Get match if available (would need to query job_matches table)
    match = None
    
    # Check if job has resumes
    has_resume = False
    latest_resume_id = None
    if job_id and db:
        try:
            resumes = db.get_resumes_by_job_id(job_id)
            if resumes:
                has_resume = True
                latest_resume_id = resumes[0]["id"]  # Most recent resume
        except Exception:
            pass
    
    return JobResponse(
        id=job["id"],
        company=job.get("company", "Unknown"),
        title=job.get("title", "Unknown"),
        location=job.get("location"),
        description=job.get("description", ""),
        source_url=job.get("source_url"),
        status=job.get("status"),
        notes=job.get("notes"),
        contact_name=job.get("contact_name"),
        date_applied=job.get("date_applied"),
        date_added=job.get("created_at"),
        job_skills=job_skills,
        match=match,
        has_resume=has_resume,
        latest_resume_id=latest_resume_id,
    )
