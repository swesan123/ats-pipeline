"""Skills API routes."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import APIRouter, HTTPException
from backend.app.models.skills import UserSkillsRequest, UserSkillsResponse, UserSkillRequest, SkillEvidenceRequest
from src.models.skills import UserSkills, UserSkill, SkillEvidence
import json

router = APIRouter()


def _convert_skills_to_response(user_skills: UserSkills) -> UserSkillsResponse:
    """Convert UserSkills model to UserSkillsResponse.
    
    Migrates old 'projects' field to 'evidence_sources' for backward compatibility.
    """
    skills_response = []
    for skill in user_skills.skills:
        # Start with existing evidence sources
        evidence_sources = [
            SkillEvidenceRequest(
                source_type=ev.source_type,
                source_name=ev.source_name,
                evidence_text=ev.evidence_text,
            )
            for ev in skill.evidence_sources
        ]
        
        # Migrate old 'projects' field to evidence_sources if they don't already exist
        for project_name in skill.projects:
            # Check if project already exists in evidence_sources
            if not any(ev.source_type == 'project' and ev.source_name == project_name 
                      for ev in evidence_sources):
                evidence_sources.append(
                    SkillEvidenceRequest(
                        source_type='project',
                        source_name=project_name,
                        evidence_text=None,
                    )
                )
        
        skills_response.append(
            UserSkillRequest(
                name=skill.name,
                category=skill.category,
                projects=[],  # Empty - migrated to evidence_sources
                evidence_sources=evidence_sources,
            )
        )
    return UserSkillsResponse(skills=skills_response)


@router.get("/skills", response_model=UserSkillsResponse)
async def get_skills():
    """Get user skills."""
    try:
        skills_file = Path("data/user_skills.json")
        
        if not skills_file.exists():
            return UserSkillsResponse(skills=[])
        
        with open(skills_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        user_skills = UserSkills.model_validate(data)
        return _convert_skills_to_response(user_skills)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/skills", response_model=UserSkillsResponse)
async def update_skills(request: UserSkillsRequest):
    """Update user skills."""
    try:
        # Convert request to UserSkills model
        # Migrate old 'projects' field to 'evidence_sources'
        user_skills_list = []
        for skill in request.skills:
            # Start with existing evidence sources
            evidence_sources = [
                SkillEvidence(
                    source_type=ev.source_type,
                    source_name=ev.source_name,
                    evidence_text=ev.evidence_text,
                )
                for ev in skill.evidence_sources
            ]
            
            # Migrate old 'projects' field to evidence_sources if they don't already exist
            for project_name in (skill.projects or []):
                if not any(ev.source_type == 'project' and ev.source_name == project_name 
                          for ev in evidence_sources):
                    evidence_sources.append(
                        SkillEvidence(
                            source_type='project',
                            source_name=project_name,
                            evidence_text=None,
                        )
                    )
            
            user_skills_list.append(
                UserSkill(
                    name=skill.name,
                    category=skill.category,
                    projects=[],  # Empty - migrated to evidence_sources
                    evidence_sources=evidence_sources,
                )
            )
        
        user_skills = UserSkills(skills=user_skills_list)
        
        # Save to file
        skills_file = Path("data/user_skills.json")
        skills_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(skills_file, 'w', encoding='utf-8') as f:
            json.dump(user_skills.model_dump(), f, indent=2, default=str)
        
        return _convert_skills_to_response(user_skills)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/skills/add", response_model=UserSkillsResponse)
async def add_skill(request: UserSkillRequest):
    """Add a single skill."""
    try:
        skills_file = Path("data/user_skills.json")
        
        # Load existing skills
        user_skills = UserSkills(skills=[])
        if skills_file.exists():
            try:
                with open(skills_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                user_skills = UserSkills.model_validate(data)
            except:
                pass
        
        # Check if skill already exists
        existing_skill = next(
            (s for s in user_skills.skills if s.name.lower() == request.name.lower()),
            None
        )
        
        if existing_skill:
            raise HTTPException(status_code=400, detail=f"Skill '{request.name}' already exists")
        
        # Add new skill - migrate old 'projects' field to 'evidence_sources'
        evidence_sources = [
            SkillEvidence(
                source_type=ev.source_type,
                source_name=ev.source_name,
                evidence_text=ev.evidence_text,
            )
            for ev in (request.evidence_sources or [])
        ]
        
        # Migrate old 'projects' field to evidence_sources if they don't already exist
        for project_name in (request.projects or []):
            if not any(ev.source_type == 'project' and ev.source_name == project_name 
                      for ev in evidence_sources):
                evidence_sources.append(
                    SkillEvidence(
                        source_type='project',
                        source_name=project_name,
                        evidence_text=None,
                    )
                )
        
        new_skill = UserSkill(
            name=request.name,
            category=request.category,
            projects=[],  # Empty - migrated to evidence_sources
            evidence_sources=evidence_sources,
        )
        
        user_skills.skills.append(new_skill)
        
        # Save to file
        skills_file.parent.mkdir(parents=True, exist_ok=True)
        with open(skills_file, 'w', encoding='utf-8') as f:
            json.dump(user_skills.model_dump(), f, indent=2, default=str)
        
        return _convert_skills_to_response(user_skills)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/skills/{skill_name}", response_model=UserSkillsResponse)
async def delete_skill(skill_name: str):
    """Delete a skill by name."""
    try:
        skills_file = Path("data/user_skills.json")
        
        if not skills_file.exists():
            raise HTTPException(status_code=404, detail="No skills found")
        
        # Load existing skills
        with open(skills_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        user_skills = UserSkills.model_validate(data)
        
        # Remove skill
        original_count = len(user_skills.skills)
        user_skills.skills = [
            s for s in user_skills.skills 
            if s.name.lower() != skill_name.lower()
        ]
        
        if len(user_skills.skills) == original_count:
            raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
        
        # Save to file
        with open(skills_file, 'w', encoding='utf-8') as f:
            json.dump(user_skills.model_dump(), f, indent=2, default=str)
        
        return _convert_skills_to_response(user_skills)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
