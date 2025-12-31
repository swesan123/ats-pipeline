"""Experience API routes."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import APIRouter, HTTPException
from typing import List
from backend.app.models.experience import (
    ExperienceCreateRequest,
    ExperienceUpdateRequest,
    ExperienceResponse,
    BulletRequest,
)
from src.storage.experience_library import ExperienceLibrary
from src.models.resume import ExperienceItem, Bullet

router = APIRouter()


@router.get("/experience", response_model=List[ExperienceResponse])
async def list_experience():
    """List all experience entries."""
    try:
        library = ExperienceLibrary()
        experience_items = library.get_all_experience()
        
        result = []
        for exp in experience_items:
            result.append(_experience_to_response(exp))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/experience", response_model=ExperienceResponse, status_code=201)
async def create_experience(request: ExperienceCreateRequest):
    """Create a new experience entry."""
    try:
        library = ExperienceLibrary()
        
        # Convert bullets
        bullets = [
            Bullet(text=b.text, skills=b.skills, evidence=b.evidence)
            for b in request.bullets
        ]
        
        experience = ExperienceItem(
            organization=request.organization,
            role=request.role,
            location=request.location,
            start_date=request.start_date,
            end_date=request.end_date,
            bullets=bullets,
        )
        
        library.add_experience(experience)
        
        return _experience_to_response(experience)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/experience/{organization}/{role}", response_model=ExperienceResponse)
async def update_experience(
    organization: str,
    role: str,
    request: ExperienceUpdateRequest,
):
    """Update an experience entry (identified by organization and role)."""
    try:
        library = ExperienceLibrary()
        experience = library.get_experience(organization, role)
        
        if not experience:
            raise HTTPException(status_code=404, detail="Experience not found")
        
        # Update fields
        if request.organization is not None:
            experience.organization = request.organization
        if request.role is not None:
            experience.role = request.role
        if request.location is not None:
            experience.location = request.location
        if request.start_date is not None:
            experience.start_date = request.start_date
        if request.end_date is not None:
            experience.end_date = request.end_date
        if request.bullets is not None:
            experience.bullets = [
                Bullet(text=b.text, skills=b.skills, evidence=b.evidence)
                for b in request.bullets
            ]
        
        library.add_experience(experience)  # This updates if organization+role matches
        
        return _experience_to_response(experience)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/experience/{organization}/{role}", status_code=204)
async def delete_experience(organization: str, role: str):
    """Delete an experience entry."""
    try:
        library = ExperienceLibrary()
        success = library.remove_experience(organization, role)
        
        if not success:
            raise HTTPException(status_code=404, detail="Experience not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _experience_to_response(experience: ExperienceItem) -> ExperienceResponse:
    """Convert ExperienceItem to ExperienceResponse."""
    return ExperienceResponse(
        organization=experience.organization,
        role=experience.role,
        location=experience.location,
        start_date=experience.start_date,
        end_date=experience.end_date,
        bullets=[
            BulletRequest(text=b.text, skills=b.skills, evidence=b.evidence)
            for b in experience.bullets
        ],
    )
