"""Cover letter generator using AI."""

import os
import sys
from pathlib import Path
from typing import Optional
from openai import OpenAI, OpenAIError
from src.models.resume import Resume
from src.models.job import JobPosting


class CoverLetterGenerator:
    """Generate personalized cover letters using AI."""
    
    def __init__(self):
        """Initialize cover letter generator."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = OpenAI(api_key=api_key)
    
    def generate(self, resume: Resume, job: JobPosting) -> str:
        """Generate a cover letter for a job application.
        
        Args:
            resume: Resume object
            job: JobPosting object
            
        Returns:
            Generated cover letter text
        """
        # Extract key information from resume
        resume_summary = self._extract_resume_summary(resume)
        
        # Extract key information from job
        job_summary = self._extract_job_summary(job)
        
        # Generate cover letter using AI
        try:
            cover_letter = self._generate_with_ai(resume_summary, job_summary, job)
            return cover_letter
        except OpenAIError as e:
            raise ValueError(f"Failed to generate cover letter: {e}")
    
    def _extract_resume_summary(self, resume: Resume) -> str:
        """Extract key information from resume."""
        summary_parts = []
        
        # Add name/contact if available
        if hasattr(resume, 'name') and resume.name:
            summary_parts.append(f"Name: {resume.name}")
        
        # Add experience summary
        if resume.experience:
            summary_parts.append("\nExperience:")
            for exp in resume.experience[:3]:  # Top 3 experiences
                summary_parts.append(f"- {exp.role} at {exp.organization} ({exp.start_date} - {exp.end_date or 'Present'})")
                # Add first 2 bullets from each experience
                for bullet in exp.bullets[:2]:
                    summary_parts.append(f"  • {bullet.text}")
        
        # Add projects summary
        if resume.projects:
            summary_parts.append("\nProjects:")
            for project in resume.projects[:3]:  # Top 3 projects
                summary_parts.append(f"- {project.name}")
                if project.tech_stack:
                    summary_parts.append(f"  Technologies: {', '.join(project.tech_stack)}")
                # Add first bullet from each project
                if project.bullets:
                    summary_parts.append(f"  • {project.bullets[0].text}")
        
        # Add skills summary
        if resume.skills:
            summary_parts.append("\nKey Skills:")
            all_skills = []
            for category, skills in resume.skills.items():
                all_skills.extend(skills[:5])  # Top 5 from each category
            summary_parts.append(", ".join(all_skills[:15]))  # Top 15 skills
        
        return "\n".join(summary_parts)
    
    def _extract_job_summary(self, job: JobPosting) -> str:
        """Extract key information from job posting."""
        summary_parts = []
        
        summary_parts.append(f"Company: {job.company}")
        summary_parts.append(f"Title: {job.title}")
        if job.location:
            summary_parts.append(f"Location: {job.location}")
        
        # Extract first 500 characters of description
        if job.description:
            description_preview = job.description[:500]
            summary_parts.append(f"\nJob Description Preview:\n{description_preview}")
        
        return "\n".join(summary_parts)
    
    def _generate_with_ai(
        self,
        resume_summary: str,
        job_summary: str,
        job: JobPosting
    ) -> str:
        """Generate cover letter using OpenAI."""
        prompt = f"""Write a professional, personalized cover letter for this job application.

Job Information:
{job_summary}

Candidate Background:
{resume_summary}

Requirements:
1. Address the letter to the hiring manager (use "Dear Hiring Manager" if company name is not available)
2. Start with a strong opening paragraph that expresses genuine interest in the role and company
3. Highlight 2-3 key experiences or projects that directly relate to the job requirements
4. Show enthusiasm and explain why you're a good fit
5. Keep it concise (3-4 paragraphs, approximately 250-350 words)
6. End with a professional closing (e.g., "Sincerely," followed by a placeholder for signature)
7. Use professional, confident language
8. Avoid generic phrases - be specific about your accomplishments
9. Show knowledge of the company/role if possible
10. Emphasize how your skills and experience align with the job requirements

Generate the cover letter now:"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional career coach and cover letter writer. Write compelling, personalized cover letters that help candidates stand out.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=800,
        )
        
        cover_letter = response.choices[0].message.content.strip()
        
        # Ensure proper formatting
        if not cover_letter.startswith("Dear"):
            # Try to find where the letter starts
            lines = cover_letter.split("\n")
            for i, line in enumerate(lines):
                if "Dear" in line or line.strip().startswith("Dear"):
                    cover_letter = "\n".join(lines[i:])
                    break
        
        return cover_letter
