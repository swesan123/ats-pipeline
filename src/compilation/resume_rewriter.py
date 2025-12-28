"""Resume rewriter with reasoning chain generation."""

import os
from typing import Dict, List, Tuple, Optional
from openai import OpenAI
from src.models.resume import Resume, Bullet, Reasoning, Justification
from src.models.job import JobMatch
from src.models.skills import SkillOntology, UserSkills


class ResumeRewriter:
    """Generate resume bullet variations with reasoning chains."""
    
    def __init__(self, api_key: Optional[str] = None, user_skills: Optional[UserSkills] = None):
        """Initialize rewriter with OpenAI client and optional user skills."""
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        self.client = OpenAI(api_key=api_key)
        self.user_skills = user_skills
    
    def generate_variations(
        self,
        resume: Resume,
        job_match: JobMatch,
        ontology: SkillOntology,
    ) -> Dict[str, Tuple[Reasoning, List[Bullet]]]:
        """Generate variations for bullets needing adjustment.
        
        Returns: Dict mapping bullet_id -> (Reasoning, List[4 Bullet variations])
        """
        proposals = {}
        
        # Identify bullets that need adjustment based on gap analysis
        bullets_to_adjust = self._identify_bullets_to_adjust(resume, job_match)
        
        # Build a map of bullet_id to project context (if it's a project bullet)
        project_context_map = {}
        project_name_map = {}
        bullet_id = 0
        for project in resume.projects:
            for bullet in project.bullets:
                bullet_key = f"proj_{project.name}_{bullet_id}"
                project_context_map[bullet_key] = project.tech_stack
                project_name_map[bullet_key] = project.name
                bullet_id += 1
        
        for bullet_id, bullet in bullets_to_adjust.items():
            # Step 1: Generate reasoning chain
            reasoning = self._generate_reasoning(bullet, job_match, ontology)
            
            # Step 2: Generate variations with reasoning (pass project context if applicable)
            project_context = project_context_map.get(bullet_id)
            project_name = project_name_map.get(bullet_id)
            variations = self._generate_variations_with_reasoning(
                bullet, reasoning, job_match, ontology, project_context=project_context, project_name=project_name
            )
            
            proposals[bullet_id] = (reasoning, variations)
        
        return proposals
    
    def _identify_bullets_to_adjust(
        self, resume: Resume, job_match: JobMatch
    ) -> Dict[str, Bullet]:
        """Identify which bullets need adjustment based on gap analysis."""
        bullets_to_adjust = {}
        
        # Check if there are missing skills that could be added
        required_missing = job_match.skill_gaps.get("required_missing", [])
        preferred_missing = job_match.skill_gaps.get("preferred_missing", [])
        missing_skills = job_match.missing_skills or []
        
        # If no gaps at all, no adjustments needed
        if not required_missing and not preferred_missing and not missing_skills:
            return bullets_to_adjust  # No adjustments needed
        
        # Find bullets that could be enhanced
        bullet_id = 0
        for exp_item in resume.experience:
            for bullet in exp_item.bullets:
                bullet_key = f"exp_{exp_item.organization}_{bullet_id}"
                # Check if bullet could be enhanced with missing skills
                if self._bullet_can_be_enhanced(bullet, job_match, context=None):
                    bullets_to_adjust[bullet_key] = bullet
                bullet_id += 1
        
        bullet_id = 0
        for project in resume.projects:
            for bullet in project.bullets:
                bullet_key = f"proj_{project.name}_{bullet_id}"
                # For projects, pass the project's tech stack as context
                # Only enhance if skills match the project's tech stack
                if self._bullet_can_be_enhanced(bullet, job_match, context=project.tech_stack):
                    bullets_to_adjust[bullet_key] = bullet
                bullet_id += 1
        
        return bullets_to_adjust
    
    def _bullet_can_be_enhanced(self, bullet: Bullet, job_match: JobMatch, context: Optional[List[str]] = None) -> bool:
        """Check if a bullet can be enhanced with missing skills.
        
        Args:
            bullet: The bullet to check
            job_match: Job match information with missing skills
            context: Optional context (e.g., project tech stack) to restrict skill additions
        """
        # Get all missing skills (required, preferred, and general)
        all_missing = []
        all_missing.extend(job_match.skill_gaps.get("required_missing", [])[:5])
        all_missing.extend(job_match.skill_gaps.get("preferred_missing", [])[:3])
        all_missing.extend(job_match.missing_skills[:3])
        
        if not all_missing:
            return False
        
        # For project bullets, only consider skills that match the project's tech stack
        if context is not None:
            # Context is a project's tech stack
            context_lower = [s.lower() for s in context]
            # Filter missing skills to only those that match the project context
            relevant_missing = []
            for skill in all_missing:
                skill_lower = skill.lower()
                # Check if skill matches any tech in the project
                if any(tech in skill_lower or skill_lower in tech for tech in context_lower):
                    relevant_missing.append(skill)
                # Also check for related skills (e.g., Python -> NumPy, pandas)
                elif self._skill_matches_context(skill, context_lower):
                    relevant_missing.append(skill)
            
            if not relevant_missing:
                return False  # No relevant skills for this project
            all_missing = relevant_missing
        
        # If bullet has few skills, it can definitely be enhanced
        if len(bullet.skills) < 2:
            return True
        
        # Check if any missing skills could fit in this bullet's context
        bullet_text_lower = bullet.text.lower()
        for missing_skill in all_missing:
            skill_lower = missing_skill.lower()
            # Check if skill is mentioned or if bullet context is relevant
            if skill_lower in bullet_text_lower or self._skill_relevant(missing_skill, bullet_text_lower):
                return True
        
        # For experience bullets (no context), allow enhancement in technical contexts
        if context is None:
            tech_keywords = ["develop", "build", "implement", "create", "design", "code", "program", "system", "software", "application"]
            if any(keyword in bullet_text_lower for keyword in tech_keywords):
                # Technical bullets can often be enhanced with additional skills
                return True
        
        return False
    
    def _skill_matches_context(self, skill: str, context: List[str]) -> bool:
        """Check if a skill matches the project context (e.g., related technologies)."""
        skill_lower = skill.lower()
        
        # Related technology mappings
        related_tech = {
            "python": ["numpy", "pandas", "scikit-learn", "tensorflow", "pytorch", "matplotlib"],
            "javascript": ["typescript", "node.js", "react", "vue", "angular"],
            "java": ["spring", "maven", "gradle"],
            "golang": ["go"],
            "react": ["react native", "next.js"],
            "node.js": ["express", "trpc", "graphql"],
        }
        
        # Check if skill is related to any tech in context
        for tech in context:
            tech_lower = tech.lower()
            # Direct match
            if skill_lower in tech_lower or tech_lower in skill_lower:
                return True
            # Check related technologies
            for key, related in related_tech.items():
                if key in tech_lower and skill_lower in related:
                    return True
                if skill_lower == key and any(r in tech_lower for r in related):
                    return True
        
        return False
    
    def _skill_relevant(self, skill: str, bullet_text: str) -> bool:
        """Check if skill is relevant to bullet context."""
        # Simple heuristic: check for related keywords
        tech_keywords = ["develop", "build", "implement", "create", "design", "code"]
        return any(keyword in bullet_text for keyword in tech_keywords)
    
    def _generate_reasoning(
        self, bullet: Bullet, job_match: JobMatch, ontology: SkillOntology
    ) -> Reasoning:
        """Generate reasoning chain for bullet adjustment."""
        prompt = self._build_reasoning_prompt(bullet, job_match)
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume writer. Think step-by-step about how to improve resume bullets to match job requirements."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        
        return Reasoning(
            problem_identification=result.get("problem_identification", ""),
            analysis=result.get("analysis", ""),
            solution_approach=result.get("solution_approach", ""),
            evaluation=result.get("evaluation", ""),
            alternatives_considered=result.get("alternatives_considered", []),
            confidence_score=result.get("confidence_score", 0.5),
        )
    
    def _build_reasoning_prompt(self, bullet: Bullet, job_match: JobMatch) -> str:
        """Build prompt for reasoning generation."""
        missing_skills_str = ", ".join(job_match.missing_skills[:10])
        skill_gaps_str = ", ".join(job_match.skill_gaps.get("required_missing", [])[:10])
        
        return f"""Analyze this resume bullet and job requirements to generate a reasoning chain for improvement.

Current Bullet: {bullet.text}
Skills in Bullet: {', '.join(bullet.skills)}

Job Requirements:
- Missing Required Skills: {skill_gaps_str}
- Skills Not in Resume: {missing_skills_str}
- Matching Skills: {', '.join(job_match.matching_skills[:10])}

Think step-by-step and provide:
1. problem_identification: What gap/issue prompted this change?
2. analysis: How does current bullet compare to job requirements?
3. solution_approach: Why was this approach chosen?
4. evaluation: Why does this variation work better?
5. alternatives_considered: What other approaches were considered? (list)
6. confidence_score: Confidence in this change (0.0-1.0)

Return as JSON:
{{
    "problem_identification": "...",
    "analysis": "...",
    "solution_approach": "...",
    "evaluation": "...",
    "alternatives_considered": ["...", "..."],
    "confidence_score": 0.85
}}"""
    
    def _generate_variations_with_reasoning(
        self,
        bullet: Bullet,
        reasoning: Reasoning,
        job_match: JobMatch,
        ontology: SkillOntology,
        project_context: Optional[List[str]] = None,
        project_name: Optional[str] = None,
    ) -> List[Bullet]:
        """Generate 4 variations based on reasoning.
        
        Args:
            bullet: The bullet to generate variations for
            reasoning: The reasoning chain for the change
            job_match: Job match information
            ontology: Skill ontology
            project_context: Optional project tech stack to restrict skill additions
            project_name: Optional project name for user skills filtering
        """
        prompt = self._build_variation_prompt(bullet, reasoning, job_match, project_context=project_context, project_name=project_name)
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume writer. Generate 4 variations of a bullet point, each emphasizing different aspects. Maintain factual accuracy - do not fabricate experience."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,  # Some creativity for variations
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        variations_data = result.get("variations", [])
        
        variations = []
        for i, var_data in enumerate(variations_data[:4]):
            var_text = var_data.get("text", "")
            var_skills = var_data.get("skills", [])
            var_justification = Justification(
                trigger=var_data.get("trigger", reasoning.problem_identification),
                skills_added=var_data.get("skills_added", []),
                ats_keywords_added=var_data.get("ats_keywords_added", []),
            )
            
            # Validate bullet length
            if len(var_text) > 150:
                var_text = var_text[:147] + "..."
            
            new_bullet = Bullet(
                text=var_text,
                skills=var_skills,
            )
            
            # Store justification in history
            from src.models.resume import BulletHistory
            new_bullet.history.append(BulletHistory(
                original_text=bullet.text,
                new_text=var_text,
                justification=var_justification,
                reasoning=reasoning,
            ))
            
            variations.append(new_bullet)
        
        # Ensure we have exactly 4 variations
        while len(variations) < 4:
            # Duplicate last variation if needed
            if variations:
                variations.append(variations[-1])
            else:
                # Fallback: return original bullet
                variations.append(bullet)
        
        return variations[:4]
    
    def _build_variation_prompt(
        self, bullet: Bullet, reasoning: Reasoning, job_match: JobMatch, project_context: Optional[List[str]] = None, project_name: Optional[str] = None
    ) -> str:
        """Build prompt for variation generation."""
        context_note = ""
        if project_context:
            context_note = f"\n\nIMPORTANT - Project Context: This bullet is part of a project with tech stack: {', '.join(project_context)}. Only add skills that are relevant to this project's tech stack. Do NOT add unrelated skills (e.g., do not add Golang/Swift/Kotlin to a Python/ML project unless they are actually used in the project)."
        
        # Add user skills restriction if available
        user_skills_note = ""
        if self.user_skills:
            # Get allowed skills for this project (if project_name provided)
            if project_name:
                allowed_skills = self.user_skills.get_skills_for_project(project_name)
                if allowed_skills:
                    user_skills_note = f"\n\nCRITICAL - Allowed Skills Only: You may ONLY use these skills that are verified for this project: {', '.join(allowed_skills)}. Do NOT add any skills that are not in this list. If a required job skill is not in this list, do NOT add it to the bullet."
            else:
                # For non-project bullets, use all user skills
                all_user_skills = list(self.user_skills.get_all_skill_names())
                if all_user_skills:
                    user_skills_note = f"\n\nCRITICAL - Allowed Skills Only: You may ONLY use these verified skills: {', '.join(all_user_skills[:20])}. Do NOT add any skills that are not in this list. If a required job skill is not in this list, do NOT add it to the bullet."
        
        return f"""Generate 4 variations of this resume bullet based on the reasoning chain.

Original Bullet: {bullet.text}
Current Skills: {', '.join(bullet.skills)}{context_note}{user_skills_note}

Reasoning:
- Problem: {reasoning.problem_identification}
- Analysis: {reasoning.analysis}
- Solution Approach: {reasoning.solution_approach}
- Evaluation: {reasoning.evaluation}
- Alternatives: {', '.join(reasoning.alternatives_considered[:3])}

Job Context:
- Missing Skills: {', '.join(job_match.missing_skills[:5])}
- Required Skills: {', '.join(job_match.skill_gaps.get('required_missing', [])[:5])}

Generate 4 variations:
1. Emphasize skills identified in reasoning
2. Add ATS keywords from reasoning analysis
3. Restructure based on solution approach
4. Alternative phrasing from alternatives considered

Each variation must:
- Be ≤150 characters
- Maintain factual accuracy (no fabrication)
- Include skills that are actually demonstrated and relevant to the project/context
- Have one clear claim per bullet
- For project bullets: Only use skills that match the project's tech stack
- NEVER add skills that are not in the allowed skills list (if provided)

Return as JSON:
{{
    "variations": [
        {{
            "text": "...",
            "skills": ["skill1", "skill2"],
            "trigger": "...",
            "skills_added": ["skill1"],
            "ats_keywords_added": ["keyword1"]
        }},
        ...
    ]
}}"""

