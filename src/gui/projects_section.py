"""Projects management section for GUI."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import json
from src.projects.project_library import ProjectLibrary
from src.models.resume import ProjectItem, Bullet
from src.extractors.github_repo_extractor import GitHubRepoExtractor
from datetime import datetime
import requests


def render_projects_section():
    """Render projects management section."""
    st.header("Projects")
    
    library = ProjectLibrary()
    projects = library.get_all_projects()
    
    # Initialize bullet list in session state
    if 'project_bullets' not in st.session_state:
        st.session_state.project_bullets = [""]
    
    # Add new project form
    with st.expander("Add New Project", expanded=False):
        # Add method selection (Manual or GitHub)
        if 'add_method' not in st.session_state:
            st.session_state.add_method = "Manual"
        
        method = st.radio(
            "Add method:",
            ["Manual Entry", "Add through GitHub"],
            key="add_method_radio",
            index=0 if st.session_state.add_method == "Manual" else 1,
            horizontal=True
        )
        st.session_state.add_method = "Manual" if method == "Manual Entry" else "GitHub"
        
        # GitHub import section
        if st.session_state.add_method == "GitHub":
            github_url = st.text_input(
                "GitHub Repository URL",
                key="github_url_input",
                placeholder="https://github.com/owner/repo",
                help="Enter the full URL of the GitHub repository"
            )
            
            if st.button("Import from GitHub", key="import_github_btn", type="primary"):
                if not github_url:
                    st.error("Please enter a GitHub repository URL")
                else:
                    try:
                        with st.spinner("Extracting project information from GitHub..."):
                            extractor = GitHubRepoExtractor()
                            extracted_project = extractor.extract_project(github_url)
                            
                            # Store extracted project in session state for preview/edit
                            st.session_state.github_extracted_project = extracted_project
                            st.session_state.show_github_preview = True
                            st.success("Project information extracted successfully!")
                            st.rerun()
                    except ValueError as e:
                        st.error(f"Invalid GitHub URL: {str(e)}")
                    except requests.HTTPError as e:
                        if e.response.status_code == 404:
                            st.error("Repository not found. Please check the URL.")
                        elif e.response.status_code == 403:
                            st.error("Access denied. The repository may be private. Make sure GITHUB_TOKEN is set in your environment.")
                        else:
                            st.error(f"GitHub API error: {str(e)}")
                    except Exception as e:
                        st.error(f"Error extracting project: {str(e)}")
            
            # Show preview/edit form for extracted project
            if st.session_state.get("show_github_preview") and st.session_state.get("github_extracted_project"):
                st.divider()
                st.subheader("Review and Edit Extracted Information")
                
                extracted = st.session_state.github_extracted_project
                
                with st.form("github_project_preview_form"):
                    preview_name = st.text_input("Project Name", value=extracted.name, key="preview_name")
                    preview_tech_stack = st.text_input(
                        "Tech Stack (comma-separated)",
                        value=", ".join(extracted.tech_stack) if extracted.tech_stack else "",
                        key="preview_tech_stack"
                    )
                    preview_start_date = st.text_input(
                        "Start Date",
                        value=extracted.start_date or "",
                        key="preview_start_date",
                        help="Format: Jan 2024"
                    )
                    preview_end_date = st.text_input(
                        "End Date (or 'Present')",
                        value=extracted.end_date or "",
                        key="preview_end_date"
                    )
                    
                    st.write("**Bullets:**")
                    # Initialize preview bullets in session state if needed
                    if 'preview_bullets_list' not in st.session_state:
                        st.session_state.preview_bullets_list = [bullet.text for bullet in extracted.bullets]
                    
                    preview_bullets = []
                    for i in range(len(st.session_state.preview_bullets_list)):
                        current_value = st.session_state.preview_bullets_list[i] if i < len(st.session_state.preview_bullets_list) else ""
                        bullet_text = st.text_area(
                            f"Bullet {i+1}",
                            value=current_value,
                            key=f"preview_bullet_{i}",
                            height=80
                        )
                        # Update session state
                        if i < len(st.session_state.preview_bullets_list):
                            st.session_state.preview_bullets_list[i] = bullet_text
                        else:
                            st.session_state.preview_bullets_list.append(bullet_text)
                        
                        if bullet_text and bullet_text.strip():
                            preview_bullets.append(bullet_text.strip())
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Save Project", type="primary"):
                            if not preview_name:
                                st.error("Project name is required")
                            elif not preview_bullets:
                                st.error("At least one bullet is required")
                            else:
                                # Parse tech stack
                                tech_list = [t.strip() for t in preview_tech_stack.split(',') if t.strip()] if preview_tech_stack else []
                                
                                # Create project
                                project = ProjectItem(
                                    name=preview_name,
                                    tech_stack=tech_list,
                                    start_date=preview_start_date if preview_start_date else None,
                                    end_date=preview_end_date if preview_end_date else None,
                                    bullets=[Bullet(text=b, skills=[], evidence=None) for b in preview_bullets]
                                )
                                
                                library.add_project(project)
                                
                                # Clear session state
                                if 'github_extracted_project' in st.session_state:
                                    del st.session_state.github_extracted_project
                                if 'show_github_preview' in st.session_state:
                                    del st.session_state.show_github_preview
                                if 'preview_bullets_list' in st.session_state:
                                    del st.session_state.preview_bullets_list
                                
                                st.success(f"Project '{preview_name}' added successfully!")
                                st.rerun()
                    
                    with col2:
                        if st.form_submit_button("Cancel", type="secondary"):
                            if 'github_extracted_project' in st.session_state:
                                del st.session_state.github_extracted_project
                            if 'show_github_preview' in st.session_state:
                                del st.session_state.show_github_preview
                            if 'preview_bullets_list' in st.session_state:
                                del st.session_state.preview_bullets_list
                            st.rerun()
                
                # Add bullet button (outside form)
                if st.button("+ Add Bullet", key="preview_add_bullet"):
                    if 'preview_bullets_list' not in st.session_state:
                        st.session_state.preview_bullets_list = [bullet.text for bullet in extracted.bullets]
                    st.session_state.preview_bullets_list.append("")
                    st.rerun()
            
            st.divider()
        
        # Manual entry form
        if st.session_state.add_method == "Manual":
            # Handle remove bullet buttons (check session state for removals)
            bullets_to_remove = []
            for i in range(len(st.session_state.project_bullets)):
                if f"remove_bullet_{i}" in st.session_state and st.session_state[f"remove_bullet_{i}"]:
                    if len(st.session_state.project_bullets) > 1:
                        bullets_to_remove.append(i)
            
            # Remove bullets (in reverse order to maintain indices)
            for idx in sorted(bullets_to_remove, reverse=True):
                st.session_state.project_bullets.pop(idx)
                # Also remove the corresponding session state keys
                if f"project_bullet_{idx}" in st.session_state:
                    del st.session_state[f"project_bullet_{idx}"]
                if f"remove_bullet_{idx}" in st.session_state:
                    del st.session_state[f"remove_bullet_{idx}"]
                st.rerun()
            
            with st.form("add_project_form"):
            name = st.text_input("Project Name", key="project_name")
            tech_stack = st.text_input("Tech Stack (comma-separated)", key="project_tech_stack", 
                                       help="e.g., Python, TensorFlow, scikit-learn")
            start_date = st.text_input("Start Date (YYYY-MM)", key="project_start_date", 
                                      help="e.g., 2025-01")
            end_date = st.text_input("End Date (YYYY-MM or 'Present')", key="project_end_date",
                                    help="e.g., 2025-12 or Present")
            
            st.write("**Bullets:**")
            
            # Display bullets (inside form, but remove handled via checkboxes)
            for i in range(len(st.session_state.project_bullets)):
                col1, col2 = st.columns([10, 1])
                with col1:
                    # Get current value from session state
                    current_value = st.session_state.project_bullets[i] if i < len(st.session_state.project_bullets) else ""
                    updated_value = st.text_area(
                        f"Bullet {i+1}",
                        value=current_value,
                        key=f"project_bullet_{i}",
                        height=80,
                        label_visibility="visible"
                    )
                    # Update stored value
                    if i < len(st.session_state.project_bullets):
                        st.session_state.project_bullets[i] = updated_value
                with col2:
                    if len(st.session_state.project_bullets) > 1:
                        # Use checkbox to mark for removal (can't use button in form)
                        if st.checkbox("×", key=f"remove_check_{i}", help="Remove this bullet", label_visibility="collapsed"):
                            st.session_state[f"remove_bullet_{i}"] = True
                            st.rerun()
            
            # Add bullet button (beneath bullet entries, inside form but using form_submit_button won't work)
            # Use a workaround: add button outside form but check if form context
            submitted = st.form_submit_button("Add Project", type="primary")
            
            # Handle form submission
            if submitted:
                name = st.session_state.get("project_name", "")
                tech_stack = st.session_state.get("project_tech_stack", "")
                start_date = st.session_state.get("project_start_date", "")
                end_date = st.session_state.get("project_end_date", "")
                
                if not name:
                    st.error("Project name is required")
                else:
                    # Parse tech stack
                    tech_list = [t.strip() for t in tech_stack.split(',') if t.strip()] if tech_stack else []
                    
                    # Parse dates - convert to string format expected by ProjectItem
                    start_str = None
                    end_str = None
                    if start_date:
                        try:
                            start_dt = datetime.strptime(start_date, "%Y-%m")
                            # Format as "Sep 2025" (month abbreviation + year)
                            start_str = start_dt.strftime("%b %Y")
                        except ValueError:
                            st.error(f"Invalid start date format. Use YYYY-MM")
                            return
                    
                    if end_date and end_date.lower() != 'present':
                        try:
                            end_dt = datetime.strptime(end_date, "%Y-%m")
                            # Format as "Dec 2025" (month abbreviation + year)
                            end_str = end_dt.strftime("%b %Y")
                        except ValueError:
                            st.error(f"Invalid end date format. Use YYYY-MM or 'Present'")
                            return
                    elif end_date and end_date.lower() == 'present':
                        end_str = "Present"
                    
                    # Collect bullets from session state keys (form values are stored there)
                    bullets = []
                    for i in range(len(st.session_state.project_bullets)):
                        # Get value from session state key (set by text_area widget)
                        bullet_text = st.session_state.get(f"project_bullet_{i}", "")
                        if bullet_text and bullet_text.strip():
                            bullets.append(Bullet(text=bullet_text.strip(), skills=[], evidence=None))
                    
                    if not bullets:
                        st.error("At least one bullet is required")
                        return
                    
                    # Create project
                    project = ProjectItem(
                        name=name,
                        tech_stack=tech_list,
                        start_date=start_str,
                        end_date=end_str,
                        bullets=bullets
                    )
                    
                    # Clear bullets from session state after successful submission
                    if 'project_bullets' in st.session_state:
                        del st.session_state.project_bullets
                        # Reset to one empty bullet for next project
                        st.session_state.project_bullets = [""]
                    
                    library.add_project(project)
                    st.success(f"Project '{name}' added successfully!")
                    st.rerun()
        
        # Add bullet button (outside form, beneath entries)
        if st.session_state.add_method == "Manual":
            st.write("")  # Spacer
            if st.button("+ Add Bullet", key="add_bullet_btn"):
                st.session_state.project_bullets.append("")
                st.rerun()
    
    # List existing projects with edit capability
    if projects:
        st.subheader(f"Your Projects ({len(projects)})")
        
        for i, project in enumerate(projects):
            with st.expander(f"{project.name}", expanded=False):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Tech Stack:** {', '.join(project.tech_stack) if project.tech_stack else 'None'}")
                    if project.start_date:
                        end_str = "Present" if not project.end_date else project.end_date
                        st.write(f"**Dates:** {project.start_date} - {end_str}")
                    
                    st.write("**Bullets:**")
                    for j, bullet in enumerate(project.bullets, 1):
                        st.write(f"{j}. {bullet.text}")
                    
                    # Inline edit form
                    with st.expander("Edit", expanded=False):
                        new_name = st.text_input(
                            "Project Name",
                            value=project.name,
                            key=f"edit_proj_name_{i}",
                        )
                        new_tech_stack = st.text_input(
                            "Tech Stack (comma-separated)",
                            value=", ".join(project.tech_stack) if project.tech_stack else "",
                            key=f"edit_proj_tech_{i}",
                            help="e.g., Python, TensorFlow, scikit-learn"
                        )
                        new_start = st.text_input(
                            "Start Date (as shown)",
                            value=project.start_date or "",
                            key=f"edit_proj_start_{i}",
                        )
                        new_end = st.text_input(
                            "End Date (as shown or 'Present')",
                            value=project.end_date or "",
                            key=f"edit_proj_end_{i}",
                        )
                        edited_bullets = []
                        for j, bullet in enumerate(project.bullets, 1):
                            txt = st.text_area(
                                f"Bullet {j}",
                                value=bullet.text,
                                key=f"edit_proj_bullet_{i}_{j}",
                                height=80,
                            )
                            if txt and txt.strip():
                                edited_bullets.append(
                                    Bullet(
                                        text=txt.strip(),
                                        skills=bullet.skills,
                                        evidence=bullet.evidence,
                                        history=bullet.history,
                                    )
                                )
                        if st.button("Save Changes", key=f"save_proj_{i}", type="primary"):
                            if not new_name:
                                st.error("Project name is required")
                            elif not edited_bullets:
                                st.error("At least one bullet is required")
                            else:
                                # Parse tech stack
                                tech_list = [t.strip() for t in new_tech_stack.split(',') if t.strip()] if new_tech_stack else []
                                
                                all_projects = library.get_all_projects()
                                if i < len(all_projects):
                                    all_projects[i] = ProjectItem(
                                        name=new_name,
                                        tech_stack=tech_list,
                                        start_date=new_start if new_start else None,
                                        end_date=new_end if new_end else None,
                                        bullets=edited_bullets,
                                    )
                                    library._save_projects(all_projects)
                                st.success("Project updated")
                                st.rerun()
                
                with col2:
                    if st.button("Delete", key=f"delete_project_{i}", type="secondary"):
                        # Remove from library
                        all_projects = library.get_all_projects()
                        if i < len(all_projects):
                            all_projects.pop(i)
                            library._save_projects(all_projects)
                        st.success(f"Project deleted")
                        st.rerun()
    else:
        st.info("No projects yet. Add your first project above!")
