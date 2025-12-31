"""Bullet generation API routes."""

import sys
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.extractors.bullet_formatter import BulletFormatter

router = APIRouter()


class BulletGenerationRequest(BaseModel):
    """Request model for bullet generation."""
    project_name: str
    description: str
    tech_stack: List[str] = []
    context: Optional[str] = None


class BulletGenerationResponse(BaseModel):
    """Response model for bullet generation."""
    bullets: List[str]
    reasoning: Optional[str] = None


@router.post("/bullets/generate", response_model=BulletGenerationResponse)
async def generate_bullets(request: BulletGenerationRequest):
    """Generate formatted resume bullets for a project."""
    try:
        formatter = BulletFormatter()
        
        # Use description as raw bullets if no context provided
        raw_bullets = [request.description]
        if request.context:
            # Split context into potential bullets
            raw_bullets = [s.strip() for s in request.context.split('\n') if s.strip()]
        
        formatted_bullets = formatter.format_bullets(
            raw_bullets=raw_bullets,
            project_name=request.project_name,
            tech_stack=request.tech_stack,
            description=request.description,
        )
        
        return BulletGenerationResponse(
            bullets=formatted_bullets,
            reasoning="Bullets formatted using AI to match professional resume standards.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
