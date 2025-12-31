"""AI-powered bullet generation for projects and experience."""

import json
import os
import sys
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from openai import OpenAI

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

router = APIRouter()


class BulletGenerationRequest(BaseModel):
    """Request model for bullet generation."""
    project_name: str
    description: Optional[str] = None  # Optional project description
    tech_stack: List[str] = []
    context: Optional[str] = None  # Additional context about the project


class BulletGenerationResponse(BaseModel):
    """Response model for bullet generation."""
    bullets: List[str]
    reasoning: Optional[str] = None


# Example bullets from the user's resume for reference
EXAMPLE_BULLETS = [
    "Built a convolutional neural network classifier in **Python** using **TensorFlow**.",
    "Applied preprocessing, augmentation, and splitting using **NumPy** and **pandas**.",
    "Evaluated accuracy, precision, recall, and confusion matrices using **scikit-learn** and **Matplotlib**.",
    "Trained SVM models in **Python** using **scikit-learn** to classify flare intensity.",
    "Improved accuracy through feature scaling and hyperparameter tuning using **NumPy** and **pandas**.",
    "Visualized ROC/PR curves and confusion matrices with **Matplotlib**.",
    "Implemented a feedforward neural network in **PyTorch** with two hidden layers.",
    "Applied early stopping, mini-batch SGD, dropout, and L1/L2 regularization using **NumPy** and **scikit-learn**.",
    "Plotted training/validation loss trends using **Matplotlib**.",
    "Developing a mobile ride-share application using **React Native** and **TypeScript**.",
    "Built backend APIs using **Node.js**, **tRPC**, and **PostgreSQL**.",
    "Implemented user authentication with **JWT** and styled UI using **Tailwind**.",
    "Validated AMD **MI300X/MI325X/MI350X/MI355X** GPUs using internal debugging tools and **Python**.",
    "Triaged silicon, firmware, and platform issues using **Linux**-based debug workflows.",
    "Developed automated triage flows in **Python**, reducing diagnosis time by **50%**.",
    "Authored reusable debug playbooks to standardize validation procedures across teams.",
]


BULLET_GUIDELINES = """
BULLET POINT STRUCTURE AND GUIDELINES:

1. **Format**: Full sentences, 1-2 lines maximum (approximately 100-150 characters)
2. **Start with Action Verbs**: Use past tense action verbs (Built, Applied, Evaluated, Trained, Improved, Visualized, Implemented, Developed, Created, Designed, Optimized, etc.)
3. **Include Technologies**: Bold key technologies/frameworks using **Technology** format
4. **Focus on Accomplishments**: What was accomplished, not just what was done
5. **Be Specific**: Include specific technologies, methods, or results
6. **Show Impact**: Include metrics or outcomes when possible (e.g., "reducing diagnosis time by 50%")
7. **Technical Details**: Include relevant technical details (algorithms, architectures, methods)
8. **No Fragments**: Each bullet must be a complete, grammatically correct sentence
9. **Professional Tone**: Use professional, concise language suitable for a resume

EXAMPLES OF GOOD BULLETS:
- "Built a convolutional neural network classifier in **Python** using **TensorFlow**."
- "Applied preprocessing, augmentation, and splitting using **NumPy** and **pandas**."
- "Evaluated accuracy, precision, recall, and confusion matrices using **scikit-learn** and **Matplotlib**."
- "Developed automated triage flows in **Python**, reducing diagnosis time by **50%**."

EXAMPLES OF BAD BULLETS (DO NOT GENERATE THESE):
- "CNN training on two datasets" (fragment, not a sentence)
- "Behavior of training vs validation loss curves" (not an accomplishment)
- "Conv1: 1 → 10 filters" (too technical, not formatted for resume)
- "Overfitting and underfitting patterns" (not an accomplishment)
"""


