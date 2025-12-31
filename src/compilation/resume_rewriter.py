"""Resume rewriter with reasoning chain generation."""

import os
import uuid
from typing import Dict, List, Tuple, Optional
from openai import OpenAI
from src.models.resume import Resume, Bullet, Reasoning, Justification, BulletCandidate
from src.models.job import JobMatch
from src.models.skills import SkillOntology, UserSkills
from src.compilation.bullet_scorer import BulletScorer
from src.compilation.bullet_validator import BulletValidator


class ResumeRewriter:
    """Generate resume bullet variations with reasoning chains."""
    
    def __init__(self, api_key: Optional[str] = None, user_skills: Optional[UserSkills] = None, ontology: Optional[SkillOntology] = None):
        """Initialize rewriter with OpenAI client and optional user skills."""
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        self.client = OpenAI(api_key=api_key)
        self.user_skills = user_skills
        self.ontology = ontology or SkillOntology()
        self.scorer = BulletScorer()
        self.validator = BulletValidator(ontology=self.ontology, user_skills=user_skills)
    
    def _get_allowed_job_skills_for_user(self, job_match: JobMatch) -> List[str]:
        """Get intersection of user skills and job skills (required + preferred).
        
        This is the only set of skills that can be mentioned in bullets.
        
        Args:
            job_match: Job match information with job skills
        
        Returns:
            List of allowed skill names (intersection of user skills and job skills)
        """
        if not self.user_skills:
            return []
        
        user_skills_set = self.user_skills.get_all_skill_names()
        user_skills_lower = {s.lower().strip() for s in user_skills_set}
        
        # Get all job skills (required + preferred)
        job_skills_list = []
        if hasattr(job_match, 'skill_gaps'):
            job_skills_list.extend(job_match.skill_gaps.get("required_missing", []))
            job_skills_list.extend(job_match.skill_gaps.get("preferred_missing", []))
        if hasattr(job_match, 'missing_skills'):
            job_skills_list.extend(job_match.missing_skills)
        
        # Find intersection: skills that are both in user's skills AND in job requirements
        allowed_skills = []
        for job_skill in job_skills_list:
            job_skill_lower = job_skill.lower().strip()
            # Check for exact match or partial match
            for user_skill in user_skills_set:
                user_skill_lower = user_skill.lower().strip()
                if (user_skill_lower == job_skill_lower or 
                    user_skill_lower in job_skill_lower or 
                    job_skill_lower in user_skill_lower):
                    if user_skill not in allowed_skills:
                        allowed_skills.append(user_skill)
        
        return allowed_skills
    
    def generate_variations(
        self,
        resume: Resume,
        job_match: JobMatch,
        ontology: Optional[SkillOntology] = None,
        rewrite_intent: Optional[str] = None,
    ) -> Dict[str, Tuple[Reasoning, List[BulletCandidate]]]:
        """Generate ranked candidate variations for bullets needing adjustment.
        
        Args:
            resume: Resume to generate variations for
            job_match: Job match information
            ontology: Skill ontology (uses instance ontology if not provided)
            rewrite_intent: Optional rewrite intent ("emphasize_skills", "more_technical", "more_concise", "conservative")
        
        Returns: Dict mapping bullet_id -> (Reasoning, List[ranked BulletCandidate objects])
        """
        if ontology:
            self.ontology = ontology
            self.validator = BulletValidator(ontology=ontology, user_skills=self.user_skills)
        
        # Track resume generation started event (if db available)
        # Note: This requires db to be passed or accessed differently
        # For now, we'll track this in the calling code
        
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
            reasoning = self._generate_reasoning(bullet, job_match, self.ontology)
            
            # Step 2: Generate candidates with reasoning (pass project context if applicable)
            project_context = project_context_map.get(bullet_id)
            project_name = project_name_map.get(bullet_id)
            candidates = self._generate_candidates_with_reasoning(
                bullet, reasoning, job_match, self.ontology, 
                project_context=project_context, 
                project_name=project_name,
                rewrite_intent=rewrite_intent
            )
            
            # Step 3: Validate and filter candidates
            # Get allowed job skills for validation
            allowed_job_skills = self._get_allowed_job_skills_for_user(job_match)
            valid_candidates = []
            for candidate in candidates:
                is_valid, errors = self.validator.validate(
                    candidate, 
                    bullet.text, 
                    job_skills=allowed_job_skills if allowed_job_skills else None,
                    rewrite_intent=rewrite_intent
                )
                if is_valid:
                    valid_candidates.append(candidate)
                # Log errors for debugging if needed
            
            # Step 4: Rank candidates
            ranked_candidates = self.scorer.rank_candidates(valid_candidates, bullet.text, job_match)
            
            # Step 5: Calculate risk levels
            for candidate in ranked_candidates:
                candidate.risk_level = self.scorer.calculate_risk_level(candidate, bullet.text)
            
            proposals[bullet_id] = (reasoning, ranked_candidates)
        
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
        # Get allowed skills: intersection of user skills and job skills
        allowed_skills = self._get_allowed_job_skills_for_user(job_match)
        
        # Filter missing skills to only those the user actually has AND are job-relevant
        missing_skills_filtered = []
        allowed_skills_lower = {s.lower().strip() for s in allowed_skills}
        for skill in job_match.missing_skills[:10]:
            skill_lower = skill.lower().strip()
            if any(allowed.lower().strip() == skill_lower or 
                   allowed.lower().strip() in skill_lower or 
                   skill_lower in allowed.lower().strip() 
                   for allowed in allowed_skills):
                missing_skills_filtered.append(skill)
        
        # Filter required missing skills similarly
        required_missing_filtered = []
        for skill in job_match.skill_gaps.get("required_missing", [])[:10]:
            skill_lower = skill.lower().strip()
            if any(allowed.lower().strip() == skill_lower or 
                   allowed.lower().strip() in skill_lower or 
                   skill_lower in allowed.lower().strip() 
                   for allowed in allowed_skills):
                required_missing_filtered.append(skill)
        
        missing_skills_str = ", ".join(missing_skills_filtered) if missing_skills_filtered else "None (all covered by your skills)"
        skill_gaps_str = ", ".join(required_missing_filtered) if required_missing_filtered else "None (all covered by your skills)"
        
        user_skills_note = ""
        if allowed_skills:
            user_skills_list = sorted(allowed_skills)[:30]  # Show first 30
            user_skills_note = f"\n\nCRITICAL CONSTRAINT: You may ONLY work with these verified skills from the user's Skills page that are ALSO job-relevant: {', '.join(user_skills_list)}. Do NOT suggest adding any skills that are not in this list. If a job requires a skill not in this list, acknowledge it but do NOT add it to the bullet."
        elif self.user_skills:
            user_skills_set = self.user_skills.get_all_skill_names()
            user_skills_list = sorted(list(user_skills_set))[:30]
            user_skills_note = f"\n\nCRITICAL CONSTRAINT: You may ONLY work with these verified skills from the user's Skills page: {', '.join(user_skills_list)}. Do NOT suggest adding any skills that are not in this list. If a job requires a skill not in this list, acknowledge it but do NOT add it to the bullet."
        
        return f"""Analyze this resume bullet and job requirements to generate a reasoning chain for improvement.

Current Bullet: {bullet.text}
Skills in Bullet: {', '.join(bullet.skills)}

Job Requirements:
- Missing Required Skills: {skill_gaps_str}
- Skills Not in Resume: {missing_skills_str}
- Matching Skills: {', '.join(job_match.matching_skills[:10])}{user_skills_note}

Think step-by-step and provide:
1. problem_identification: What gap/issue prompted this change? (Only consider gaps that can be addressed with verified skills)
2. analysis: How does current bullet compare to job requirements? (Focus on skills you can actually add)
3. solution_approach: Why was this approach chosen? (Only use verified skills from the Skills page)
4. evaluation: Why does this variation work better? (Without fabricating new skills)
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
    
    def _generate_candidates_with_reasoning(
        self,
        bullet: Bullet,
        reasoning: Reasoning,
        job_match: JobMatch,
        ontology: SkillOntology,
        project_context: Optional[List[str]] = None,
        project_name: Optional[str] = None,
        rewrite_intent: Optional[str] = None,
    ) -> List[BulletCandidate]:
        """Generate bullet candidates with metadata based on reasoning.
        
        Args:
            bullet: The bullet to generate candidates for
            reasoning: The reasoning chain for the change
            job_match: Job match information
            ontology: Skill ontology
            project_context: Optional project tech stack to restrict skill additions
            project_name: Optional project name for user skills filtering
            rewrite_intent: Optional rewrite intent to guide generation
        
        Returns:
            List of BulletCandidate objects with metadata
        """
        prompt = self._build_candidate_prompt(bullet, reasoning, job_match, project_context=project_context, project_name=project_name, rewrite_intent=rewrite_intent)
        
        system_message = "You are an expert resume writer. Generate bullet point candidates with detailed metadata including scores, diffs, and justifications. Maintain factual accuracy - do not fabricate experience."
        if self.user_skills:
            system_message += " CRITICAL: You may ONLY use skills from the user's verified Skills page. Adding any skill not explicitly listed is STRICTLY FORBIDDEN and will result in rejection."
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": system_message
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,  # Some creativity for variations
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        candidates_data = result.get("candidates", [])
        
        candidates = []
        for i, cand_data in enumerate(candidates_data[:4]):
            var_text = cand_data.get("text", "")
            
            # Validate bullet length
            if len(var_text) > 150:
                var_text = var_text[:147] + "..."
            
            # Extract metadata
            score = cand_data.get("score", {})
            diff = cand_data.get("diff_from_original", {"added": [], "removed": []})
            justification = cand_data.get("justification", {})
            intent = cand_data.get("rewrite_intent", rewrite_intent)
            
            # Create candidate
            candidate = BulletCandidate(
                candidate_id=f"{bullet.text[:20]}_{uuid.uuid4().hex[:8]}",
                text=var_text,
                score={
                    "job_skill_coverage": score.get("job_skill_coverage", 0.0),
                    "ats_keyword_gain": score.get("ats_keyword_gain", 0),
                    "semantic_similarity": score.get("semantic_similarity", 0.0),
                    "constraint_violations": score.get("constraint_violations", 0),
                },
                diff_from_original={
                    "added": diff.get("added", []),
                    "removed": diff.get("removed", []),
                },
                justification={
                    "job_requirements_addressed": justification.get("job_requirements_addressed", []),
                    "skills_mapped": justification.get("skills_mapped", []),
                    "why_this_version": justification.get("why_this_version", ""),
                },
                risk_level="medium",  # Will be calculated later
                rewrite_intent=intent,
                composite_score=0.0,  # Will be calculated by scorer
            )
            
            candidates.append(candidate)
        
        # Ensure we have at least one candidate
        if not candidates:
            # Fallback: create a candidate from original
            candidates.append(BulletCandidate(
                candidate_id=f"{bullet.text[:20]}_{uuid.uuid4().hex[:8]}",
                text=bullet.text,
                score={"job_skill_coverage": 0.0, "ats_keyword_gain": 0, "semantic_similarity": 1.0, "constraint_violations": 0},
                diff_from_original={"added": [], "removed": []},
                justification={"job_requirements_addressed": [], "skills_mapped": [], "why_this_version": "Original bullet"},
                risk_level="low",
                rewrite_intent=None,
                composite_score=0.0,
            ))
        
        return candidates
    
    def _build_candidate_prompt(
        self, bullet: Bullet, reasoning: Reasoning, job_match: JobMatch, project_context: Optional[List[str]] = None, project_name: Optional[str] = None, rewrite_intent: Optional[str] = None
    ) -> str:
        """Build prompt for variation generation."""
        from src.compilation.bullet_feedback import BulletFeedbackStore
        
        # Get allowed skills: intersection of user skills and job skills
        allowed_skills = self._get_allowed_job_skills_for_user(job_match)
        
        context_note = ""
        if project_context:
            context_note = f"\n\nIMPORTANT - Project Context: This bullet is part of a project with tech stack: {', '.join(project_context)}. Only add skills that are relevant to this project's tech stack. Do NOT add unrelated skills (e.g., do not add Golang/Swift/Kotlin to a Python/ML project unless they are actually used in the project)."
        
        # Add user skills restriction if available - STRICT ENFORCEMENT
        user_skills_note = ""
        if self.user_skills:
            # Get allowed skills for this project (if project_name provided)
            if project_name:
                project_skills = self.user_skills.get_skills_for_project(project_name)
                # Intersect with job-relevant skills
                if project_skills:
                    # Filter to only skills that are both in project AND in allowed_skills
                    project_allowed = [s for s in project_skills if s in allowed_skills or any(s.lower() == a.lower() for a in allowed_skills)]
                    if project_allowed:
                        user_skills_note = f"\n\n🚫 STRICT CONSTRAINT - Allowed Skills ONLY: You MUST ONLY use these verified skills for this project that are ALSO job-relevant: {', '.join(project_allowed)}. It is FORBIDDEN to add ANY skill not in this list. If a job requires a skill not listed here, you MUST NOT add it - instead, rephrase the bullet to emphasize skills you CAN use."
                    else:
                        # No intersection - use project skills but warn
                        user_skills_note = f"\n\n🚫 STRICT CONSTRAINT - Allowed Skills ONLY: You MUST ONLY use these verified skills for this project: {', '.join(project_skills)}. It is FORBIDDEN to add ANY skill not in this list."
                else:
                    # No project-specific skills, use allowed job skills
                    if allowed_skills:
                        user_skills_note = f"\n\n🚫 STRICT CONSTRAINT - Allowed Skills ONLY: You MUST ONLY use these verified skills from the Skills page that are ALSO job-relevant: {', '.join(allowed_skills[:40])}. It is FORBIDDEN to add ANY skill not in this list."
            else:
                # For non-project bullets, use allowed job skills
                if allowed_skills:
                    user_skills_note = f"\n\n🚫 STRICT CONSTRAINT - Allowed Skills ONLY: You MUST ONLY use these verified skills from the Skills page that are ALSO job-relevant: {', '.join(allowed_skills[:40])}. It is FORBIDDEN to add ANY skill not in this list. If a job requires a skill not listed here, you MUST NOT add it - instead, rephrase the bullet to emphasize skills you CAN use."
        
        # Filter job context to only show skills the user actually has AND are job-relevant
        job_missing_filtered = []
        job_required_filtered = []
        allowed_skills_lower = {s.lower().strip() for s in allowed_skills}
        for skill in job_match.missing_skills[:5]:
            skill_lower = skill.lower().strip()
            if any(allowed.lower().strip() == skill_lower or 
                   allowed.lower().strip() in skill_lower or 
                   skill_lower in allowed.lower().strip() 
                   for allowed in allowed_skills):
                job_missing_filtered.append(skill)
        for skill in job_match.skill_gaps.get('required_missing', [])[:5]:
            skill_lower = skill.lower().strip()
            if any(allowed.lower().strip() == skill_lower or 
                   allowed.lower().strip() in skill_lower or 
                   skill_lower in allowed.lower().strip() 
                   for allowed in allowed_skills):
                job_required_filtered.append(skill)

        # Incorporate simple user preference note based on past feedback
        feedback_note = ""
        try:
            store = BulletFeedbackStore()
            note = store.preference_note()
            if note:
                feedback_note = f"\\n\\nUSER PREFERENCES: {note}"
        except Exception:
            feedback_note = ""
        
        # Build intent-specific guidance
        intent_guidance = ""
        if rewrite_intent == "reword_only":
            intent_guidance = "\n\n🚫 CRITICAL: REWORD-ONLY MODE - You MUST NOT add any new skills. You may ONLY reword the existing bullet text to improve clarity, strength, or readability. The set of skills mentioned in the bullet must remain EXACTLY the same. Preserve all existing skills and do not introduce any new technical terms or skill names."
        elif rewrite_intent == "emphasize_skills":
            intent_guidance = "\n\nFocus: Emphasize required/preferred skills from the job description. Add skill keywords naturally, but ONLY from the allowed skills list."
        elif rewrite_intent == "more_technical":
            intent_guidance = "\n\nFocus: Make the bullet more technical and specific. Use precise technical terminology, but ONLY from the allowed skills list."
        elif rewrite_intent == "more_concise":
            intent_guidance = "\n\nFocus: Make the bullet more concise while preserving key information. Remove unnecessary words. Do not add new skills unless they are in the allowed list."
        elif rewrite_intent == "conservative":
            intent_guidance = "\n\nFocus: Conservative rewrite - minimal changes, only add skills that clearly fit the context AND are in the allowed skills list. Avoid scope expansion."
        
        return f"""Generate 4 bullet candidates with detailed metadata based on the reasoning chain.

