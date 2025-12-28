"""Experience management section for GUI."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import json
from src.models.resume import ExperienceItem, Bullet
from src.storage.experience_library import ExperienceLibrary
from datetime import datetime


def render_experience_section():
    """Render experience management section."""
    st.header("Work Experience")
    
    # Load existing experience using library
    exp_library = ExperienceLibrary()
    experience_items = exp_library.get_all_experience()
    
    # Initialize bullet list in session state
    if 'experience_bullets' not in st.session_state:
        st.session_state.experience_bullets = [""]
    
    # Handle remove bullet buttons
    bullets_to_remove = []
    for i in range(len(st.session_state.experience_bullets)):
        if f"remove_exp_bullet_{i}" in st.session_state and st.session_state[f"remove_exp_bullet_{i}"]:
            if len(st.session_state.experience_bullets) > 1:
                bullets_to_remove.append(i)
    
    # Remove bullets
    for idx in sorted(bullets_to_remove, reverse=True):
        st.session_state.experience_bullets.pop(idx)
        if f"experience_bullet_{idx}" in st.session_state:
            del st.session_state[f"experience_bullet_{idx}"]
        if f"remove_exp_bullet_{idx}" in st.session_state:
            del st.session_state[f"remove_exp_bullet_{idx}"]
        st.rerun()
    
    # Add new experience form
    with st.expander("Add New Experience", expanded=False):
        with st.form("add_experience_form"):
            organization = st.text_input("Company/Organization", key="exp_organization")
            role = st.text_input("Job Title/Role", key="exp_role")
            location = st.text_input("Location", key="exp_location", help="e.g., Markham, ON")
            start_date = st.text_input("Start Date (YYYY-MM)", key="exp_start_date", help="e.g., 2024-05")
            end_date = st.text_input("End Date (YYYY-MM or 'Present')", key="exp_end_date", help="e.g., 2025-08 or Present")
            
            st.write("**Bullets:**")
            
            # Display bullets
            for i in range(len(st.session_state.experience_bullets)):
                col1, col2 = st.columns([10, 1])
                with col1:
                    current_value = st.session_state.experience_bullets[i] if i < len(st.session_state.experience_bullets) else ""
                    updated_value = st.text_area(
                        f"Bullet {i+1}",
                        value=current_value,
                        key=f"experience_bullet_{i}",
                        height=80,
                        label_visibility="visible"
                    )
                    if i < len(st.session_state.experience_bullets):
                        st.session_state.experience_bullets[i] = updated_value
                with col2:
                    if len(st.session_state.experience_bullets) > 1:
                        if st.checkbox("×", key=f"remove_exp_check_{i}", help="Remove this bullet", label_visibility="collapsed"):
                            st.session_state[f"remove_exp_bullet_{i}"] = True
                            st.rerun()
            
            submitted = st.form_submit_button("Add Experience", type="primary")
            
            if submitted:
                if not organization or not role:
                    st.error("Company and role are required")
                else:
                    # Format dates
                    start_str = None
                    end_str = None
                    if start_date:
                        try:
                            start_dt = datetime.strptime(start_date, "%Y-%m")
                            start_str = start_dt.strftime("%b %Y")
                        except ValueError:
                            st.error(f"Invalid start date format. Use YYYY-MM")
                            return
                    
                    if end_date and end_date.lower() != 'present':
                        try:
                            end_dt = datetime.strptime(end_date, "%Y-%m")
                            end_str = end_dt.strftime("%b %Y")
                        except ValueError:
                            st.error(f"Invalid end date format. Use YYYY-MM or 'Present'")
                            return
                    elif end_date and end_date.lower() == 'present':
                        end_str = "Present"
                    
                    # Collect bullets
                    bullets = []
                    for i in range(len(st.session_state.experience_bullets)):
                        bullet_text = st.session_state.get(f"experience_bullet_{i}", "")
                        if bullet_text and bullet_text.strip():
                            bullets.append(Bullet(text=bullet_text.strip(), skills=[], evidence=None))
                    
                    if not bullets:
                        st.error("At least one bullet is required")
                        return
                    
                    # Create experience item
                    exp_item = ExperienceItem(
                        organization=organization,
                        role=role,
                        location=location,
                        start_date=start_str,
                        end_date=end_str,
                        bullets=bullets
                    )
                    
                    # Add to library (will handle saving)
                    exp_library.add_experience(exp_item)
                    experience_items = exp_library.get_all_experience()
                    
                    # Clear bullets
                    if 'experience_bullets' in st.session_state:
                        del st.session_state.experience_bullets
                        st.session_state.experience_bullets = [""]
                    
                    st.success(f"Experience at {organization} added successfully!")
                    st.rerun()
    
    # List existing experience
    if experience_items:
        st.subheader(f"Your Experience ({len(experience_items)})")
        
        for i, exp in enumerate(experience_items):
            with st.expander(f"{exp.role} at {exp.organization}", expanded=False):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Location:** {exp.location}")
                    if exp.start_date:
                        end_str = "Present" if not exp.end_date else exp.end_date
                        st.write(f"**Dates:** {exp.start_date} - {end_str}")
                    
                    st.write("**Bullets:**")
                    for j, bullet in enumerate(exp.bullets, 1):
                        st.write(f"{j}. {bullet.text}")
                
                with col2:
                    if st.button("Delete", key=f"delete_exp_{i}", type="secondary"):
                        # Remove from library
                        all_experience = exp_library.get_all_experience()
                        if i < len(all_experience):
                            # Re-save without this item
                            all_experience.pop(i)
                            # Save updated list
                            exp_library._save_experience(all_experience)
                        st.success(f"Experience deleted")
                        st.rerun()
    else:
        st.info("No experience entries yet. Add your first experience above!")

