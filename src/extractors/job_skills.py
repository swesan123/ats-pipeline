"""Extract skills from job descriptions using OpenAI."""

import os
from typing import Optional
from openai import OpenAI
from src.models.job import JobSkills, JobPosting


class JobSkillExtractor:
    """Extract skills from job descriptions using OpenAI structured output."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize extractor with OpenAI client."""
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        self.client = OpenAI(api_key=api_key)
    
    def extract_skills(self, job_posting: JobPosting) -> JobSkills:
        """Extract skills from job posting using OpenAI structured output."""
        prompt = self._build_prompt(job_posting.description)
        
        # Use structured output with function calling
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing job descriptions and extracting technical skills, soft skills, and seniority indicators."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0,  # Deterministic
        )
        
        # Parse response
        import json
        result = json.loads(response.choices[0].message.content)
        
        return JobSkills(
            required_skills=result.get("required_skills", []),
            preferred_skills=result.get("preferred_skills", []),
            soft_skills=result.get("soft_skills", []),
            seniority_indicators=result.get("seniority_indicators", []),
        )
    
    def _build_prompt(self, job_description: str) -> str:
        """Build prompt for skill extraction."""
        return f"""Extract skills and requirements from the following job description.

Job Description:
{job_description}

Analyze the job description and extract:
1. Required skills: Technical skills that are mandatory for this role
2. Preferred skills: Technical skills that are nice to have but not required
3. Soft skills: Communication, teamwork, leadership, etc.
4. Seniority indicators: Keywords that indicate experience level (e.g., "senior", "lead", "junior", "5+ years")

Return your analysis as a JSON object with the following structure:
{{
    "required_skills": ["skill1", "skill2", ...],
    "preferred_skills": ["skill1", "skill2", ...],
    "soft_skills": ["skill1", "skill2", ...],
    "seniority_indicators": ["indicator1", "indicator2", ...]
}}

Be specific and comprehensive. Include programming languages, frameworks, tools, methodologies, and domain knowledge."""

