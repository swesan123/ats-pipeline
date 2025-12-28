"""Skills management section for GUI."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import json
from src.models.skills import UserSkills, UserSkill
from src.projects.project_library import ProjectLibrary


def render_skills_section():
    """Render skills management section."""
    st.header("Skills")
    
    skills_file = Path("data/user_skills.json")
    
    # Load existing skills
    user_skills = UserSkills(skills=[])
    if skills_file.exists():
        try:
            with open(skills_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                user_skills = UserSkills.model_validate(data)
        except Exception as e:
            st.warning(f"Could not load existing skills: {e}")
    
    # Get available projects for skill-project mapping
    library = ProjectLibrary()
    projects = library.get_all_projects()
    project_names = [p.name for p in projects]
    
    # Add new skill form
    with st.expander("Add New Skill", expanded=False):
        with st.form("add_skill_form"):
            skill_name = st.text_input("Skill Name", key="skill_name", 
                                      help="e.g., Python, TensorFlow, React")
            category = st.selectbox("Category", 
                                   ["Languages", "ML/AI", "Mobile/Web", "Backend/DB", "DevOps", "Other"],
                                   key="skill_category")
            proficiency = st.selectbox("Proficiency Level",
                                      ["beginner", "intermediate", "advanced", "expert"],
                                      key="skill_proficiency")
            
            # Project selection (multi-select)
            selected_projects = st.multiselect("Associated Projects",
                                               project_names,
                                               key="skill_projects",
                                               help="Select projects that demonstrate this skill")
            
            submitted = st.form_submit_button("Add Skill", type="primary")
            
            if submitted:
                if not skill_name:
                    st.error("Skill name is required")
                else:
                    # Check if skill already exists
                    existing_skill = next((s for s in user_skills.skills if s.name.lower() == skill_name.lower()), None)
                    
                    if existing_skill:
                        # Update existing skill
                        existing_skill.category = category
                        existing_skill.proficiency_level = proficiency
                        existing_skill.projects = selected_projects
                        st.success(f"Skill '{skill_name}' updated!")
                    else:
                        # Add new skill
                        new_skill = UserSkill(
                            name=skill_name,
                            category=category,
                            proficiency_level=proficiency,
                            projects=selected_projects
                        )
                        user_skills.skills.append(new_skill)
                        st.success(f"Skill '{skill_name}' added!")
                    
                    # Save to file
                    with open(skills_file, 'w', encoding='utf-8') as f:
                        json.dump(user_skills.model_dump(), f, indent=2, default=str)
                    
                    st.rerun()
    
    # Display existing skills by category
    if user_skills.skills:
        st.subheader(f"Your Skills ({len(user_skills.skills)})")
        
        # Group by category
        by_category = {}
        for skill in user_skills.skills:
            cat = skill.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(skill)
        
        for category, skills_list in sorted(by_category.items()):
            with st.expander(f"{category} ({len(skills_list)})", expanded=True):
                for skill in skills_list:
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**{skill.name}**")
                        if skill.projects:
                            st.caption(f"Projects: {', '.join(skill.projects)}")
                    with col2:
                        st.caption(f"Level: {skill.proficiency_level}")
                    with col3:
                        if st.button("Delete", key=f"delete_skill_{skill.name}", type="secondary"):
                            user_skills.skills = [s for s in user_skills.skills if s.name != skill.name]
                            with open(skills_file, 'w', encoding='utf-8') as f:
                                json.dump(user_skills.model_dump(), f, indent=2, default=str)
                            st.success(f"Skill '{skill.name}' deleted")
                            st.rerun()
    else:
        st.info("No skills yet. Add your first skill above!")

