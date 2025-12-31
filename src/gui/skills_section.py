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
from src.models.skills import UserSkills, UserSkill, SkillEvidence
from src.projects.project_library import ProjectLibrary
from src.db.database import Database
from src.analytics.analytics_service import AnalyticsService
from src.utils.skill_ai_assistant import SkillAIAssistant


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
            
            # Project selection (multi-select)
            selected_projects = st.multiselect("Associated Projects",
                                               project_names,
                                               key="skill_projects",
                                               help="Select projects that demonstrate this skill")
            # Optional evidence source (experience / project / coursework / certification)
            evidence_type = st.selectbox(
                "Primary Evidence Type (optional)",
                ["", "experience", "project", "coursework", "certification"],
                key="skill_evidence_type",
            )
            evidence_name = st.text_input(
                "Evidence Name (e.g., AMD Datacenter Co-op, Hitchly, Course title)",
                key="skill_evidence_name",
            )
            evidence_text = st.text_area(
                "Evidence Snippet (optional)",
                key="skill_evidence_text",
                help="Optional short description showing where you used this skill.",
            )
            
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
                        existing_skill.projects = selected_projects
                        # Append evidence source if provided
                        if evidence_type and evidence_name:
                            existing_skill.evidence_sources.append(
                                SkillEvidence(
                                    source_type=evidence_type,
                                    source_name=evidence_name,
                                    evidence_text=evidence_text or None,
                                )
                            )
                        st.success(f"Skill '{skill_name}' updated!")
                    else:
                        # Build evidence list if provided
                        evidence_sources = []
                        if evidence_type and evidence_name:
                            evidence_sources.append(
                                SkillEvidence(
                                    source_type=evidence_type,
                                    source_name=evidence_name,
                                    evidence_text=evidence_text or None,
                                )
                            )
                        # Add new skill
                        new_skill = UserSkill(
                            name=skill_name,
                            category=category,
                            projects=selected_projects,
                            evidence_sources=evidence_sources,
                        )
                        user_skills.skills.append(new_skill)
                        st.success(f"Skill '{skill_name}' added!")
                    
                    # Save to file
                    with open(skills_file, 'w', encoding='utf-8') as f:
                        json.dump(user_skills.model_dump(), f, indent=2, default=str)
                    
                    # Mark that refresh is needed (defer actual refresh until user clicks Refresh button)
                    # This avoids lag when adding skills
                    if db:
                        st.session_state['missing_skills_refresh_needed'] = True
                    
                    st.rerun()
    
    # Display existing skills by category, with edit capabilities
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
                for idx, skill in enumerate(skills_list):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{skill.name}**")
                        meta_bits = []
                        if skill.projects:
                            meta_bits.append(f"Projects: {', '.join(skill.projects)}")
                        if skill.evidence_sources:
                            meta_bits.append(
                                f"Evidence: {', '.join({e.source_name for e in skill.evidence_sources})}"
                            )
                        if meta_bits:
                            st.caption(" | ".join(meta_bits))
                    with col2:
                        # Edit inline
                        with st.expander("Edit", expanded=False):
                            new_name = st.text_input(
                                "Name",
                                value=skill.name,
                                key=f"edit_skill_name_{category}_{idx}",
                            )
                            new_category = st.selectbox(
                                "Category",
                                ["Languages", "ML/AI", "Mobile/Web", "Backend/DB", "DevOps", "Other"],
                                index=["Languages", "ML/AI", "Mobile/Web", "Backend/DB", "DevOps", "Other"].index(
                                    skill.category if skill.category in ["Languages", "ML/AI", "Mobile/Web", "Backend/DB", "DevOps", "Other"] else "Other"
                                ),
                                key=f"edit_skill_cat_{category}_{idx}",
                            )
                            new_projects = st.multiselect(
                                "Projects",
                                project_names,
                                default=skill.projects,
                                key=f"edit_skill_projects_{category}_{idx}",
                            )
                            # Simple evidence editor: one primary evidence entry
                            ev_name = st.text_input(
                                "Primary Evidence Name",
                                value=skill.evidence_sources[0].source_name
                                if skill.evidence_sources
                                else "",
                                key=f"edit_skill_ev_name_{category}_{idx}",
                            )
                            ev_type = st.selectbox(
                                "Evidence Type",
                                ["", "experience", "project", "coursework", "certification"],
                                index=(
                                    ["", "experience", "project", "coursework", "certification"].index(
                                        skill.evidence_sources[0].source_type
                                    )
                                    if skill.evidence_sources
                                    else 0
                                ),
                                key=f"edit_skill_ev_type_{category}_{idx}",
                            )
                            ev_text = st.text_area(
                                "Evidence Snippet",
                                value=skill.evidence_sources[0].evidence_text
                                if skill.evidence_sources and skill.evidence_sources[0].evidence_text
                                else "",
                                key=f"edit_skill_ev_text_{category}_{idx}",
                            )
                            if st.button("Save Changes", key=f"save_skill_{category}_{idx}", type="primary"):
                                skill.name = new_name
                                skill.category = new_category
                                skill.projects = new_projects
                                if ev_type and ev_name:
                                    skill.evidence_sources = [
                                        SkillEvidence(
                                            source_type=ev_type,
                                            source_name=ev_name,
                                            evidence_text=ev_text or None,
                                        )
                                    ]
                                # Persist changes
                                with open(skills_file, 'w', encoding='utf-8') as f:
                                    json.dump(user_skills.model_dump(), f, indent=2, default=str)
                                st.success(f"Skill '{skill.name}' updated")
                                st.rerun()
                    with col3:
                        if st.button("Delete", key=f"delete_skill_{skill.name}", type="secondary"):
                            user_skills.skills = [s for s in user_skills.skills if s.name != skill.name]
                            with open(skills_file, 'w', encoding='utf-8') as f:
                                json.dump(user_skills.model_dump(), f, indent=2, default=str)
                            st.success(f"Skill '{skill.name}' deleted")
                            st.rerun()
    else:
        st.info("No skills yet. Add your first skill above!")
    
    # AI-assisted skill suggestions
    st.divider()
    with st.expander("AI Skill Suggestions (beta)", expanded=False):
        st.caption("Paste a job description or project description to get suggested skills. Suggestions are never auto-added; you choose what to keep.")
        suggestion_text = st.text_area(
            "Text for analysis",
            key="ai_skill_suggestion_text",
            height=160,
        )
        if st.button("Suggest Skills", key="ai_skill_suggest_btn", type="secondary"):
            assistant = SkillAIAssistant()
            suggestions = assistant.suggest_skills(
                suggestion_text,
                existing_skills=[s.name for s in user_skills.skills],
            )
            if not suggestions:
                st.info("No new skills suggested (or OpenAI API key not configured).")
            else:
                st.write("**Suggested Skills (click to add):**")
                for idx, s in enumerate(suggestions):
                    col_s1, col_s2 = st.columns([3, 1])
                    with col_s1:
                        st.write(f"- {s['name']} ({s['category']})")
                    with col_s2:
                        if st.button("Add", key=f"ai_add_skill_{idx}", type="primary"):
                            new_skill = UserSkill(
                                name=s["name"],
                                category=s["category"],
                                projects=[],
                                evidence_sources=[],
                            )
                            user_skills.skills.append(new_skill)
                            with open(skills_file, 'w', encoding='utf-8') as f:
                                json.dump(user_skills.model_dump(), f, indent=2, default=str)
                            st.success(f"Skill '{s['name']}' added from AI suggestion")
                            st.rerun()

    # Missing Skills Analysis Section
    if db:
        st.divider()
        st.subheader("Missing Skills Analysis")
        st.caption("Skills that appear in job postings but are not yet in your skills list")
        
        # Initialize analytics service
        analytics = AnalyticsService(db)
        
        # Refresh button - also show indicator if refresh is needed
        col_refresh, col_spacer = st.columns([1, 10])
        with col_refresh:
            refresh_needed = st.session_state.get('missing_skills_refresh_needed', False)
            refresh_label = "Refresh" + (" ⚠️" if refresh_needed else "")
            if st.button(refresh_label, help="Update missing skills aggregation", key="refresh_missing_skills", width='stretch'):
                with st.spinner("Refreshing skills aggregation..."):
                    count = analytics.refresh_missing_skills_aggregation()
                    st.success(f"Updated {count} skills in aggregation cache")
                    st.session_state['missing_skills_refresh_needed'] = False
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
                                _display_missing_skills_table(skills_list, sort_by='priority_score', user_skill_names=user_skill_names, category=category)
                        else:
                            # Use expandable sections for categories
                            with st.expander(f"{category} ({len(skills_list)} skills)", expanded=True):
                                _display_missing_skills_table(skills_list, sort_by='priority_score', user_skill_names=user_skill_names, category=category)
                    
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
                                _display_missing_skills_table(skills_list, sort_by='frequency_count', user_skill_names=user_skill_names, category=category)
                        else:
                            # Use expandable sections for categories
                            with st.expander(f"{category} ({len(skills_list)} skills)", expanded=True):
                                _display_missing_skills_table(skills_list, sort_by='frequency_count', user_skill_names=user_skill_names, category=category)
                    
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