Original Bullet: {bullet.text}
Current Skills: {', '.join(bullet.skills)}{context_note}{user_skills_note}{intent_guidance}

Reasoning:
- Problem: {reasoning.problem_identification}
- Analysis: {reasoning.analysis}
- Solution Approach: {reasoning.solution_approach}
- Evaluation: {reasoning.evaluation}
- Alternatives: {', '.join(reasoning.alternatives_considered[:3])}

Job Context (filtered to your verified skills only):
- Missing Skills You Can Address: {', '.join(job_missing_filtered) if job_missing_filtered else 'None - focus on emphasizing existing skills'}
- Required Skills You Can Address: {', '.join(job_required_filtered) if job_required_filtered else 'None - focus on emphasizing existing skills'}
- Matching Skills: {', '.join(job_match.matching_skills[:5])}
{feedback_note}

For each candidate, provide:
1. text: The bullet text (≤150 characters)
2. score: Object with:
   - job_skill_coverage: 0.0-1.0 (how well it covers required/preferred skills)
   - ats_keyword_gain: integer (number of new ATS keywords added)
   - semantic_similarity: 0.0-1.0 (how similar to original meaning)
   - constraint_violations: integer (number of constraint violations, 0 is best)
3. diff_from_original: Object with:
   - added: List of words/phrases added
   - removed: List of words/phrases removed
