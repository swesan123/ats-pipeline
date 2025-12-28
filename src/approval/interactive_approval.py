"""Interactive approval workflow for resume bullet changes."""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from src.models.resume import Resume, Bullet, Reasoning, BulletHistory
from src.compilation.resume_rewriter import ResumeRewriter


class InteractiveApproval:
    """Interactive approval workflow for bullet changes."""
    
    def approve_bullet_changes(
        self,
        original: Bullet,
        reasoning: Reasoning,
        variations: List[Bullet],
    ) -> Optional[Bullet]:
        """Display reasoning and variations, get user approval.
        
        Returns: Approved Bullet or None if rejected.
        """
        # Display reasoning chain
        self._display_reasoning(reasoning)
        
        # Display original
        print("\n" + "="*80)
        print("ORIGINAL BULLET:")
        print(f"  {original.text}")
        print("="*80)
        
        # Display variations
        print("\nVARIATIONS:")
        for i, variation in enumerate(variations, 1):
            print(f"\n[{i}] {variation.text}")
            if variation.history:
                justification = variation.history[0].justification
                print(f"    Trigger: {justification.trigger}")
                if justification.skills_added:
                    print(f"    Skills added: {', '.join(justification.skills_added)}")
                if justification.ats_keywords_added:
                    print(f"    ATS keywords: {', '.join(justification.ats_keywords_added)}")
        
        # Get user input
        while True:
            choice = input("\n[y/n/r/1-4]: ").strip().lower()
            
            if choice == 'y' or choice == '':
                # Approve variation 1 (default)
                selected = variations[0]
                selected_variation_index = 0
                break
            elif choice == 'n':
                # Reject all, keep original
                return None
            elif choice == 'r':
                # Retry with feedback
                feedback = input("Enter feedback: ").strip()
                # Note: In a real implementation, this would call ResumeRewriter with feedback
                print("Regenerating variations with feedback...")
                # For now, just return None to indicate retry needed
                return self._retry_with_feedback(original, reasoning, variations, feedback)
            elif choice in ['1', '2', '3', '4']:
                # Select specific variation
                idx = int(choice) - 1
                if 0 <= idx < len(variations):
                    selected = variations[idx]
                    selected_variation_index = idx
                    break
                else:
                    print("Invalid variation number. Please try again.")
            else:
                print("Invalid choice. Please enter y, n, r, or 1-4.")
        
        # Create BulletHistory entry
        history_entry = BulletHistory(
            original_text=original.text,
            new_text=selected.text,
            justification=selected.history[0].justification if selected.history else None,
            reasoning=reasoning,
            approved_by_human=True,
            timestamp=datetime.now(),
            selected_variation_index=selected_variation_index,
        )
        
        # Update bullet with approved text and history
        approved_bullet = Bullet(
            text=selected.text,
            skills=selected.skills,
            evidence=selected.evidence,
            history=original.history + [history_entry],
        )
        
        return approved_bullet
    
    def _display_reasoning(self, reasoning: Reasoning) -> None:
        """Display reasoning chain."""
        print("\n" + "="*80)
        print("REASONING CHAIN:")
        print("="*80)
        print(f"\nProblem Identification:")
        print(f"  {reasoning.problem_identification}")
        print(f"\nAnalysis:")
        print(f"  {reasoning.analysis}")
        print(f"\nSolution Approach:")
        print(f"  {reasoning.solution_approach}")
        print(f"\nEvaluation:")
        print(f"  {reasoning.evaluation}")
        if reasoning.alternatives_considered:
            print(f"\nAlternatives Considered:")
            for alt in reasoning.alternatives_considered:
                print(f"  - {alt}")
        print(f"\nConfidence Score: {reasoning.confidence_score:.1%}")
        print("="*80)
    
    def _retry_with_feedback(
        self,
        original: Bullet,
        reasoning: Reasoning,
        variations: List[Bullet],
        feedback: str,
    ) -> Optional[Bullet]:
        """Retry variation generation with user feedback."""
        # This would integrate with ResumeRewriter to regenerate
        # For now, return None to indicate retry is needed
        print(f"Feedback received: {feedback}")
        print("(Retry functionality requires ResumeRewriter integration)")
        return None


