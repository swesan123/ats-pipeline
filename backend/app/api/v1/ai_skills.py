"""AI skill suggestions API routes."""

import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

router = APIRouter()


class SkillSuggestionRequest(BaseModel):
    """Request model for AI skill suggestions."""
    job_description: str
    current_skills: Optional[List[str]] = []


class SkillSuggestionResponse(BaseModel):
    """Response model for AI skill suggestions."""
    suggested_skills: List[str]
    reasoning: str
    categorized_skills: Optional[List[dict]] = None  # List of {skill: str, category: str}


class SkillCategoryRequest(BaseModel):
    """Request model for skill category classification."""
    skill_name: str


@router.post("/skills/ai-suggestions", response_model=SkillSuggestionResponse)
async def suggest_skills(request: SkillSuggestionRequest):
    """Get AI-powered skill suggestions based on job description."""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500, detail="OpenAI API key not configured"
            )
        
        client = OpenAI(api_key=api_key)
        
        prompt = f"""Analyze this job description and suggest skills that would be valuable for this role.
Focus on technical skills, tools, frameworks, and technologies mentioned or implied.

Job Description:
{request.job_description}

Current Skills (user already has these):
{', '.join(request.current_skills) if request.current_skills else 'None listed'}

Provide:
1. A list of 5-10 specific, relevant skills that would strengthen a candidate's profile
2. Brief reasoning for why each skill is important

Format as JSON:
{{
    "suggested_skills": ["skill1", "skill2", ...],
    "reasoning": "Brief explanation of why these skills are important for this role"
}}

Focus on:
- Skills explicitly mentioned in the job description
- Related technologies/frameworks that are commonly used together
- Industry-standard tools for this type of role
- Skills that complement the user's current skillset
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a career advisor helping job seekers identify valuable skills for their target roles. Provide specific, actionable skill suggestions.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Classify each suggested skill into a category
        suggested_skills = result.get("suggested_skills", [])
        categorized_skills = []
        
        for skill in suggested_skills:
            category = await classify_skill_category(skill)
            categorized_skills.append({
                "skill": skill,
                "category": category
            })
        
        return SkillSuggestionResponse(
            suggested_skills=suggested_skills,
            reasoning=result.get("reasoning", ""),
            categorized_skills=categorized_skills,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def classify_skill_category(skill_name: str) -> str:
    """Classify a skill into the appropriate category using AI."""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Fallback to simple heuristics if API key not available
            return _classify_skill_heuristic(skill_name)
        
        client = OpenAI(api_key=api_key)
        
        categories = ["Languages", "ML/AI", "Mobile/Web", "Backend/DB", "DevOps"]
        
        prompt = f"""Classify the following skill into one of these categories:
- Languages: Programming languages (Python, Java, JavaScript, TypeScript, C, C++, Go, Rust, etc.)
- ML/AI: Machine learning and AI frameworks/tools (TensorFlow, PyTorch, scikit-learn, NumPy, pandas, etc.)
- Mobile/Web: Frontend and mobile frameworks (React, React Native, Vue, Angular, Flutter, etc.)
- Backend/DB: Backend frameworks and databases (Django, Flask, Node.js, PostgreSQL, MongoDB, Redis, etc.)
- DevOps: Infrastructure and deployment tools (Docker, Kubernetes, AWS, CI/CD tools, etc.)

Skill to classify: {skill_name}

Respond with ONLY the category name (one of: Languages, ML/AI, Mobile/Web, Backend/DB, DevOps).
Do not include any explanation or additional text."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical skill classifier. Respond with only the category name.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=20,
        )
        
        category = response.choices[0].message.content.strip()
        
        # Validate category is in our list
        if category in categories:
            return category
        
        # Fallback to heuristic if AI returns something unexpected
        return _classify_skill_heuristic(skill_name)
    except Exception:
        # Fallback to heuristic on any error
        return _classify_skill_heuristic(skill_name)


def _classify_skill_heuristic(skill_name: str) -> str:
    """Fallback heuristic classification."""
    skill_lower = skill_name.lower()
    
    # Languages
    languages = ["python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "ruby", "php", "swift", "kotlin", "scala", "r"]
    if any(lang in skill_lower for lang in languages):
        return "Languages"
    
    # ML/AI
    ml_ai = ["tensorflow", "pytorch", "keras", "scikit", "numpy", "pandas", "matplotlib", "seaborn", "xgboost", "opencv", "nltk", "spacy"]
    if any(term in skill_lower for term in ml_ai):
        return "ML/AI"
    
    # Mobile/Web
    mobile_web = ["react", "vue", "angular", "flutter", "react native", "expo", "next.js", "svelte", "ionic", "cordova"]
    if any(term in skill_lower for term in mobile_web):
        return "Mobile/Web"
    
    # Backend/DB
    backend_db = ["django", "flask", "fastapi", "express", "node.js", "spring", "rails", "postgresql", "mysql", "mongodb", "redis", "sqlite", "drizzle", "prisma", "sqlalchemy"]
    if any(term in skill_lower for term in backend_db):
        return "Backend/DB"
    
    # DevOps
    devops = ["docker", "kubernetes", "aws", "azure", "gcp", "terraform", "ansible", "jenkins", "github actions", "gitlab", "ci/cd", "linux", "bash"]
    if any(term in skill_lower for term in devops):
        return "DevOps"
    
    # Default to Backend/DB for unknown (better than Other)
    return "Backend/DB"


@router.post("/skills/classify-category")
async def classify_category(request: SkillCategoryRequest):
    """Classify a single skill into the appropriate category."""
    try:
        category = await classify_skill_category(request.skill_name)
        return {"skill": request.skill_name, "category": category}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
