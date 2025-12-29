"""Bullet scoring and ranking system."""

from typing import List, Dict
from src.models.resume import BulletCandidate
from src.models.job import JobMatch


class BulletScorer:
    """Score and rank bullet candidates."""
    
    def __init__(self):
        """Initialize scorer."""
        pass
    
    def score_bullet(
        self,
        candidate: BulletCandidate,
        original_text: str,
        job_match: JobMatch,
    ) -> float:
        """Calculate composite score for a bullet candidate.
        
        Formula:
        score = 0.4 * job_skill_coverage + 0.3 * semantic_similarity + 0.2 * ats_keyword_gain - 0.1 * constraint_violations
        
        Args:
            candidate: The bullet candidate to score
            original_text: Original bullet text for comparison
            job_match: Job match information
            
        Returns:
            Composite score (0.0-1.0)
        """
        score_components = candidate.score
        
        job_skill_coverage = score_components.get("job_skill_coverage", 0.0)
        semantic_similarity = score_components.get("semantic_similarity", 0.0)
        ats_keyword_gain = score_components.get("ats_keyword_gain", 0.0)
        constraint_violations = score_components.get("constraint_violations", 0.0)
        
        # Normalize ats_keyword_gain (assume max 10 keywords = 1.0)
        ats_keyword_gain = min(ats_keyword_gain / 10.0, 1.0) if ats_keyword_gain > 0 else 0.0
        
        # Normalize constraint_violations (assume max 5 violations = 1.0)
        constraint_violations = min(constraint_violations / 5.0, 1.0) if constraint_violations > 0 else 0.0
        
        # Calculate composite score
        composite = (
            0.4 * job_skill_coverage +
            0.3 * semantic_similarity +
            0.2 * ats_keyword_gain -
            0.1 * constraint_violations
        )
        
        # Ensure score is between 0.0 and 1.0
        return max(0.0, min(1.0, composite))
    
    def rank_candidates(
        self,
        candidates: List[BulletCandidate],
        original_text: str,
        job_match: JobMatch,
    ) -> List[BulletCandidate]:
        """Rank candidates by composite score.
        
        Args:
            candidates: List of bullet candidates to rank
            original_text: Original bullet text
            job_match: Job match information
            
        Returns:
            Sorted list of candidates (highest score first)
        """
        # Calculate composite scores
        scored_candidates = []
        for candidate in candidates:
            composite_score = self.score_bullet(candidate, original_text, job_match)
            # Update candidate with composite score
            candidate.composite_score = composite_score
            scored_candidates.append(candidate)
        
        # Sort by composite score (descending)
        scored_candidates.sort(key=lambda c: c.composite_score, reverse=True)
        
        return scored_candidates
    
    def calculate_risk_level(
        self,
        candidate: BulletCandidate,
        original_text: str,
    ) -> str:
        """Calculate risk level based on scope expansion and skill additions.
        
        Args:
            candidate: The bullet candidate
            original_text: Original bullet text
            
        Returns:
            Risk level: "low", "medium", or "high"
        """
        added = candidate.diff_from_original.get("added", [])
        removed = candidate.diff_from_original.get("removed", [])
        
        # Count skill additions
        skills_added = len([item for item in added if any(keyword in item.lower() for keyword in ["skill", "technology", "tool", "framework", "language"])])
        
        # Check for scope expansion keywords
        expansion_keywords = ["led", "managed", "architected", "designed", "built", "created", "established", "founded"]
        original_lower = original_text.lower()
        candidate_lower = candidate.text.lower()
        
        scope_expansion = 0
        for keyword in expansion_keywords:
            if keyword in candidate_lower and keyword not in original_lower:
                scope_expansion += 1
        
        # Determine risk level
        if skills_added == 0 and scope_expansion == 0 and len(removed) == 0:
            return "low"
        elif skills_added <= 2 and scope_expansion == 0:
            return "medium"
        else:
            return "high"

