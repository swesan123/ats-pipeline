"""Interactive approval workflow GUI component."""

import sys
from pathlib import Path
from typing import Optional, List, Callable

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from src.models.resume import Bullet, Reasoning, BulletCandidate
from src.compilation.bullet_feedback import BulletFeedbackStore


def render_approval_workflow(
    original: Bullet,
    reasoning: Reasoning,
    candidates: List[BulletCandidate],
    bullet_num: int,
    total_bullets: int,
    regenerate_callback: Optional[Callable[[str], None]] = None,
    rewrite_intent: Optional[str] = None,
) -> tuple[bool, Optional[int], Optional[str]]:
    """Render approval workflow UI with ranked candidates.
    
    Args:
        original: Original bullet
        reasoning: Reasoning chain
        candidates: Ranked list of BulletCandidate objects
        bullet_num: Current bullet number
        total_bullets: Total number of bullets
        regenerate_callback: Optional callback for rewrite intents (takes intent: str)
        rewrite_intent: Current rewrite intent mode
    
    Returns: (approved, selected_candidate_index, rewrite_intent)
    - approved: True if approved, False if rejected, None if pending
    - selected_candidate_index: Index of selected candidate if approved, None otherwise
    - rewrite_intent: Intent string if regeneration requested, None otherwise
    """
    st.progress(bullet_num / total_bullets, text=f"Processing bullet {bullet_num} of {total_bullets}")
    
    st.subheader(f"Bullet {bullet_num} of {total_bullets}")
    
    # Display rewrite mode selector
    if regenerate_callback:
        st.write("**Rewrite Mode:**")
        mode_options = ["emphasize_skills", "reword_only", "more_technical", "more_concise", "conservative"]
        mode_labels = {
            "emphasize_skills": "Emphasize Skills (add job keywords)",
            "reword_only": "Reword Only (no new skills)",
            "more_technical": "More Technical",
            "more_concise": "More Concise",
            "conservative": "Conservative"
        }
        current_mode = rewrite_intent or "emphasize_skills"
        selected_mode = st.radio(
            "Select rewrite mode:",
            options=mode_options,
            format_func=lambda x: mode_labels.get(x, x),
            index=mode_options.index(current_mode) if current_mode in mode_options else 0,
            key=f"rewrite_mode_{bullet_num}",
        )
        if selected_mode != current_mode:
            # Mode changed - trigger regeneration
            return None, None, selected_mode
    
    # Display original
    st.write("**Original Bullet:**")
    st.write(original.text)
    
    # Display reasoning chain (expandable)
    with st.expander("Reasoning Chain", expanded=False):
        st.write("**Problem Identification:**")
        st.write(reasoning.problem_identification)
        
        st.write("**Analysis:**")
        st.write(reasoning.analysis)
        
        st.write("**Solution Approach:**")
        st.write(reasoning.solution_approach)
        
        st.write("**Evaluation:**")
        st.write(reasoning.evaluation)
        
        if reasoning.alternatives_considered:
            st.write("**Alternatives Considered:**")
            for alt in reasoning.alternatives_considered:
                st.write(f"- {alt}")
        
        st.progress(reasoning.confidence_score, text=f"Confidence: {reasoning.confidence_score:.1%}")
    
    if not candidates:
        st.warning("No valid candidates generated for this bullet.")
        if st.button("Reject", key=f"reject_{bullet_num}"):
            return False, None, None
        return None, None, None
    
    # Display primary candidate (top ranked)
    primary = candidates[0]
    
    # Risk level color coding
    risk_colors = {
        "low": "🟢",
        "medium": "🟡",
        "high": "🔴"
    }
    risk_emoji = risk_colors.get(primary.risk_level, "⚪")
    
    st.write("---")
    st.write(f"**Recommended** {risk_emoji} (Score: {primary.composite_score:.2f}, Risk: {primary.risk_level.upper()})")
    st.write(primary.text)
    
    # Show metadata for primary
    with st.expander("Candidate Details", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Score Components:**")
            st.write(f"- Job Skill Coverage: {primary.score.get('job_skill_coverage', 0.0):.2f}")
            st.write(f"- ATS Keyword Gain: {primary.score.get('ats_keyword_gain', 0)}")
            st.write(f"- Semantic Similarity: {primary.score.get('semantic_similarity', 0.0):.2f}")
            st.write(f"- Constraint Violations: {primary.score.get('constraint_violations', 0)}")
        
        with col2:
            st.write("**Changes:**")
            added = primary.diff_from_original.get("added", [])
            removed = primary.diff_from_original.get("removed", [])
            if added:
                st.write(f"Added: {', '.join(added[:5])}")
            if removed:
                st.write(f"Removed: {', '.join(removed[:5])}")
        
        st.write("**Justification:**")
        st.write(primary.justification.get("why_this_version", ""))
        if primary.justification.get("job_requirements_addressed"):
            st.write(f"Addresses: {', '.join(primary.justification['job_requirements_addressed'][:5])}")
    
    # Display alternatives (if any)
    if len(candidates) > 1:
        st.write("---")
        st.write("**Alternatives:**")
        for i, candidate in enumerate(candidates[1:3], 1):  # Show up to 2 alternatives
            risk_emoji_alt = risk_colors.get(candidate.risk_level, "⚪")
            intent_label = ""
            if candidate.rewrite_intent:
                intent_map = {
                    "emphasize_skills": "Emphasizes skills",
                    "more_technical": "More technical",
                    "more_concise": "More concise",
                    "conservative": "Conservative"
                }
                intent_label = f" ({intent_map.get(candidate.rewrite_intent, candidate.rewrite_intent)})"
            
            with st.expander(f"Alternative {chr(64+i)} {risk_emoji_alt} (Score: {candidate.composite_score:.2f}, Risk: {candidate.risk_level.upper()}){intent_label}", expanded=False):
                st.write(candidate.text)
                st.caption(f"ATS keywords: {candidate.score.get('ats_keyword_gain', 0)} | Similarity: {candidate.score.get('semantic_similarity', 0.0):.2f}")
    
    # Candidate selection
    candidate_options = ["Recommended"] + [f"Alternative {chr(64+i)}" for i in range(1, min(len(candidates), 3))]
    selected_option = st.radio(
        "Select candidate:",
        options=range(len(candidate_options)),
        format_func=lambda i: candidate_options[i],
        key=f"candidate_select_{bullet_num}",
    )
    
    selected_candidate = candidates[selected_option]
    
    # Action buttons
    col1, col2, col3, col4, col5 = st.columns(5)
    feedback_store = BulletFeedbackStore()
    
    with col1:
        approve_btn = st.button("Accept", type="primary", key=f"approve_{bullet_num}")
        if approve_btn:
            st.session_state[f'approved_{bullet_num}'] = selected_option
            # Record feedback for future generations
            feedback_store.record_feedback(
                action="accepted",
                candidate=selected_candidate,
                rewrite_intent=selected_candidate.rewrite_intent,
            )
            return True, selected_option, None
    
    with col2:
        reject_btn = st.button("Reject", key=f"reject_{bullet_num}")
        if reject_btn:
            st.session_state[f'rejected_{bullet_num}'] = True
            feedback_store.record_feedback(
                action="rejected",
                candidate=primary,
                rewrite_intent=primary.rewrite_intent,
            )
            return False, None, None
    
    # Rewrite intent buttons
    if regenerate_callback:
        with col3:
            if st.button("Emphasize Skills", key=f"intent_r_{bullet_num}"):
                return None, None, "emphasize_skills"
        with col4:
            if st.button("More Technical", key=f"intent_t_{bullet_num}"):
                return None, None, "more_technical"
        with col5:
            if st.button("More Concise", key=f"intent_c_{bullet_num}"):
                return None, None, "more_concise"
        
        # Conservative button on next row
        col6, col7 = st.columns(2)
        with col6:
            if st.button("Conservative", key=f"intent_s_{bullet_num}"):
                return None, None, "conservative"
    
    # Check if already approved/rejected in this session
    if f'approved_{bullet_num}' in st.session_state:
        return True, st.session_state[f'approved_{bullet_num}'], None
    if f'rejected_{bullet_num}' in st.session_state:
        return False, None, None
    
    return None, None, None

