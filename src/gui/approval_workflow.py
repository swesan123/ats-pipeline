"""Interactive approval workflow GUI component."""

import sys
from pathlib import Path
from typing import Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

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
    col1, col2 = st.columns(2)
    
    with col1:
        approve_btn = st.button("Approve", type="primary", key=f"approve_{bullet_num}")
        if approve_btn:
            st.session_state[f'approved_{bullet_num}'] = selected_variation
            return True, selected_variation
    
    with col2:
        reject_btn = st.button("Reject", key=f"reject_{bullet_num}")
        if reject_btn:
            st.session_state[f'rejected_{bullet_num}'] = True
            return False, None
    
    # Check if already approved/rejected in this session
    if f'approved_{bullet_num}' in st.session_state:
        return True, st.session_state[f'approved_{bullet_num}']
    if f'rejected_{bullet_num}' in st.session_state:
        return False, None
    
    return None, None

