"""Resumes page component showing all resumes organized by job."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import json
from pathlib import Path
from src.db.database import Database
from src.storage.resume_manager import ResumeManager
from src.gui.resume_preview import render_resume_preview
from src.models.resume import Resume
from datetime import datetime


def render_resumes_page(db: Database):
    """Render the resumes page showing all resumes organized by job."""
    st.header("Resumes")
    
    # Template upload section
    template_path = Path("templates/resume.tex")
    resume_json_path = Path("data/resume.json")
    
    # Check if template already exists
    if template_path.exists():
        st.subheader("Current Resume Template")
        st.info(f"Template found at: `{template_path}`")
        
        # Show template info
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"**Last modified:** {datetime.fromtimestamp(template_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        with col2:
            view_template = st.button("View Template", key="view_template_resumes")
        with col3:
            preview_resume = st.button("Preview Resume", key="preview_template_resume")
        
        # Initialize session state if not exists
        if 'view_template_resumes_state' not in st.session_state:
            st.session_state['view_template_resumes_state'] = False
        if 'preview_template_resume_state' not in st.session_state:
            st.session_state['preview_template_resume_state'] = False
        
        # Toggle state on button click - ensure only one is active at a time
        if view_template:
            st.session_state['view_template_resumes_state'] = not st.session_state.get('view_template_resumes_state', False)
            # Close preview when opening template view
            if st.session_state['view_template_resumes_state']:
                st.session_state['preview_template_resume_state'] = False
            st.rerun()
        
        if preview_resume:
            st.session_state['preview_template_resume_state'] = not st.session_state.get('preview_template_resume_state', False)
            # Close template view when opening preview
            if st.session_state['preview_template_resume_state']:
                st.session_state['view_template_resumes_state'] = False
            st.rerun()
        
        if st.session_state.get('view_template_resumes_state', False):
            with st.expander("Template Source", expanded=True):
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
                st.code(template_content, language='latex')
                if st.button("Close", key="close_template_view"):
                    st.session_state['view_template_resumes_state'] = False
                    st.rerun()
        
        # Preview resume from template
        if st.session_state.get('preview_template_resume_state', False):
            try:
                # Try to load from resume.json first (faster)
                resume_obj = None
                if resume_json_path.exists():
                    try:
                        with open(resume_json_path, 'r', encoding='utf-8') as f:
                            resume_data = json.load(f)
                        resume_obj = Resume.model_validate(resume_data)
                        st.info("Using resume from data/resume.json")
                    except Exception as e:
                        st.warning(f"Could not load resume.json: {e}. Parsing template instead...")
                
                # If resume.json doesn't exist or failed, parse template
                if resume_obj is None:
                    from src.parsers.latex_resume import LaTeXResumeParser
                    parser = LaTeXResumeParser.from_file(template_path)
                    resume_obj = parser.parse()
                    st.info("Parsed resume from template")
                
                # Generate PDF preview
                import tempfile
                from src.rendering.latex_renderer import LaTeXRenderer
                
                with st.spinner("Generating PDF preview..."):
                    temp_pdf = Path(tempfile.gettempdir()) / f"resume_template_preview_{datetime.now().timestamp()}.pdf"
                    renderer = LaTeXRenderer(template_path=template_path)
                    renderer.render_pdf(resume_obj, temp_pdf)
                    
                    if temp_pdf.exists():
                        render_resume_preview(temp_pdf)
                        if st.button("Close Preview", key="close_resume_preview"):
                            st.session_state['preview_template_resume_state'] = False
                            # Clean up temp file
                            if temp_pdf.exists():
                                temp_pdf.unlink()
                            st.rerun()
                    else:
                        st.error("Failed to generate PDF preview")
            except Exception as e:
                st.error(f"Error generating preview: {e}")
                import traceback
                st.exception(e)
                if st.button("Close", key="close_error_preview"):
                    st.session_state['preview_template_resume_state'] = False
                    st.rerun()
    
    with st.expander("Upload New Resume Template", expanded=False):
        uploaded_file = st.file_uploader("Upload LaTeX Resume Template", type=['tex'], key="resumes_template_upload")
        
        if uploaded_file is not None:
            if st.button("Save Template", type="primary", key="resumes_save_template"):
                try:
                    # Read uploaded content
                    content = uploaded_file.read().decode('utf-8')
                    
                    # Save to templates directory
                    template_path.parent.mkdir(exist_ok=True, parents=True)
                    with open(template_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    st.success(f"Template saved to {template_path}")
                    
                    # Try to parse and convert to JSON
                    try:
                        from src.parsers.latex_resume import LaTeXResumeParser
                        parser = LaTeXResumeParser.from_file(template_path)
                        resume = parser.parse()
                        
                        # Append Experience, Projects, and Skills to existing libraries
                        from src.storage.experience_library import ExperienceLibrary
                        from src.projects.project_library import ProjectLibrary
                        from src.models.skills import UserSkills, UserSkill
                        
                        # Get existing counts before adding
                        exp_library = ExperienceLibrary()
                        existing_exp = exp_library.get_all_experience()
                        
                        proj_library = ProjectLibrary()
                        existing_proj = proj_library.get_all_projects()
                        
                        # Append experience
                        exp_added = 0
                        exp_updated = 0
                        for exp_item in resume.experience:
                            exists = any(
                                e.organization == exp_item.organization and e.role == exp_item.role
                                for e in existing_exp
                            )
                            exp_library.add_experience(exp_item)
                            if exists:
                                exp_updated += 1
                            else:
                                exp_added += 1
                        
                        # Append projects
                        proj_added = 0
                        proj_updated = 0
                        for proj in resume.projects:
                            exists = any(p.name == proj.name for p in existing_proj)
                            proj_library.add_project(proj)
                            if exists:
                                proj_updated += 1
                            else:
                                proj_added += 1
                        
                        # Append skills
                        skills_file = Path("data/user_skills.json")
                        user_skills = UserSkills(skills=[])
                        if skills_file.exists():
                            try:
                                with open(skills_file, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    user_skills = UserSkills.model_validate(data)
                            except:
                                pass
                        
                        skill_count = 0
                        # Add skills from resume to user skills
                        for category, skill_list in resume.skills.items():
                            for skill_name in skill_list:
                                # Check if skill already exists
                                existing = next((s for s in user_skills.skills if s.name.lower() == skill_name.lower()), None)
                                if not existing:
                                    # Create new skill entry
                                    new_skill = UserSkill(
                                        name=skill_name,
                                        category=category,
                                        proficiency_level="intermediate",  # Default
                                        projects=[]
                                    )
                                    user_skills.skills.append(new_skill)
                                    skill_count += 1
                        
                        # Save updated skills
                        with open(skills_file, 'w', encoding='utf-8') as f:
                            json.dump(user_skills.model_dump(), f, indent=2, default=str)
                        
                        # Save to resume.json
                        resume_json_path.parent.mkdir(exist_ok=True, parents=True)
                        with open(resume_json_path, 'w', encoding='utf-8') as f:
                            json.dump(resume.model_dump(), f, indent=2, default=str)
                        
                        st.success("Template parsed and saved to resume.json")
                        
                        # Show detailed summary
                        summary_parts = []
                        if exp_added > 0 or exp_updated > 0:
                            exp_msg = f"{exp_added} new, {exp_updated} updated" if exp_updated > 0 else f"{exp_added} new"
                            summary_parts.append(f"**Experience:** {exp_msg} ({len(resume.experience)} total from template)")
                        if proj_added > 0 or proj_updated > 0:
                            proj_msg = f"{proj_added} new, {proj_updated} updated" if proj_updated > 0 else f"{proj_added} new"
                            summary_parts.append(f"**Projects:** {proj_msg} ({len(resume.projects)} total from template)")
                        if skill_count > 0:
                            summary_parts.append(f"**Skills:** {skill_count} new skills added")
                        
                        if summary_parts:
                            st.info("\n".join(summary_parts))
                        else:
                            st.info("All items from template already exist in libraries.")
                        
                        st.rerun()
                    except Exception as e:
                        st.warning(f"Template saved but parsing failed: {e}")
                        import traceback
                        st.exception(e)
                        st.info("You can manually convert using: `ats convert-latex templates/resume.tex`")
                except Exception as e:
                    st.error(f"Error saving template: {e}")
                    import traceback
                    st.exception(e)
    
    # If template exists, show option to re-parse and update libraries
    if template_path.exists():
        st.write("")
        if st.button("Re-parse Template and Update Libraries", key="reparse_template"):
            try:
                from src.parsers.latex_resume import LaTeXResumeParser
                parser = LaTeXResumeParser.from_file(template_path)
                resume = parser.parse()
                
                # Append Experience, Projects, and Skills to existing libraries
                from src.storage.experience_library import ExperienceLibrary
                from src.projects.project_library import ProjectLibrary
                from src.models.skills import UserSkills, UserSkill
                
                # Get existing counts before adding
                exp_library = ExperienceLibrary()
                existing_exp = exp_library.get_all_experience()
                existing_exp_count = len(existing_exp)
                
                proj_library = ProjectLibrary()
                existing_proj = proj_library.get_all_projects()
                existing_proj_count = len(existing_proj)
                
                # Append experience
                exp_added = 0
                exp_updated = 0
                for exp_item in resume.experience:
                    # Check if it already exists
                    exists = any(
                        e.organization == exp_item.organization and e.role == exp_item.role
                        for e in existing_exp
                    )
                    exp_library.add_experience(exp_item)
                    if exists:
                        exp_updated += 1
                    else:
                        exp_added += 1
                
                # Append projects
                proj_added = 0
                proj_updated = 0
                for proj in resume.projects:
                    exists = any(p.name == proj.name for p in existing_proj)
                    proj_library.add_project(proj)
                    if exists:
                        proj_updated += 1
                    else:
                        proj_added += 1
                
                # Append skills
                skills_file = Path("data/user_skills.json")
                user_skills = UserSkills(skills=[])
                if skills_file.exists():
                    try:
                        with open(skills_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            user_skills = UserSkills.model_validate(data)
                    except:
                        pass
                
                skill_count = 0
                # Add skills from resume to user skills
                for category, skill_list in resume.skills.items():
                    for skill_name in skill_list:
                        # Check if skill already exists
                        existing = next((s for s in user_skills.skills if s.name.lower() == skill_name.lower()), None)
                        if not existing:
                            # Create new skill entry
                            new_skill = UserSkill(
                                name=skill_name,
                                category=category,
                                proficiency_level="intermediate",  # Default
                                projects=[]
                            )
                            user_skills.skills.append(new_skill)
                            skill_count += 1
                
                # Save updated skills
                with open(skills_file, 'w', encoding='utf-8') as f:
                    json.dump(user_skills.model_dump(), f, indent=2, default=str)
                
                # Update resume.json
                resume_json_path.parent.mkdir(exist_ok=True, parents=True)
                with open(resume_json_path, 'w', encoding='utf-8') as f:
                    json.dump(resume.model_dump(), f, indent=2, default=str)
                
                st.success("Template re-parsed and libraries updated!")
                
                # Show detailed summary
                summary_parts = []
                if exp_added > 0 or exp_updated > 0:
                    exp_msg = f"{exp_added} new, {exp_updated} updated" if exp_updated > 0 else f"{exp_added} new"
                    summary_parts.append(f"**Experience:** {exp_msg} ({len(resume.experience)} total from template)")
                if proj_added > 0 or proj_updated > 0:
                    proj_msg = f"{proj_added} new, {proj_updated} updated" if proj_updated > 0 else f"{proj_added} new"
                    summary_parts.append(f"**Projects:** {proj_msg} ({len(resume.projects)} total from template)")
                if skill_count > 0:
                    summary_parts.append(f"**Skills:** {skill_count} new skills added")
                
                if summary_parts:
                    st.info("\n".join(summary_parts))
                else:
                    st.info("All items from template already exist in libraries.")
                
                st.rerun()
            except Exception as e:
                st.error(f"Error re-parsing template: {e}")
                import traceback
                st.exception(e)
    
    st.divider()
    
    # Get all jobs
    all_jobs = db.get_all_jobs()
    
    if not all_jobs:
        st.info("No jobs added yet. Add a job from the Jobs page to generate resumes.")
        return
    
    # Group resumes by job
    resumes_by_job = {}
    unassigned_resumes = []
    resume_manager = ResumeManager()
    file_resumes = resume_manager.list_resumes()
    
    # Get resumes from database organized by job
    for job in all_jobs:
        job_id = job.get('id')
        job_company = job.get('company', 'Unknown')
        job_title = job.get('title', 'Unknown')
        
        # Get resumes for this job from database
        db_resumes = db.get_resumes_by_job_id(job_id)
        
        if db_resumes:
            resumes_by_job[job_id] = {
                'job': job,
                'resumes': db_resumes,
                'company': job_company,
                'title': job_title
            }
    
    # Display resumes grouped by job
    if resumes_by_job:
        for job_id, job_data in sorted(resumes_by_job.items(), key=lambda x: x[1]['company']):
            job = job_data['job']
            db_resumes = job_data['resumes']
            
            with st.expander(f"{job.get('company')} - {job.get('title')} ({len(db_resumes)} resume(s))", expanded=False):
                st.write(f"**Location:** {job.get('location', 'N/A')}")
                st.write(f"**Status:** {job.get('status', 'New')}")
                
                # Display each resume for this job
                for resume_data in db_resumes:
                    resume = resume_data['resume']
                    resume_id = resume_data['id']
                    file_path = resume_data.get('file_path')
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Resume ID:** {resume_id}")
                        st.write(f"**Name:** {resume.name}")
                        st.write(f"**Version:** {resume.version}")
                        if resume_data.get('is_customized'):
                            st.write("**Customized for this job**")
                        
                        # Try to find PDF
                        pdf_path = None
                        if file_path:
                            company = job.get('company', '')
                            title = job.get('title', '')
                            filename = resume_manager._sanitize_filename(f"{company}_{title}")
                            pdf_path = Path(file_path) / f"{filename}.pdf"
                            if not pdf_path.exists():
                                pdf_path = None
                        
                        # If not found by file_path, try to find in file system
                        if not pdf_path:
                            for file_resume in file_resumes:
                                expected_name = resume_manager._sanitize_filename(f"{job.get('company')}_{job.get('title')}")
                                if file_resume['filename'] == expected_name or file_resume['filename'].startswith(expected_name.split('_')[0]):
                                    pdf_path = file_resume['pdf_path']
                                    break
                        
                        if pdf_path and pdf_path.exists():
                            if st.button("Preview PDF", key=f"preview_{job_id}_{resume_id}"):
                                st.session_state[f"preview_{job_id}_{resume_id}"] = True
                    with col2:
                        if pdf_path and pdf_path.exists():
                            st.download_button(
                                "Download PDF",
                                data=pdf_path.read_bytes(),
                                file_name=pdf_path.name,
                                mime="application/pdf",
                                key=f"download_{job_id}_{resume_id}"
                            )
                    
                    # Show preview if requested
                    if st.session_state.get(f"preview_{job_id}_{resume_id}", False):
                        if pdf_path and pdf_path.exists():
                            render_resume_preview(pdf_path, {"company": job.get('company'), "title": job.get('title')})
                            if st.button("Close Preview", key=f"close_{job_id}_{resume_id}"):
                                st.session_state[f"preview_{job_id}_{resume_id}"] = False
                                st.rerun()
                    
                    st.divider()
    
    # Show unassigned resumes (from file system but not linked to jobs in database)
    unassigned_file_resumes = []
    assigned_filenames = set()
    for job_data in resumes_by_job.values():
        job = job_data['job']
        expected_name = resume_manager._sanitize_filename(f"{job.get('company')}_{job.get('title')}")
        assigned_filenames.add(expected_name)
    
    for resume_info in file_resumes:
        if resume_info['filename'] not in assigned_filenames:
            unassigned_file_resumes.append(resume_info)
    
    if unassigned_file_resumes:
        st.subheader("Other Resumes")
        for resume_info in unassigned_file_resumes:
            with st.expander(f"{resume_info['filename']} - {resume_info['created_at'].strftime('%Y-%m-%d %H:%M:%S')}", expanded=False):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Created:** {resume_info['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                    try:
                        with open(resume_info['json_path'], 'r', encoding='utf-8') as f:
                            resume_data = json.load(f)
                            resume = Resume.model_validate(resume_data)
                            st.write(f"**Name:** {resume.name}")
                    except:
                        pass
                    
                    if resume_info['pdf_path'] and resume_info['pdf_path'].exists():
                        if st.button("Preview PDF", key=f"preview_file_{resume_info['json_path']}"):
                            st.session_state[f"preview_file_{resume_info['json_path']}"] = True
                
                with col2:
                    if resume_info['pdf_path'] and resume_info['pdf_path'].exists():
                        st.download_button(
                            "Download PDF",
                            data=resume_info['pdf_path'].read_bytes(),
                            file_name=resume_info['pdf_path'].name,
                            mime="application/pdf",
                            key=f"download_file_{resume_info['json_path']}"
                        )
                
                if st.session_state.get(f"preview_file_{resume_info['json_path']}", False):
                    if resume_info['pdf_path'] and resume_info['pdf_path'].exists():
                        render_resume_preview(resume_info['pdf_path'])
                        if st.button("Close Preview", key=f"close_file_{resume_info['json_path']}"):
                            st.session_state[f"preview_file_{resume_info['json_path']}"] = False
                            st.rerun()
    
    if not resumes_by_job and not unassigned_file_resumes:
        st.info("No resumes generated yet. Generate a resume from the Jobs page.")

