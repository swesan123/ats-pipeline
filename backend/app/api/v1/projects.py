"""Projects API routes."""

import json
import sys
from pathlib import Path
from typing import List

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import APIRouter, HTTPException
from backend.app.models.projects import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    GitHubImportRequest,
    BulletRequest,
)
from src.projects.project_library import ProjectLibrary
from src.models.resume import ProjectItem, Bullet
from src.extractors.github_repo_extractor import GitHubRepoExtractor
from src.models.skills import UserSkills, UserSkill, SkillEvidence

router = APIRouter()


async def _add_tech_stack_skills_to_user_skills(tech_stack: List[str], project_name: str):
    """Add tech stack skills to user skills list.
    
    Args:
        tech_stack: List of technology names
        project_name: Name of the project (used as evidence source)
    """
    if not tech_stack:
        return
    
    try:
        # Import AI classification function
        from backend.app.api.v1.ai_skills import classify_skill_category
        
        skills_file = Path("data/user_skills.json")
        
        # Load existing skills
        user_skills = UserSkills(skills=[])
        if skills_file.exists():
            try:
                with open(skills_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                user_skills = UserSkills.model_validate(data)
            except Exception:
                pass
        
        # Get existing skill names (case-insensitive)
        existing_skill_names = {s.name.lower() for s in user_skills.skills}
        
        # Add each tech stack skill
        for tech in tech_stack:
            tech_clean = tech.strip()
            if not tech_clean:
                continue
            
            # Skip if skill already exists
            if tech_clean.lower() in existing_skill_names:
                # Update evidence source if project not already linked
                existing_skill = next(
                    (s for s in user_skills.skills if s.name.lower() == tech_clean.lower()),
                    None
                )
                if existing_skill:
                    # Check if project is already in evidence sources
                    project_in_evidence = any(
                        ev.source_type == 'project' and ev.source_name == project_name
                        for ev in existing_skill.evidence_sources
                    )
                    if not project_in_evidence:
                        existing_skill.evidence_sources.append(
                            SkillEvidence(
                                source_type='project',
                                source_name=project_name,
                                evidence_text=None,
                            )
                        )
                continue
            
            # Classify skill category using AI
            try:
                category = await classify_skill_category(tech_clean)
            except Exception as e:
                # Fallback to heuristic if classification fails
                from backend.app.api.v1.ai_skills import _classify_skill_heuristic
                category = _classify_skill_heuristic(tech_clean)
            
            # Create new skill with project as evidence
            new_skill = UserSkill(
                name=tech_clean,
                category=category,
                projects=[],  # Deprecated, use evidence_sources
                evidence_sources=[
                    SkillEvidence(
                        source_type='project',
                        source_name=project_name,
                        evidence_text=None,
                    )
                ],
            )
            
            user_skills.skills.append(new_skill)
            existing_skill_names.add(tech_clean.lower())
        
        # Save updated skills
        skills_file.parent.mkdir(parents=True, exist_ok=True)
        with open(skills_file, 'w', encoding='utf-8') as f:
            json.dump(user_skills.model_dump(), f, indent=2, default=str)
            
    except Exception as e:
        # Don't fail project creation if skill addition fails
        # Just log the error (could use proper logging in production)
        print(f"Warning: Failed to add tech stack skills to user skills: {e}")


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects():
    """List all projects in the library."""
    try:
        library = ProjectLibrary()
        projects = library.get_all_projects()
        
        result = []
        for project in projects:
            result.append(_project_to_response(project))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(request: ProjectCreateRequest):
    """Create a new project (manual entry)."""
    try:
        library = ProjectLibrary()
        
        # Convert bullets
        bullets = [
            Bullet(text=b.text, skills=b.skills, evidence=b.evidence)
            for b in request.bullets
        ]
        
        project = ProjectItem(
            name=request.name,
            tech_stack=request.tech_stack,
            start_date=request.start_date,
            end_date=request.end_date,
            bullets=bullets,
        )
        
        library.add_project(project)
        
        # Auto-add tech stack skills to user skills
        await _add_tech_stack_skills_to_user_skills(project.tech_stack, project.name)
        
        return _project_to_response(project)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/github", response_model=ProjectResponse, status_code=201)
async def import_from_github(request: GitHubImportRequest):
    """Import a project from GitHub repository."""
    try:
        extractor = GitHubRepoExtractor()
        project = extractor.extract_project(request.url)
        
        library = ProjectLibrary()
        library.add_project(project)
        
        # Auto-add tech stack skills to user skills
        await _add_tech_stack_skills_to_user_skills(project.tech_stack, project.name)
        
        return _project_to_response(project)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/projects/{project_name}", response_model=ProjectResponse)
async def update_project(project_name: str, request: ProjectUpdateRequest):
    """Update a project by name."""
    try:
        library = ProjectLibrary()
        project = library.get_project(project_name)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update fields
        if request.name is not None:
            project.name = request.name
        if request.tech_stack is not None:
            project.tech_stack = request.tech_stack
        if request.start_date is not None:
            project.start_date = request.start_date
        if request.end_date is not None:
            project.end_date = request.end_date
        if request.bullets is not None:
            project.bullets = [
                Bullet(text=b.text, skills=b.skills, evidence=b.evidence)
                for b in request.bullets
            ]
        
        library.add_project(project)  # This updates if name matches
        
        # Auto-add tech stack skills to user skills
        # Use updated project name if it was changed
        final_project_name = project.name
        final_tech_stack = project.tech_stack
        await _add_tech_stack_skills_to_user_skills(final_tech_stack, final_project_name)
        
        return _project_to_response(project)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project_name}", status_code=204)
async def delete_project(project_name: str):
    """Delete a project by name."""
    try:
        library = ProjectLibrary()
        success = library.remove_project(project_name)
        
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _project_to_response(project: ProjectItem) -> ProjectResponse:
    """Convert ProjectItem to ProjectResponse."""
    return ProjectResponse(
        name=project.name,
        tech_stack=project.tech_stack,
        start_date=project.start_date,
        end_date=project.end_date,
        bullets=[
            BulletRequest(text=b.text, skills=b.skills, evidence=b.evidence)
            for b in project.bullets
        ],
    )
