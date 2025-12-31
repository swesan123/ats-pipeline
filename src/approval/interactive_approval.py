"""Interactive approval workflow for resume bullet changes."""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from src.models.resume import Resume, Bullet, Reasoning, BulletHistory, BulletCandidate, Justification
from src.compilation.resume_rewriter import ResumeRewriter


class InteractiveApproval:
    """Interactive approval workflow for bullet changes."""
    
    def approve_bullet_changes(
        self,
        original: Bullet,
        reasoning: Reasoning,
        candidates: List[BulletCandidate],
        rewriter: Optional[ResumeRewriter] = None,
    ) -> Optional[Bullet]:
        """Display reasoning and ranked candidates, get user approval.
        
        Args:
            original: Original bullet
            reasoning: Reasoning chain
            candidates: Ranked list of BulletCandidate objects
            rewriter: Optional rewriter for retry with rewrite intents
        
        Returns: Approved Bullet or None if rejected.
        """
        # Display reasoning chain
        self._display_reasoning(reasoning)
        
        # Display original
        print("\n" + "="*80)
        print("ORIGINAL BULLET:")
        print(f"  {original.text}")
        print("="*80)
        
        # Display ranked candidates
        if not candidates:
            print("\nNo valid candidates generated.")
            return None
        
        # Primary candidate (top ranked)
        primary = candidates[0]
        print("\n" + "="*80)
        print(f"RECOMMENDED (Score: {primary.composite_score:.2f}, Risk: {primary.risk_level}):")
        print(f"  {primary.text}")
        print(f"  Covers: {', '.join(primary.justification.get('job_requirements_addressed', [])[:5])}")
        print(f"  ATS keywords added: {primary.score.get('ats_keyword_gain', 0)}")
        print("="*80)
        
        # Alternatives (if any)
        if len(candidates) > 1:
            print("\nALTERNATIVES:")
            for i, candidate in enumerate(candidates[1:3], 1):  # Show up to 2 alternatives
                print(f"\n[{chr(64+i)}] {candidate.text} (Score: {candidate.composite_score:.2f}, Risk: {candidate.risk_level})")
                if candidate.rewrite_intent:
                    intent_map = {
                        "emphasize_skills": "Emphasizes skills",
                        "more_technical": "More technical",
                        "more_concise": "More concise",
                        "conservative": "Conservative"
                    }
                    print(f"    {intent_map.get(candidate.rewrite_intent, candidate.rewrite_intent)}")
        
        # Get user input
        while True:
            print("\nOptions:")
            print("  [y] Accept recommended")
            if len(candidates) > 1:
                print(f"  [a] Alternative A" + (f" / [b] Alternative B" if len(candidates) > 2 else ""))
            print("  [r] Emphasize skills")
            print("  [t] Make more technical")
            print("  [c] Make more concise")
            print("  [s] Conservative rewrite")
            print("  [x] Reject")
            choice = input("\nChoose: ").strip().lower()
            
            if choice == 'y' or choice == '':
                # Accept primary candidate
                selected = primary
                selected_index = 0
                break
            elif choice == 'a' and len(candidates) > 1:
                selected = candidates[1]
                selected_index = 1
                break
            elif choice == 'b' and len(candidates) > 2:
                selected = candidates[2]
                selected_index = 2
                break
            elif choice == 'x' or choice == 'n':
                # Reject all, keep original
                # Track rejection event (if db available via rewriter)
                if rewriter:
                    try:
                        from src.analytics.event_tracker import EventTracker
                        from src.db.database import Database
                        # Note: This requires db access - would need to pass db or get from rewriter
                        # For now, tracking will be done at a higher level
                    except Exception:
                        pass
                return None
            elif choice in ['r', 't', 'c', 's']:
                # Rewrite with specific intent
                intent_map = {
                    'r': 'emphasize_skills',
                    't': 'more_technical',
                    'c': 'more_concise',
                    's': 'conservative'
                }
                if rewriter:
                    # Regenerate with intent
                    print(f"Regenerating with intent: {intent_map[choice]}...")
                    # This would need job_match and ontology - for now, return None to indicate retry
                    return None
                else:
                    print("Rewriter not available for retry.")
                    continue
            else:
                print("Invalid choice. Please try again.")
        
        # Extract skills from candidate justification
        skills_mapped = selected.justification.get("skills_mapped", [])
        
        # Create Justification object
        justification = Justification(
            trigger=reasoning.problem_identification,
            skills_added=selected.diff_from_original.get("added", []),
            ats_keywords_added=[],  # Would need to extract from score
        )
        
        # Create BulletHistory entry
        history_entry = BulletHistory(
            original_text=original.text,
            new_text=selected.text,
            justification=justification,
            reasoning=reasoning,
            approved_by_human=True,
            timestamp=datetime.now(),
            selected_variation_index=selected_index,
            candidate_id=selected.candidate_id,
            decision_metadata={
                "composite_score": selected.composite_score,
                "risk_level": selected.risk_level,
                "rewrite_intent": selected.rewrite_intent,
                "score_components": selected.score,
            },
        )
        
        # Update bullet with approved text and history
        approved_bullet = Bullet(
            text=selected.text,
            skills=skills_mapped if skills_mapped else original.skills,
            evidence=original.evidence,
            history=original.history + [history_entry],
        )
        
        # Track approval event (if db available via rewriter)
        if rewriter:
            try:
                from src.analytics.event_tracker import EventTracker
                from src.db.database import Database
                # Note: This requires db access - tracking will be done at GUI/CLI level
            except Exception:
                pass
        
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
        candidates: List[BulletCandidate],
        feedback: str,
    ) -> Optional[Bullet]:
        """Retry candidate generation with user feedback."""
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
        rewrite_proposals: Dict[str, Tuple[Reasoning, List[BulletCandidate]]],
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
    
    def _update_skills_section(self, resume: Resume, job_skills: Optional[List[str]] = None) -> None:
        """Update skills section based on skills mentioned in all bullets.
        
        Args:
            resume: Resume to update
            job_skills: Optional list of job-relevant skills to prioritize
        """
        from src.utils.skill_categorizer import categorize_skills
        
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
        
        # Categorize skills using shared utility
        categorized_skills = categorize_skills(list(all_skills), job_skills)
        
        # Update resume skills, replacing with categorized version
        # This removes skills that are no longer mentioned in any bullet
        resume.skills = categorized_skills

