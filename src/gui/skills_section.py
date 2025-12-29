"""Skills management section for GUI."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import json
import pandas as pd
from typing import List, Dict
from src.models.skills import UserSkills, UserSkill
from src.projects.project_library import ProjectLibrary
from src.db.database import Database
from src.analytics.analytics_service import AnalyticsService


def render_skills_section(db: Database = None):
    """Render skills management section.
    
    Args:
        db: Optional database instance for missing skills analysis
    """
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
                    
                    # Refresh missing skills aggregation if database is available
                    if db:
                        try:
                            analytics = AnalyticsService(db)
                            analytics.refresh_missing_skills_aggregation()
                        except Exception:
                            pass  # Silently fail if refresh doesn't work
                    
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
    
    # Missing Skills Analysis Section
    if db:
        st.divider()
        st.subheader("Missing Skills Analysis")
        st.caption("Skills that appear in job postings but are not yet in your skills list")
        
        # Initialize analytics service
        analytics = AnalyticsService(db)
        
        # Refresh button
        col_refresh, col_spacer = st.columns([1, 10])
        with col_refresh:
            if st.button("Refresh", help="Update missing skills aggregation", key="refresh_missing_skills", width='stretch'):
                with st.spinner("Refreshing skills aggregation..."):
                    count = analytics.refresh_missing_skills_aggregation()
                    st.success(f"Updated {count} skills in aggregation cache")
                    st.rerun()
        
        # Get user's current skills for filtering
        user_skill_names = {skill.name.lower() for skill in user_skills.skills}
        
        # Tabs for different views
        tab1, tab2 = st.tabs(["By Priority", "By Frequency"])
        
        with tab1:
            st.write("**Top Skills by Priority Score**")
            
            # Explanation of priority score vs frequency
            with st.expander("Understanding Priority Score vs Frequency", expanded=False):
                st.markdown("""
                **Priority Score** (weighted impact):
                - Calculated as: `(required_count × 3.0) + (preferred_count × 1.5) + (general_count × 1.0)`
                - Prioritizes skills that are **required** by employers (weighted 3x)
                - Shows which skills will have the **biggest impact** on your fit scores
                - Use this to focus on skills that will improve your match rate the most
                
                **Frequency** (raw count):
                - Simple count of how often a skill appears across all jobs
                - Shows the **most common** missing skills
                - Useful for understanding market trends
                - Doesn't account for whether skills are required or preferred
                """)
            
            st.caption("Priority score = (required_count × 3.0) + (preferred_count × 1.5) + (general_count × 1.0)")
            
            # Get skills by category and filter out user's existing skills
            skills_by_category = analytics.get_missing_skills_by_category(limit=100)
            
            if skills_by_category:
                # Filter out skills that user already has
                filtered_skills_by_category = {}
                for category, skills_list in skills_by_category.items():
                    filtered_skills = [
                        skill for skill in skills_list 
                        if skill.get('skill_name', '').lower() not in user_skill_names
                    ]
                    if filtered_skills:
                        filtered_skills_by_category[category] = filtered_skills
                
                if filtered_skills_by_category:
                    # Display skills grouped by category
                    for category, skills_list in sorted(filtered_skills_by_category.items(), key=lambda x: len(x[1]), reverse=True):
                        if category == "Other" and len(filtered_skills_by_category) > 1:
                            # Only show "Other" if there are other categories too
                            with st.expander(f"{category} ({len(skills_list)} skills)", expanded=False):
                                _display_missing_skills_table(skills_list, sort_by='priority_score', user_skill_names=user_skill_names)
                        else:
                            # Use expandable sections for categories
                            with st.expander(f"{category} ({len(skills_list)} skills)", expanded=True):
                                _display_missing_skills_table(skills_list, sort_by='priority_score', user_skill_names=user_skill_names)
                    
                    # Also show overall top skills chart
                    priority_skills = analytics.get_missing_skills_ranked(limit=20, by='priority')
                    filtered_priority = [s for s in priority_skills if s.get('skill_name', '').lower() not in user_skill_names]
                    if filtered_priority:
                        df_priority = pd.DataFrame(filtered_priority)
                        df_priority['skill_name'] = df_priority['skill_name'].str.title()
                        
                        st.write("**Top 20 Missing Skills by Priority Score**")
                        st.bar_chart(
                            df_priority.set_index('skill_name')['priority_score'],
                            height=400
                        )
                else:
                    st.success("Great! You have all the top priority skills covered!")
            else:
                st.info("No missing skills data. Skills are aggregated from job matches. Try refreshing skills data.")
        
        with tab2:
            st.write("**Top Skills by Frequency**")
            
            # Explanation of frequency vs priority score
            with st.expander("Understanding Frequency vs Priority Score", expanded=False):
                st.markdown("""
                **Frequency** (raw count):
                - Simple count of how often a skill appears across all jobs
                - Shows the **most common** missing skills
                - Useful for understanding market trends
                - Doesn't account for whether skills are required or preferred
                
                **Priority Score** (weighted impact):
                - Calculated as: `(required_count × 3.0) + (preferred_count × 1.5) + (general_count × 1.0)`
                - Prioritizes skills that are **required** by employers (weighted 3x)
                - Shows which skills will have the **biggest impact** on your fit scores
                - Use this to focus on skills that will improve your match rate the most
                """)
            
            st.caption("Skills that appear most often across all job postings")
            
            # Get skills by category and filter out user's existing skills
            skills_by_category = analytics.get_missing_skills_by_category(limit=100)
            
            if skills_by_category:
                # Filter out skills that user already has
                filtered_skills_by_category = {}
                for category, skills_list in skills_by_category.items():
                    filtered_skills = [
                        skill for skill in skills_list 
                        if skill.get('skill_name', '').lower() not in user_skill_names
                    ]
                    if filtered_skills:
                        filtered_skills_by_category[category] = filtered_skills
                
                if filtered_skills_by_category:
                    # Display skills grouped by category
                    for category, skills_list in sorted(filtered_skills_by_category.items(), key=lambda x: len(x[1]), reverse=True):
                        if category == "Other" and len(filtered_skills_by_category) > 1:
                            # Only show "Other" if there are other categories too
                            with st.expander(f"{category} ({len(skills_list)} skills)", expanded=False):
                                _display_missing_skills_table(skills_list, sort_by='frequency_count', user_skill_names=user_skill_names)
                        else:
                            # Use expandable sections for categories
                            with st.expander(f"{category} ({len(skills_list)} skills)", expanded=True):
                                _display_missing_skills_table(skills_list, sort_by='frequency_count', user_skill_names=user_skill_names)
                    
                    # Also show overall top skills chart
                    frequency_skills = analytics.get_missing_skills_ranked(limit=20, by='frequency')
                    filtered_frequency = [s for s in frequency_skills if s.get('skill_name', '').lower() not in user_skill_names]
                    if filtered_frequency:
                        df_frequency = pd.DataFrame(filtered_frequency)
                        df_frequency['skill_name'] = df_frequency['skill_name'].str.title()
                        
                        st.write("**Top 20 Missing Skills by Frequency**")
                        st.bar_chart(
                            df_frequency.set_index('skill_name')['frequency_count'],
                            height=400
                        )
                else:
                    st.success("Great! You have all the top frequency skills covered!")
            else:
                st.info("No missing skills data. Skills are aggregated from job matches. Try refreshing skills data.")


def _display_missing_skills_table(skills_list: List[Dict], sort_by: str = 'priority_score', user_skill_names: set = None):
    """Display a table of missing skills with evidence and add-to-skills button.
    
    Args:
        skills_list: List of skill dictionaries
        sort_by: Column to sort by ('priority_score' or 'frequency_count')
        user_skill_names: Set of user's existing skill names (lowercase) for filtering
    """
    if not skills_list:
        st.write("No skills in this category")
        return
    
    # Sort skills
    reverse = True  # Descending order
    sorted_skills = sorted(skills_list, key=lambda x: x.get(sort_by, 0), reverse=reverse)
    
    # Display each skill with evidence and add button
    for idx, skill in enumerate(sorted_skills):
        skill_name = skill.get('skill_name', '').title()
        skill_name_lower = skill.get('skill_name', '').lower()
        priority_score = skill.get('priority_score', 0)
        frequency_count = skill.get('frequency_count', 0)
        resume_coverage = skill.get('resume_coverage', 'none')
        is_generic = skill.get('is_generic', False)
        job_evidence_json = skill.get('job_evidence_json')
        
        # Skip if user already has this skill
        if user_skill_names and skill_name_lower in user_skill_names:
            continue
        
        # Create expandable for each skill with evidence
        coverage_text = {
            'covered': '[Covered]',
            'partial': '[Partial]',
            'none': ''
        }.get(resume_coverage or 'none', '[Unknown]')
        
        generic_badge = " [Generic]" if is_generic else ""
        
        with st.expander(f"{coverage_text} {skill_name}{generic_badge} | Priority: {priority_score:.2f} | Frequency: {frequency_count}", expanded=False):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**Priority Score:** {priority_score:.2f}")
                st.write(f"**Frequency:** {frequency_count}")
                st.write(f"**Required:** {skill.get('required_count', 0)}")
                st.write(f"**Preferred:** {skill.get('preferred_count', 0)}")
                st.write(f"**General:** {skill.get('general_count', 0)}")
            with col2:
                resume_coverage_display = resume_coverage.title() if resume_coverage else "Unknown"
                st.write(f"**Resume Coverage:** {resume_coverage_display}")
                if is_generic:
                    st.write("**Type:** Generic/Vague Skill")
                else:
                    st.write("**Type:** Specific Skill")
                
                # Add to skills button - use index to ensure uniqueness
                add_key = f"add_missing_skill_{idx}_{skill_name_lower}"
                if st.button("Add to My Skills", key=add_key, type="primary"):
                    # Add skill to user skills
                    skills_file = Path("data/user_skills.json")
                    user_skills = UserSkills(skills=[])
                    if skills_file.exists():
                        try:
                            with open(skills_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                user_skills = UserSkills.model_validate(data)
                        except Exception:
                            pass
                    
                    # Check if already exists
                    existing = next((s for s in user_skills.skills if s.name.lower() == skill_name_lower), None)
                    if not existing:
                        # Determine category from skill categorization
                        from src.analytics.skills_aggregator import _categorize_skill
                        category = _categorize_skill(skill_name)
                        # Map to user skill categories
                        category_map = {
                            "Programming Languages": "Languages",
                            "Data & Machine Learning": "ML/AI",
                            "Frameworks & Libraries": "Mobile/Web",
                            "Databases & Storage": "Backend/DB",
                            "DevOps & Infrastructure": "DevOps",
                        }
                        user_category = category_map.get(category, "Other")
                        
                        new_skill = UserSkill(
                            name=skill_name,
                            category=user_category,
                            proficiency_level="beginner",  # Default to beginner for new skills
                            projects=[]
                        )
                        user_skills.skills.append(new_skill)
                        
                        # Save to file
                        with open(skills_file, 'w', encoding='utf-8') as f:
                            json.dump(user_skills.model_dump(), f, indent=2, default=str)
                        
                        # Refresh missing skills aggregation if database is available
                        if db:
                            try:
                                analytics = AnalyticsService(db)
                                analytics.refresh_missing_skills_aggregation()
                            except Exception:
                                pass  # Silently fail if refresh doesn't work
                        
                        st.success(f"Added '{skill_name}' to your skills!")
                        st.rerun()
                    else:
                        st.info(f"'{skill_name}' is already in your skills list")
            
            # Display job evidence if available
            if job_evidence_json:
                try:
                    import json
                    evidence = json.loads(job_evidence_json)
                    if evidence:
                        st.write("**Job Evidence:**")
                        for i, ev in enumerate(evidence[:5], 1):  # Show first 5
                            with st.expander(f"Evidence {i} (Job #{ev.get('job_id', '?')})", expanded=False):
                                st.write(ev.get('snippet', ''))
                                st.caption(f"Match type: {ev.get('match_type', 'unknown')}")
                        if len(evidence) > 5:
                            st.caption(f"... and {len(evidence) - 5} more evidence snippets")
                except (json.JSONDecodeError, KeyError):
                    pass
            else:
                st.caption("No job evidence found for this skill")
            
            # Display decomposition if available
            decomposition_json = skill.get('decomposition_json')
            if decomposition_json:
                try:
                    import json
                    decomposition = json.loads(decomposition_json)
                    if decomposition and decomposition.get('children'):
                        st.divider()
                        st.write("**Decomposed Sub-Skills:**")
                        st.caption(f"Based on job evidence - {len(decomposition['children'])} specific skills identified")
                        for child in decomposition['children']:
                            child_skill = child.get('skill', '')
                            child_coverage = child.get('resume_coverage', 'none')
                            child_freq = child.get('job_frequency', 0)
                            
                            coverage_text = {
                                'covered': '[Covered]',
                                'partial': '[Partial]',
                                'none': ''
                            }.get(child_coverage, '[Unknown]')
                            
                            st.write(f"{coverage_text} **{child_skill}** - Frequency: {child_freq} jobs, Resume: {child_coverage}")
                except (json.JSONDecodeError, KeyError):
                    pass