4. justification: Object with:
   - job_requirements_addressed: List of job requirements this addresses
   - skills_mapped: List of skills mentioned/added
   - why_this_version: Brief explanation
5. rewrite_intent: "{rewrite_intent or 'emphasize_skills'}"

Each candidate must:
- Be ≤150 characters
- Maintain factual accuracy (no fabrication)
- Include ONLY skills from the verified Skills page list (if provided)
- Have one clear claim per bullet
- For project bullets: Only use skills that match the project's tech stack AND are in your Skills page
- NEVER add skills that are not in the allowed skills list - this is STRICTLY FORBIDDEN
- If a job requires a skill you don't have, rephrase to emphasize skills you DO have instead of adding new ones

Return as JSON:
{{
    "candidates": [
        {{
            "text": "...",
            "score": {{
                "job_skill_coverage": 0.85,
                "ats_keyword_gain": 3,
                "semantic_similarity": 0.90,
                "constraint_violations": 0
            }},
            "diff_from_original": {{
                "added": ["Linux", "pipelines"],
                "removed": []
            }},
            "justification": {{
                "job_requirements_addressed": ["Linux experience", "Automation"],
                "skills_mapped": ["Python", "Linux", "Automation"],
                "why_this_version": "Maximizes required skill coverage without introducing new experience claims"
            }},
            "rewrite_intent": "{rewrite_intent or 'emphasize_skills'}"
        }},
        ...
    ]
}}"""

