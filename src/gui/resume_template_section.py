"""Resume template upload and preview section for GUI."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import json
from src.parsers.latex_resume import LaTeXResumeParser
from src.rendering.latex_renderer import LaTeXRenderer
from src.models.resume import Resume


def render_resume_template_section():
    """Render resume template upload and preview section."""
    st.header("Resume Template")
    
    template_path = Path("templates/resume.tex")
    resume_json_path = Path("data/resume.json")
    
    # Upload new template
    st.subheader("Upload Template")
    uploaded_file = st.file_uploader("Upload LaTeX Resume Template", type=['tex'], key="template_upload")
    
    if uploaded_file is not None:
        if st.button("Save Template", type="primary"):
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
                    parser = LaTeXResumeParser.from_file(template_path)
                    resume = parser.parse()
                    
                    # Append Experience, Projects, and Skills to existing libraries
                    from src.storage.experience_library import ExperienceLibrary
                    from src.projects.project_library import ProjectLibrary
                    from src.models.skills import UserSkills, UserSkill
                    
                    # Append experience
                    exp_library = ExperienceLibrary()
                    for exp_item in resume.experience:
                        exp_library.add_experience(exp_item)
                    
                    # Append projects
                    proj_library = ProjectLibrary()
                    for proj in resume.projects:
                        proj_library.add_project(proj)
                    
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
                                    projects=[]
                                )
                                user_skills.skills.append(new_skill)
                    
                    # Save updated skills
                    with open(skills_file, 'w', encoding='utf-8') as f:
                        json.dump(user_skills.model_dump(), f, indent=2, default=str)
                    
                    # Save to resume.json
                    resume_json_path.parent.mkdir(exist_ok=True, parents=True)
                    with open(resume_json_path, 'w', encoding='utf-8') as f:
                        json.dump(resume.model_dump(), f, indent=2, default=str)
                    
                    st.success("Template parsed and saved to resume.json")
                    st.info(f"Appended {len(resume.experience)} experience entries, {len(resume.projects)} projects, and skills to your libraries.")
                    st.rerun()
                except Exception as e:
                    st.warning(f"Template saved but parsing failed: {e}")
                    st.info("You can manually convert using: `ats convert-latex templates/resume.tex`")
            except Exception as e:
                st.error(f"Error saving template: {e}")
    
    # Show current template info
    if template_path.exists():
        st.subheader("Current Template")
        st.write(f"**Location:** `{template_path}`")
        
        # Preview template
        with st.expander("View Template Source", expanded=False):
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            st.code(template_content, language='latex')
        
        # Preview parsed resume
        if resume_json_path.exists():
            st.subheader("Resume Preview")
            try:
                with open(resume_json_path, 'r', encoding='utf-8') as f:
                    resume_data = json.load(f)
                resume = Resume.model_validate(resume_data)
                
                # Show resume info
                st.write(f"**Name:** {resume.name}")
                st.write(f"**Email:** {resume.email}")
                if resume.phone:
                    st.write(f"**Phone:** {resume.phone}")
                
                # Preview sections
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Experience Items:** {len(resume.experience)}")
                    st.write(f"**Projects:** {len(resume.projects)}")
                with col2:
                    st.write(f"**Education:** {len(resume.education)}")
                    st.write(f"**Skills Categories:** {len(resume.skills)}")
                
                # Generate PDF preview
                if st.button("Generate PDF Preview", type="primary"):
                    try:
                        renderer = LaTeXRenderer(template_path)
                        pdf_path = Path("data/resume_preview.pdf")
                        pdf_path.parent.mkdir(exist_ok=True, parents=True)
                        
                        with st.spinner("Generating PDF..."):
                            renderer.render_pdf(resume, pdf_path)
                        
                        st.success("PDF generated!")
                        
                        # Show PDF preview
                        if pdf_path.exists():
                            with open(pdf_path, "rb") as pdf_file:
                                pdf_bytes = pdf_file.read()
                            
                            # Use iframe for PDF preview (works without extra components)
                            import base64
                            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                            st.markdown(pdf_display, unsafe_allow_html=True)
                            
                            # Download button
                            st.download_button(
                                label="Download PDF",
                                data=pdf_bytes,
                                file_name="resume_preview.pdf",
                                mime="application/pdf"
                            )
                    except Exception as e:
                        st.error(f"Error generating PDF: {e}")
                        import traceback
                        st.exception(e)
                
            except Exception as e:
                st.error(f"Error loading resume: {e}")
        else:
            st.info("No resume.json found. Upload a template and it will be automatically converted.")
    else:
        st.info("No template uploaded yet. Upload a LaTeX resume template above.")

