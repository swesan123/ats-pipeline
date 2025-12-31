"""Resume generation workflow API routes."""

import json
import sys
from pathlib import Path
from typing import Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.dependencies import get_db
from src.db.database import Database
from src.models.resume import Resume, Bullet
from src.compilation.resume_rewriter import ResumeRewriter
from src.matching.skill_matcher import SkillMatcher
from src.models.skills import SkillOntology, UserSkills

router = APIRouter()


class GenerateResumeRequest(BaseModel):
    """Request model for generating resume."""
    job_id: int
    rewrite_intent: Optional[str] = "emphasize_skills"


class CompleteResumeRequest(BaseModel):
    """Request model for completing resume generation."""
    job_id: int
    approved_bullets: Dict[str, int]  # bullet_id -> candidate_index


@router.post("/resume-generation/start")
async def start_resume_generation(
    request: GenerateResumeRequest,
    db: Database = Depends(get_db),
):
    """Start resume generation workflow for a job."""
    try:
        # Get job and resume
        job = db.get_job(request.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        resume = db.get_latest_resume()
        if not resume:
            raise HTTPException(status_code=404, detail="No resume found")
        
        # Get job match
        job_skills_data = db.get_job_skills(request.job_id)
        if not job_skills_data:
            raise HTTPException(status_code=400, detail="Job skills not found")
        
        if isinstance(job_skills_data, dict):
            from src.models.job import JobSkills
            job_skills = JobSkills.model_validate(job_skills_data)
        else:
            job_skills = job_skills_data
        
        # Match job
        matcher = SkillMatcher(SkillOntology())
        job_match = matcher.match_job(resume, job_skills)
        
        # Load user skills
        user_skills = None
        skills_file = Path("data/user_skills.json")
        if skills_file.exists():
            try:
                with open(skills_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    user_skills = UserSkills.model_validate(data)
            except Exception:
                pass
        
        # Generate variations
        rewriter = ResumeRewriter(user_skills=user_skills)
        variations = rewriter.generate_variations(
            resume,
            job_match,
            rewrite_intent=request.rewrite_intent or "emphasize_skills",
        )
        
        # Format response
        result = {}
        for bullet_id, (reasoning, candidates) in variations.items():
            result[bullet_id] = {
                "reasoning": {
                    "problem_identification": reasoning.problem_identification,
                    "analysis": reasoning.analysis,
                    "solution_approach": reasoning.solution_approach,
                    "evaluation": reasoning.evaluation,
                    "alternatives_considered": reasoning.alternatives_considered,
                    "confidence_score": reasoning.confidence_score,
                },
                "candidates": [
                    {
                        "text": c.text,
                        "composite_score": c.composite_score,
                        "risk_level": c.risk_level,
                        "score": c.score,
                        "diff_from_original": c.diff_from_original,
                        "justification": c.justification,
                        "rewrite_intent": c.rewrite_intent,
                    }
                    for c in candidates
                ],
            }
        
        return {
            "job_id": request.job_id,
            "resume_id": None,  # Will be set after completion
            "variations": result,
            "total_bullets": len(result),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume-generation/regenerate-bullet")
async def regenerate_bullet(
    request: GenerateResumeRequest,
    bullet_id: str = Query(..., description="ID of the bullet to regenerate"),
    db: Database = Depends(get_db),
):
    """Regenerate variations for a specific bullet with new rewrite intent."""
    try:
        # Get job and resume
        job = db.get_job(request.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        resume = db.get_latest_resume()
        if not resume:
            raise HTTPException(status_code=404, detail="No resume found")
        
        # Get job match
        job_skills_data = db.get_job_skills(request.job_id)
        if not job_skills_data:
            raise HTTPException(status_code=400, detail="Job skills not found")
        
        if isinstance(job_skills_data, dict):
            from src.models.job import JobSkills
            job_skills = JobSkills.model_validate(job_skills_data)
        else:
            job_skills = job_skills_data
        
        # Match job
        matcher = SkillMatcher(SkillOntology())
        job_match = matcher.match_job(resume, job_skills)
        
        # Load user skills
        user_skills = None
        skills_file = Path("data/user_skills.json")
        if skills_file.exists():
            try:
                with open(skills_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    user_skills = UserSkills.model_validate(data)
            except Exception:
                pass
        
        # Generate variations for specific bullet
        rewriter = ResumeRewriter(user_skills=user_skills)
        variations = rewriter.generate_variations(
            resume,
            job_match,
            rewrite_intent=request.rewrite_intent or "emphasize_skills",
        )
        
        if bullet_id not in variations:
            raise HTTPException(status_code=404, detail="Bullet not found")
        
        reasoning, candidates = variations[bullet_id]
        
        return {
            "bullet_id": bullet_id,
            "reasoning": {
                "problem_identification": reasoning.problem_identification,
                "analysis": reasoning.analysis,
                "solution_approach": reasoning.solution_approach,
                "evaluation": reasoning.evaluation,
                "alternatives_considered": reasoning.alternatives_considered,
                "confidence_score": reasoning.confidence_score,
            },
            "candidates": [
                {
                    "text": c.text,
                    "composite_score": c.composite_score,
                    "risk_level": c.risk_level,
                    "score": c.score,
                    "diff_from_original": c.diff_from_original,
                    "justification": c.justification,
                    "rewrite_intent": c.rewrite_intent,
                }
                for c in candidates
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume-generation/complete")
async def complete_resume_generation(
    request: CompleteResumeRequest,
    db: Database = Depends(get_db),
):
    """Complete resume generation by applying approved bullets."""
    try:
        # Get job and resume
        job = db.get_job(request.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        resume = db.get_latest_resume()
        if not resume:
            raise HTTPException(status_code=404, detail="No resume found")
        
        # Get job match and generate variations again to get the candidates
        job_skills_data = db.get_job_skills(request.job_id)
        if not job_skills_data:
            raise HTTPException(status_code=400, detail="Job skills not found")
        
        if isinstance(job_skills_data, dict):
            from src.models.job import JobSkills
            job_skills = JobSkills.model_validate(job_skills_data)
        else:
            job_skills = job_skills_data
        
        matcher = SkillMatcher(SkillOntology())
        job_match = matcher.match_job(resume, job_skills)
        
        # Load user skills
        user_skills = None
        skills_file = Path("data/user_skills.json")
        if skills_file.exists():
            try:
                with open(skills_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    user_skills = UserSkills.model_validate(data)
            except Exception:
                pass
        
        # Generate variations to get candidates
        rewriter = ResumeRewriter(user_skills=user_skills)
        variations = rewriter.generate_variations(
            resume,
            job_match,
            rewrite_intent="emphasize_skills",
        )
        
        # Apply approved bullets
        updated_resume = resume.model_copy(deep=True)
        bullet_id = 0
        
        # Apply changes to experience bullets
        for exp in updated_resume.experience:
            for i, bullet in enumerate(exp.bullets):
                bullet_key = f"exp_{exp.organization}_{bullet_id}"
                if bullet_key in request.approved_bullets:
                    candidate_idx = request.approved_bullets[bullet_key]
                    if bullet_key in variations:
                        reasoning, candidates = variations[bullet_key]
                        if 0 <= candidate_idx < len(candidates):
                            selected_candidate = candidates[candidate_idx]
                            exp.bullets[i] = Bullet(
                                text=selected_candidate.text,
                                skills=bullet.skills.copy() if bullet.skills else [],
                                evidence=bullet.evidence,
                                history=bullet.history.copy() if bullet.history else [],
                            )
                bullet_id += 1
        
        # Apply changes to project bullets
        bullet_id = 0
        for proj in updated_resume.projects:
            for i, bullet in enumerate(proj.bullets):
                bullet_key = f"proj_{proj.name}_{bullet_id}"
                if bullet_key in request.approved_bullets:
                    candidate_idx = request.approved_bullets[bullet_key]
                    if bullet_key in variations:
                        reasoning, candidates = variations[bullet_key]
                        if 0 <= candidate_idx < len(candidates):
                            selected_candidate = candidates[candidate_idx]
                            proj.bullets[i] = Bullet(
                                text=selected_candidate.text,
                                skills=bullet.skills.copy() if bullet.skills else [],
                                evidence=bullet.evidence,
                                history=bullet.history.copy() if bullet.history else [],
                            )
                bullet_id += 1
        
        # Save rewritten resume
        resume_id = db.save_resume(
            updated_resume,
            job_id=request.job_id,
            is_customized=True,
        )
        
        return {
            "resume_id": resume_id,
            "resume": updated_resume.model_dump(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