@router.post("/bullets/generate", response_model=BulletGenerationResponse)
async def generate_bullets(request: BulletGenerationRequest):
    """Generate AI-powered resume bullets for a project."""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500, detail="OpenAI API key not configured"
            )
        
        client = OpenAI(api_key=api_key)
        
        tech_stack_str = ", ".join(request.tech_stack) if request.tech_stack else "Not specified"
        description_str = f"\nProject Description: {request.description}" if request.description else ""
        context_str = f"\n\nAdditional Context: {request.context}" if request.context else ""
        
        prompt = f"""Generate 3-5 professional resume bullet points for this project.

{BULLET_GUIDELINES}

Project Name: {request.project_name}{description_str}
Tech Stack: {tech_stack_str}{context_str}

CRITICAL REQUIREMENTS:
1. Each bullet must be a complete sentence (not a fragment)
2. Start with action verbs: Built, Developed, Implemented, Created, Designed, Applied, Evaluated, Trained, Improved, Visualized, Optimized, etc.
3. Include technologies in **bold** format: **TechnologyName**
4. Keep bullets concise: 1-2 lines maximum (approximately 100-150 characters)
5. Focus on WHAT was accomplished, not just what was done
6. Include specific technical details (methods, algorithms, frameworks)
7. DO NOT fabricate metrics unless explicitly mentioned in the description
8. Match the style of the examples below exactly

Return as JSON:
{{
    "bullets": ["bullet 1", "bullet 2", "bullet 3"],
    "reasoning": "Brief explanation of why these bullets were chosen"
}}

Reference examples (match this style exactly):
{chr(10).join(f"- {ex}" for ex in EXAMPLE_BULLETS[:8])}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional resume writer specializing in technical bullet points. Generate concise, impactful bullets that highlight technical accomplishments.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        
        result = json.loads(response.choices[0].message.content)
        
        bullets = result.get("bullets", [])
        reasoning = result.get("reasoning", "")
        
        # Validate bullets are full sentences
        validated_bullets = []
        for bullet in bullets:
            bullet = bullet.strip()
            # Ensure it's a full sentence (ends with period)
            if bullet and not bullet.endswith('.'):
                bullet += '.'
            if bullet:
                validated_bullets.append(bullet)
        
        return BulletGenerationResponse(
            bullets=validated_bullets,
            reasoning=reasoning,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class BulletFormatRequest(BaseModel):
    """Request model for formatting existing bullets."""
    bullets: List[str]
    project_name: str
    tech_stack: List[str] = []


@router.post("/bullets/format", response_model=BulletGenerationResponse)
async def format_bullets(request: BulletFormatRequest):
    """Format existing bullets to ensure proper structure and bolding."""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500, detail="OpenAI API key not configured"
            )
        
        client = OpenAI(api_key=api_key)
        
        tech_stack_str = ", ".join(request.tech_stack) if request.tech_stack else "Not specified"
        
        # Combine bullets into context
        bullets_context = "\n".join([f"- {bullet}" for bullet in request.bullets])
        
        prompt = f"""Format the following bullet points to match professional resume standards.

{BULLET_GUIDELINES}

Project Name: {request.project_name}
Tech Stack: {tech_stack_str}

Current Bullets to Format:
{bullets_context}

CRITICAL REQUIREMENTS:
1. Convert each bullet into a complete sentence starting with an action verb
2. Bold ALL technologies from the tech stack that appear in each bullet using **Technology** format
3. Ensure proper grammar and professional tone
4. Keep bullets concise (1-2 lines, 100-150 characters)
5. Maintain the original meaning and accomplishments
6. If a bullet is already well-formatted, improve it slightly but keep the core content
7. Ensure all technologies from tech stack are bolded: {tech_stack_str}

Return as JSON:
{{
    "bullets": ["formatted bullet 1", "formatted bullet 2", ...],
    "reasoning": "Brief explanation of formatting changes"
}}

Reference examples (match this style exactly):
{chr(10).join(f"- {ex}" for ex in EXAMPLE_BULLETS[:8])}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional resume editor. Format bullets to ensure proper structure, bolding of technologies, and professional tone.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.5,  # Lower temperature for more consistent formatting
        )
        
        result = json.loads(response.choices[0].message.content)
        
        bullets = result.get("bullets", [])
        reasoning = result.get("reasoning", "")
        
        # Ensure we have the same number of bullets (or fewer if some were invalid)
        if len(bullets) > len(request.bullets):
            bullets = bullets[:len(request.bullets)]
        elif len(bullets) < len(request.bullets):
            # If AI returned fewer bullets, pad with formatted versions of originals
            while len(bullets) < len(request.bullets):
                bullets.append(request.bullets[len(bullets)])
        
        # Validate and ensure proper formatting
        validated_bullets = []
        for bullet in bullets:
            bullet = bullet.strip()
            # Ensure it ends with period
            if bullet and not bullet.endswith('.'):
                bullet += '.'
            if bullet:
                validated_bullets.append(bullet)
        
        return BulletGenerationResponse(
            bullets=validated_bullets,
            reasoning=reasoning or "Bullets formatted to match professional resume standards.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
