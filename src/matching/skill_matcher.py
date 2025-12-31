"""Skill matching engine for comparing resumes to job requirements."""

from typing import Dict, List
from src.models.resume import Resume, Bullet
from src.models.job import JobSkills, JobMatch
from src.models.skills import SkillOntology


class SkillMatcher:
    """Match job requirements against resume skills."""
    
    def __init__(self, ontology: SkillOntology):
        """Initialize matcher with skill ontology."""
        self.ontology = ontology
    
    def match_job(self, resume: Resume, job_skills: JobSkills) -> JobMatch:
        """Match resume against job requirements and calculate fit score."""
        # Extract skills from resume
        resume_skills = self._extract_resume_skills(resume)
        
        # Calculate fit score
        fit_score = self._calculate_fit_score(resume_skills, job_skills)
        
        # Generate gap analysis
        skill_gaps, missing_skills, matching_skills = self._analyze_gaps(
            resume_skills, job_skills
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            skill_gaps, missing_skills, matching_skills, job_skills
        )
        
        return JobMatch(
            fit_score=fit_score,
            skill_gaps=skill_gaps,
            missing_skills=missing_skills,
            matching_skills=matching_skills,
            recommendations=recommendations,
        )
    
    def _extract_resume_skills(self, resume: Resume) -> Dict[str, List[str]]:
        """Extract all skills from resume with evidence."""
        skills_dict = {
            "technical": [],
            "soft": [],
            "domain": [],
        }
        
        # Extract from skills section
        for category, skill_list in resume.skills.items():
            category_lower = category.lower()
            # Match new category names: Languages, ML/AI, Mobile/Web, Backend/DB, DevOps, Operating Systems, Security, Tools
            if ("language" in category_lower or "ml" in category_lower or "ai" in category_lower or 
                "mobile" in category_lower or "web" in category_lower or "backend" in category_lower or 
                "db" in category_lower or "devops" in category_lower or "operating" in category_lower or 
                "security" in category_lower or "tools" in category_lower):
                skills_dict["technical"].extend(skill_list)
            elif "soft" in category_lower:
                skills_dict["soft"].extend(skill_list)
            else:
                skills_dict["domain"].extend(skill_list)
        
        # Extract from experience bullets
        for exp_item in resume.experience:
            for bullet in exp_item.bullets:
                skills_dict["technical"].extend(bullet.skills)
        
        # Extract from project bullets
        for project in resume.projects:
            for bullet in project.bullets:
                skills_dict["technical"].extend(bullet.skills)
            skills_dict["technical"].extend(project.tech_stack)
        
        # Normalize and deduplicate
        for key in skills_dict:
            skills_dict[key] = list(set(s.lower().strip() for s in skills_dict[key] if s.strip()))

        return skills_dict
    
    def _calculate_fit_score(
        self, resume_skills: Dict[str, List[str]], job_skills: JobSkills
    ) -> float:
        """Calculate weighted fit score."""
        # Normalize job skills
        required = [s.lower().strip() for s in job_skills.required_skills]
        preferred = [s.lower().strip() for s in job_skills.preferred_skills]
        soft = [s.lower().strip() for s in job_skills.soft_skills]
        
        # Get all resume skills (flattened)
        all_resume_skills = []
        for skill_list in resume_skills.values():
            all_resume_skills.extend(skill_list)
        
        # Count matches
        required_matches = sum(1 for skill in required if self._skill_matches(skill, all_resume_skills))
        preferred_matches = sum(1 for skill in preferred if self._skill_matches(skill, all_resume_skills))
        soft_matches = sum(1 for skill in soft if self._skill_matches(skill, all_resume_skills))
        
        # Calculate weighted score
        total_required = len(required) if required else 1
        total_preferred = len(preferred) if preferred else 1
        total_soft = len(soft) if soft else 1
        
        # Weighted: required × 2.0, preferred × 1.0, soft × 0.5
        score = (
            (required_matches / total_required) * 2.0 +
            (preferred_matches / total_preferred) * 1.0 +
            (soft_matches / total_soft) * 0.5
        ) / 3.5  # Normalize by total weight
        return min(1.0, max(0.0, score))
    
    def _skill_matches(self, job_skill: str, resume_skills: List[str]) -> bool:
        """Check if job skill matches any resume skill (with normalization)."""
        job_skill_normalized = self.ontology.normalize_skill_name(job_skill)
        
        # Direct match
        if job_skill_normalized in resume_skills:
            return True
        
        # Check ontology for aliases/synonyms
        skill_obj = self.ontology.find_skill(job_skill)
        if skill_obj:
            skill_name_normalized = self.ontology.normalize_skill_name(skill_obj.name)
            if skill_name_normalized in resume_skills:
                return True
        
        # Partial match (contains)
        for resume_skill in resume_skills:
            if job_skill_normalized in resume_skill or resume_skill in job_skill_normalized:
                return True
        
        return False
    
    def _analyze_gaps(
        self, resume_skills: Dict[str, List[str]], job_skills: JobSkills
    ) -> tuple[Dict[str, List[str]], List[str], List[str]]:
        """Analyze skill gaps between resume and job requirements."""
        all_resume_skills = []
        for skill_list in resume_skills.values():
            all_resume_skills.extend(skill_list)
        
        skill_gaps = {
            "required_missing": [],
            "preferred_missing": [],
            "soft_missing": [],
        }
        missing_skills = []
        matching_skills = []
        
        # Check required skills
        for skill in job_skills.required_skills:
            skill_normalized = skill.lower().strip()
            if self._skill_matches(skill, all_resume_skills):
                matching_skills.append(skill)
            else:
                skill_gaps["required_missing"].append(skill)
                # Check if skill exists in ontology
                if not self.ontology.find_skill(skill):
                    missing_skills.append(skill)
        
        # Check preferred skills
        for skill in job_skills.preferred_skills:
            skill_normalized = skill.lower().strip()
            if self._skill_matches(skill, all_resume_skills):
                matching_skills.append(skill)
            else:
                skill_gaps["preferred_missing"].append(skill)
        
        # Check soft skills
        for skill in job_skills.soft_skills:
            skill_normalized = skill.lower().strip()
            if self._skill_matches(skill, all_resume_skills):
                matching_skills.append(skill)
            else:
                skill_gaps["soft_missing"].append(skill)
        
        return skill_gaps, missing_skills, matching_skills
    
    def _generate_recommendations(
        self,
        skill_gaps: Dict[str, List[str]],
        missing_skills: List[str],
        matching_skills: List[str],
        job_skills: JobSkills,
    ) -> List[str]:
        """Generate recommendations for improving fit."""
        recommendations = []
        
        if skill_gaps["required_missing"]:
            recommendations.append(
                f"Add {len(skill_gaps['required_missing'])} required skills to resume: "
                f"{', '.join(skill_gaps['required_missing'][:3])}"
            )
        
        if skill_gaps["preferred_missing"]:
            recommendations.append(
                f"Consider adding {len(skill_gaps['preferred_missing'])} preferred skills: "
                f"{', '.join(skill_gaps['preferred_missing'][:3])}"
            )
        
        if missing_skills:
            recommendations.append(
                f"Learn or gain experience with: {', '.join(missing_skills[:3])}"
            )
        
        if not recommendations:
            recommendations.append("Resume matches job requirements well!")
        
        return recommendations

