"""Resumes API routes."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Optional
from fastapi.responses import FileResponse, Response
from backend.app.dependencies import get_db
from backend.app.models.resumes import ResumeResponse, ResumeRewriteRequest
from src.db.database import Database
from src.models.resume import Resume

router = APIRouter()


@router.get("/resumes", response_model=List[ResumeResponse])
async def list_resumes(db: Database = Depends(get_db)):
    """List all resumes."""
    try:
        # Get all resumes from database
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT id, version, file_path, job_id, is_customized, updated_at
            FROM resumes
            ORDER BY updated_at DESC
        """)
        
        result = []
        for row in cursor.fetchall():
            result.append(ResumeResponse(
                id=row["id"],
                version=str(row["version"]),  # Convert int to string
                file_path=row["file_path"],
                job_id=row["job_id"],
                is_customized=bool(row["is_customized"]),
                updated_at=row["updated_at"],
            ))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resumes/template")
async def get_template():
    """Get the current template content."""
    try:
        from pathlib import Path
        
        template_path = Path("templates/resume.tex")
        if not template_path.exists():
            raise HTTPException(status_code=404, detail="Template not found")
        
        content = template_path.read_text(encoding='utf-8')
        stats = template_path.stat()
        
        return {
            "content": content,
            "path": str(template_path),
            "last_modified": stats.st_mtime,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resumes/template/preview-pdf")
async def preview_template_pdf():
    """Preview the template as a PDF by parsing it and rendering."""
    try:
        from pathlib import Path
        from src.parsers.latex_resume import LaTeXResumeParser
        from src.rendering.latex_renderer import LaTeXRenderer
        import tempfile
        
        template_path = Path("templates/resume.tex")
        if not template_path.exists():
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Parse template to get Resume object
        parser = LaTeXResumeParser.from_file(template_path)
        resume = parser.parse()
        
        # Render to PDF
        temp_pdf = Path(tempfile.gettempdir()) / f"template_preview_{Path().cwd().name}.pdf"
        renderer = LaTeXRenderer(template_path=template_path)
        renderer.render_pdf(resume, temp_pdf)
        
        # Return file
        return FileResponse(
            path=str(temp_pdf),
            filename="template_preview.pdf",
            media_type="application/pdf",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resumes/{resume_id}", response_model=dict)
async def get_resume(
    resume_id: int,
    db: Database = Depends(get_db),
):
    """Get a specific resume by ID."""
    try:
        resume = db.get_resume(resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        return resume.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resumes", response_model=ResumeResponse, status_code=201)
async def save_resume(
    resume: dict,
    db: Database = Depends(get_db),
    job_id: Optional[int] = None,
    is_customized: bool = False,
):
    """Save a resume."""
    try:
        resume_obj = Resume.model_validate(resume)
        resume_id = db.save_resume(resume_obj, job_id=job_id, is_customized=is_customized)
        
        # Get saved resume
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT id, version, file_path, job_id, is_customized, updated_at
            FROM resumes WHERE id = ?
        """, (resume_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Resume not found after creation")
        
        return ResumeResponse(
            id=row["id"],
            version=str(row["version"]),  # Convert int to string
            file_path=row["file_path"],
            job_id=row["job_id"],
            is_customized=bool(row["is_customized"]),
            updated_at=row["updated_at"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resumes/{resume_id}/rewrite")
async def rewrite_resume(
    resume_id: int,
    request: ResumeRewriteRequest,
    db: Database = Depends(get_db),
):
    """Rewrite a resume for a specific job."""
    try:
        from src.compilation.resume_rewriter import ResumeRewriter
        
        resume = db.get_resume(resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        job = db.get_job_full(request.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get job posting
        from src.models.job import JobPosting
        job_posting = db.get_job(request.job_id)
        
        # Rewrite resume
        rewriter = ResumeRewriter()
        rewritten_resume = rewriter.rewrite_resume(
            resume,
            job_posting,
            rewrite_intent=request.rewrite_intent or "emphasize_skills",
        )
        
        # Save rewritten resume
        new_resume_id = db.save_resume(
            rewritten_resume,
            job_id=request.job_id,
            is_customized=True,
        )
        
        return {"resume_id": new_resume_id, "resume": rewritten_resume.model_dump()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resumes/{resume_id}/render-pdf")
async def render_pdf_get(
    resume_id: int,
    db: Database = Depends(get_db),
):
    """Render a resume to PDF (GET endpoint for iframe/preview)."""
    try:
        from src.rendering.latex_renderer import LaTeXRenderer
        import tempfile
        from pathlib import Path
        
        resume = db.get_resume(resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Get template path
        template_path = Path("templates/resume.tex")
        if not template_path.exists():
            raise HTTPException(status_code=404, detail="Resume template not found")
        
        # Render PDF
        temp_pdf = Path(tempfile.gettempdir()) / f"resume_{resume_id}_{Path().cwd().name}.pdf"
        renderer = LaTeXRenderer(template_path=template_path)
        renderer.render_pdf(resume, temp_pdf)
        
        # Read PDF content
        pdf_content = temp_pdf.read_bytes()
        
        # Return PDF with inline content disposition for preview
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="resume_{resume_id}.pdf"',
                "Content-Type": "application/pdf",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resumes/{resume_id}/render-pdf")
async def render_pdf(
    resume_id: int,
    db: Database = Depends(get_db),
):
    """Render a resume to PDF (POST endpoint for download)."""
    try:
        from src.rendering.latex_renderer import LaTeXRenderer
        import tempfile
        from pathlib import Path
        
        resume = db.get_resume(resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Get template path
        template_path = Path("templates/resume.tex")
        if not template_path.exists():
            raise HTTPException(status_code=404, detail="Resume template not found")
        
        # Render PDF
        temp_pdf = Path(tempfile.gettempdir()) / f"resume_{resume_id}_{Path().cwd().name}.pdf"
        renderer = LaTeXRenderer(template_path=template_path)
        renderer.render_pdf(resume, temp_pdf)
        
        # Return file
        return FileResponse(
            path=str(temp_pdf),
            filename=f"resume_{resume_id}.pdf",
            media_type="application/pdf",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resumes/template/upload")
async def upload_template(file: UploadFile = File(...)):
    """Upload a LaTeX resume template."""
    try:
        from pathlib import Path
        
        template_path = Path("templates/resume.tex")
        template_path.parent.mkdir(exist_ok=True, parents=True)
        content = await file.read()
        template_path.write_bytes(content)
        
        return {"message": "Template uploaded successfully", "path": str(template_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resumes/template/parse")
async def parse_template():
    """Parse the uploaded template and update libraries."""
    try:
        from pathlib import Path
        import json
        from src.parsers.latex_resume import LaTeXResumeParser
        from src.storage.experience_library import ExperienceLibrary
        from src.projects.project_library import ProjectLibrary
        from src.models.skills import UserSkills, UserSkill
        
        template_path = Path("templates/resume.tex")
        if not template_path.exists():
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Parse template
        parser = LaTeXResumeParser.from_file(template_path)
        resume = parser.parse()
        
        # Get existing counts
        exp_library = ExperienceLibrary()
        existing_exp = exp_library.get_all_experience()
        proj_library = ProjectLibrary()
        existing_proj = proj_library.get_all_projects()
        
        # Append experience
        exp_added = 0
        exp_updated = 0
        for exp_item in resume.experience:
            exists = any(
                e.organization == exp_item.organization and e.role == exp_item.role
                for e in existing_exp
            )
            exp_library.add_experience(exp_item)
            if exists:
                exp_updated += 1
            else:
                exp_added += 1
        
        # Append projects
        proj_added = 0
        proj_updated = 0
        for proj in resume.projects:
            exists = any(p.name == proj.name for p in existing_proj)
            proj_library.add_project(proj)
            if exists:
                proj_updated += 1
            else:
                proj_added += 1
        
        # Append skills
        skills_file = Path("data/user_skills.json")
        user_skills = UserSkills(skills=[])
        if skills_file.exists():
            try:
                with open(skills_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    user_skills = UserSkills.model_validate(data)
            except:
                pass
        
        skill_count = 0
        for category, skill_list in resume.skills.items():
            for skill_name in skill_list:
                existing = next((s for s in user_skills.skills if s.name.lower() == skill_name.lower()), None)
                if not existing:
                    new_skill = UserSkill(
                        name=skill_name,
                        category=category,
                        projects=[]
                    )
                    user_skills.skills.append(new_skill)
                    skill_count += 1
        
        # Save updated skills
        skills_file.parent.mkdir(exist_ok=True, parents=True)
        with open(skills_file, 'w', encoding='utf-8') as f:
            json.dump(user_skills.model_dump(), f, indent=2, default=str)
        
        # Save to resume.json
        resume_json_path = Path("data/resume.json")
        resume_json_path.parent.mkdir(exist_ok=True, parents=True)
        with open(resume_json_path, 'w', encoding='utf-8') as f:
            json.dump(resume.model_dump(), f, indent=2, default=str)
        
        return {
            "message": "Template parsed successfully",
            "resume": resume.model_dump(),
            "summary": {
                "experience_added": exp_added,
                "experience_updated": exp_updated,
                "projects_added": proj_added,
                "projects_updated": proj_updated,
                "skills_added": skill_count,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