class ResumeApprovalWorkflow:
    """Orchestrate approval workflow for entire resume rewrite."""
    
    def __init__(self, rewriter: Optional[ResumeRewriter] = None):
        """Initialize workflow with optional rewriter for retries."""
        self.approval = InteractiveApproval()
        self.rewriter = rewriter
    
    def process_resume_rewrite(
        self,
        resume: Resume,
        rewrite_proposals: Dict[str, Tuple[Reasoning, List[Bullet]]],
    ) -> Resume:
        """Process resume rewrite proposals with interactive approval.
        
        Returns: Updated Resume with approved changes.
        """
        # Create a copy of resume to modify
        updated_resume = resume.model_copy(deep=True)
        
        # Process each bullet proposal
        bullet_id = 0
        for exp_item in updated_resume.experience:
            for bullet in exp_item.bullets:
                bullet_key = f"exp_{exp_item.organization}_{bullet_id}"
                if bullet_key in rewrite_proposals:
                    reasoning, variations = rewrite_proposals[bullet_key]
                    approved = self.approval.approve_bullet_changes(
                        bullet, reasoning, variations
                    )
                    if approved:
                        # Update bullet in place
                        bullet.text = approved.text
                        bullet.skills = approved.skills
                        bullet.history = approved.history
                bullet_id += 1
        
        bullet_id = 0
        for project in updated_resume.projects:
            for bullet in project.bullets:
                bullet_key = f"proj_{project.name}_{bullet_id}"
                if bullet_key in rewrite_proposals:
                    reasoning, variations = rewrite_proposals[bullet_key]
                    approved = self.approval.approve_bullet_changes(
                        bullet, reasoning, variations
                    )
                    if approved:
                        bullet.text = approved.text
                        bullet.skills = approved.skills
                        bullet.history = approved.history
                bullet_id += 1
        
        # Update skills section based on all skills mentioned in bullets
        self._update_skills_section(updated_resume)
        
        # Update resume metadata
        updated_resume.version += 1
        updated_resume.date_updated = datetime.now()
        
        return updated_resume
    
    def _update_skills_section(self, resume: Resume) -> None:
        """Update skills section based on skills mentioned in all bullets."""
        # Collect all unique skills from experience and projects
        all_skills = set()
        
        # Collect from experience bullets
        for exp in resume.experience:
            for bullet in exp.bullets:
                all_skills.update(bullet.skills)
        
        # Collect from project bullets
        for project in resume.projects:
            all_skills.update(project.tech_stack)  # Tech stack is also skills
            for bullet in project.bullets:
                all_skills.update(bullet.skills)
        
        # Common skill categories and their typical skills
        skill_categories = {
            "Languages": ["Python", "Java", "C", "C++", "C#", "JavaScript", "TypeScript", "Go", "Golang", "Swift", "Kotlin", "Rust", "Ruby", "PHP", "SQL", "R", "MATLAB"],
            "ML/AI": ["NumPy", "pandas", "scikit-learn", "TensorFlow", "PyTorch", "Keras", "Matplotlib", "Seaborn", "Jupyter", "Pandas"],
            "Mobile/Web": ["React", "React Native", "Vue", "Angular", "Node.js", "Express", "Django", "Flask", "FastAPI", "Next.js", "HTML", "CSS", "Tailwind", "Bootstrap"],
            "Backend/DB": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Docker", "Kubernetes", "AWS", "GCP", "Azure", "tRPC", "GraphQL", "REST", "JWT", "Drizzle"],
            "DevOps": ["Docker", "Kubernetes", "Jenkins", "GitLab CI", "GitHub Actions", "Terraform", "Ansible", "Linux", "Bash", "Shell"]
        }
        
        # Categorize skills
        categorized_skills = {category: [] for category in skill_categories.keys()}
        uncategorized = []
        
        for skill in all_skills:
            skill_lower = skill.lower()
            categorized = False
            
            # Try to match skill to a category
            for category, typical_skills in skill_categories.items():
                for typical in typical_skills:
                    if typical.lower() in skill_lower or skill_lower in typical.lower():
                        if skill not in categorized_skills[category]:
                            categorized_skills[category].append(skill)
                        categorized = True
                        break
                if categorized:
                    break
            
            if not categorized:
                uncategorized.append(skill)
        
        # Update resume skills, preserving existing structure but adding new skills
        for category, skills_list in categorized_skills.items():
            if category not in resume.skills:
                resume.skills[category] = []
            # Add new skills that aren't already there
            for skill in skills_list:
                if skill not in resume.skills[category]:
                    resume.skills[category].append(skill)
        
        # Add uncategorized skills to "Languages" if they look like languages
        if uncategorized:
            # Simple heuristic: if it's a common programming language name, add to Languages
            common_langs = ["golang", "swift", "kotlin", "rust", "ruby", "php", "r", "matlab", "scala", "clojure"]
            for skill in uncategorized:
                if any(lang in skill.lower() for lang in common_langs):
                    if "Languages" not in resume.skills:
                        resume.skills["Languages"] = []
                    if skill not in resume.skills["Languages"]:
                        resume.skills["Languages"].append(skill)

