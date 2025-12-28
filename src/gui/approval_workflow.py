"""Interactive approval workflow GUI component."""

from typing import Optional
import streamlit as st
from src.models.resume import Bullet, Reasoning


def render_approval_workflow(
    original: Bullet,
    reasoning: Reasoning,
    variations: list[Bullet],
    bullet_num: int,
    total_bullets: int,
) -> tuple[bool, Optional[int]]:
    """Render approval workflow UI.
    
    Returns: (approved, selected_variation_index)
    - approved: True if approved, False if rejected
    - selected_variation_index: 0-3 if approved, None if rejected
    """
    st.progress(bullet_num / total_bullets, text=f"Processing bullet {bullet_num} of {total_bullets}")
    
    st.subheader(f"Bullet {bullet_num} of {total_bullets}")
    
    # Display original
    st.write("**Original Bullet:**")
    st.write(original.text)
    
    # Display reasoning chain (expandable)
    with st.expander("📋 Reasoning Chain", expanded=False):
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
    
    # Display variations
    st.write("**Variations:**")
    selected_variation = st.radio(
        "Select a variation:",
        options=range(len(variations)),
        format_func=lambda i: f"Variation {i+1}: {variations[i].text[:100]}...",
    )
    
    # Show full text of selected variation
    if selected_variation is not None:
        st.write("**Selected Variation:**")
        st.write(variations[selected_variation].text)
        
        if variations[selected_variation].history:
            justification = variations[selected_variation].history[0].justification
            st.write("**Justification:**")
            st.write(f"Trigger: {justification.trigger}")
            if justification.skills_added:
                st.write(f"Skills added: {', '.join(justification.skills_added)}")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Approve", type="primary"):
            return True, selected_variation
    
    with col2:
        if st.button("❌ Reject"):
            return False, None
    
    with col3:
        if st.button("🔄 Regenerate"):
            feedback = st.text_input("Enter feedback for regeneration:")
            if feedback:
                st.info("Regeneration would happen here with feedback")
                # Would call ResumeRewriter with feedback
                return None, None
    
    return None, None