def _display_missing_skills_table(skills_list: List[Dict], sort_by: str = 'priority_score', user_skill_names: set = None, category: str = ''):
    """Display a table of missing skills with evidence and add-to-skills button.
    
    Args:
        skills_list: List of skill dictionaries
        sort_by: Column to sort by ('priority_score' or 'frequency_count')
        user_skill_names: Set of user's existing skill names (lowercase) for filtering
        category: Category name for unique key generation
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
                
                # Add to skills button - include category and sort_by to ensure uniqueness across different calls
                category_safe = category.lower().replace(' ', '_').replace('&', 'and') if category else 'uncategorized'
                add_key = f"add_missing_skill_{category_safe}_{sort_by}_{idx}_{skill_name_lower}"
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
                            projects=[]
                        )
                        user_skills.skills.append(new_skill)
                        
                        # Save to file
                        with open(skills_file, 'w', encoding='utf-8') as f:
                            json.dump(user_skills.model_dump(), f, indent=2, default=str)
                        
                        # Mark that refresh is needed (defer actual refresh to avoid lag)
                        if db:
                            st.session_state['missing_skills_refresh_needed'] = True
                        
                        # Invalidate match details cache so they refresh when user returns to job details
                        if 'job_match_cache' in st.session_state:
                            del st.session_state['job_match_cache']
                        
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

