"""Job details component for displaying job information."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Dict, List, Optional
import streamlit as st
from pathlib import Path
from src.db.database import Database
from src.matching.skill_matcher import SkillMatcher
from src.models.skills import SkillOntology
from src.models.resume import Resume


def _categorize_skills(skills: List[str], job_skills: Optional[List[str]] = None) -> Dict[str, List[str]]:
    """Categorize skills into groups for better organization.
    
    Args:
        skills: List of skill names to categorize
        job_skills: Optional list of job-relevant skills to prioritize
    
    Returns: Dict mapping category name to list of skills
    """
    from src.utils.skill_categorizer import categorize_skills as _categorize_skills
    return _categorize_skills(skills, job_skills)


def _display_skills_by_category(skills: List[str]):
    """Display skills organized by category."""
    categorized = _categorize_skills(skills)
    
    if not categorized:
        st.write("No skills to display")
        return
    
    # Display each category
    for category, skills_list in categorized.items():
        if category == "Other" and len(categorized) > 1:
            # Only show "Other" if there are other categories too
            with st.expander(f"{category} ({len(skills_list)})", expanded=False):
                for skill in skills_list:
                    st.write(f"• {skill}")
        else:
            # Use expandable sections for categories with many skills
            if len(skills_list) > 5:
                with st.expander(f"{category} ({len(skills_list)})", expanded=True):
                    # Split into columns if many skills
                    if len(skills_list) > 10:
                        cols = st.columns(2)
                        mid = len(skills_list) // 2
                        with cols[0]:
                            for skill in skills_list[:mid]:
                                st.write(f"• {skill}")
                        with cols[1]:
                            for skill in skills_list[mid:]:
                                st.write(f"• {skill}")
                    else:
                        for skill in skills_list:
                            st.write(f"• {skill}")
            else:
                st.write(f"**{category}:**")
                for skill in skills_list:
                    st.write(f"• {skill}")


def render_job_details(db: Database, job: dict):
    """Render job details panel."""
    st.header("Job Details")
    
    # Get full job object to access description
    job_obj = db.get_job(job['id'])
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**Company:** {job['company']}")
        st.write(f"**Title:** {job['title']}")
        if job.get('location'):
            st.write(f"**Location:** {job['location']}")
        
        # Primary action buttons - moved to top for better visibility
        st.divider()
        action_col1, action_col2, action_col3 = st.columns(3)
        
        with action_col1:
            if st.button("Generate Resume", type="primary", key=f"generate_resume_{job['id']}"):
                st.session_state['generate_resume_job_id'] = job['id']
                st.rerun()
        
        with action_col2:
            if st.button("View Match Details", key=f"view_match_{job['id']}"):
                st.session_state['view_match_job_id'] = job['id']
                st.rerun()
        
        with action_col3:
            if st.button("Generate Cover Letter", key=f"generate_cover_{job['id']}"):
                st.info("Cover letter generation coming soon (P1)")
        
        st.divider()
        
        # Check if workflow or match details is active - render those FIRST before job description
        workflow_active = ('resume_generation_state' in st.session_state and 
                          st.session_state.get('resume_generation_job_id') == job['id'])
        match_details_active = ('view_match_job_id' in st.session_state and 
                               st.session_state['view_match_job_id'] == job['id'])
        generate_resume_active = ('generate_resume_job_id' in st.session_state and 
                                 st.session_state['generate_resume_job_id'] == job['id'] and
                                 'resume_generation_state' not in st.session_state)
        
        # If any workflow is active, render it here (before job description)
        if workflow_active:
            # Get job and resume for workflow
            job_obj_workflow = db.get_job(job['id'])
            if job_obj_workflow:
                job_skills_workflow = db.get_job_skills(job['id'])
                if job_skills_workflow:
                    # Get resume
                    resume = db.get_latest_resume()
                    if not resume:
                        resume_path = Path("data/resume.json")
                        if resume_path.exists():
                            try:
                                import json
                                with open(resume_path, 'r', encoding='utf-8') as f:
                                    resume_data = json.load(f)
                                resume = Resume.model_validate(resume_data)
                            except Exception as e:
                                st.error(f"Failed to load resume from file: {e}")
                                return
                        else:
                            st.error("No resume found. Please convert LaTeX resume to JSON first.")
                            return
                    
                    # Get matcher and resume manager
                    ontology = SkillOntology()
                    matcher = SkillMatcher(ontology)
                    from src.storage.resume_manager import ResumeManager
                    resume_manager = ResumeManager()
                    
                    _handle_resume_generation_workflow(db, job['id'], resume, job_skills_workflow, matcher, resume_manager, job_obj_workflow)
                    return  # Exit early - don't show job description when workflow is active
        
        if generate_resume_active:
            _handle_generate_resume(db, job['id'])
            return  # Exit early - don't show job description when generating resume
        
        if match_details_active:
            _handle_view_match_details(db, job['id'])
            return  # Exit early - don't show job description when viewing match details
        
        # Display job description (only if no workflow is active)
        if job_obj and job_obj.description:
            st.subheader("Job Description")
            with st.expander("View Full Description", expanded=False):
                st.text_area("Job Description", value=job_obj.description, height=300, disabled=True, key=f"desc_{job['id']}", label_visibility="collapsed")
            # Show truncated version
            desc_preview = job_obj.description[:500] + "..." if len(job_obj.description) > 500 else job_obj.description
            st.write(desc_preview)
        elif job.get('description'):
            st.subheader("Job Description")
            with st.expander("View Full Description", expanded=False):
                st.text_area("Job Description", value=job.get('description'), height=300, disabled=True, key=f"desc_{job['id']}", label_visibility="collapsed")
            desc_preview = job.get('description', '')[:500] + "..." if len(job.get('description', '')) > 500 else job.get('description', '')
            st.write(desc_preview)
    
    with col2:
        delete_key = f"delete_btn_{job['id']}"
        if st.button("Delete Job", type="secondary", key=delete_key):
            st.session_state[f'delete_job_id'] = job['id']
            st.session_state[f'delete_confirm_{job["id"]}'] = True
            st.rerun()
        
        # Handle delete confirmation - appears right beneath Delete button
        if st.session_state.get(f'delete_confirm_{job["id"]}', False):
            st.warning("Are you sure you want to delete this job? This action cannot be undone.")
            confirm_col1, confirm_col2 = st.columns(2)
            with confirm_col1:
                confirm_key = f"confirm_delete_{job['id']}"
                if st.button("Yes, Delete", type="primary", key=confirm_key):
                    try:
                        db.delete_job(job['id'])
                        st.success("Job deleted successfully")
                        # Clean up session state
                        if f'delete_job_id' in st.session_state:
                            del st.session_state[f'delete_job_id']
                        if f'delete_confirm_{job["id"]}' in st.session_state:
                            del st.session_state[f'delete_confirm_{job["id"]}']
                        if 'selected_job_id' in st.session_state:
                            del st.session_state['selected_job_id']
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting job: {e}")
                        import traceback
                        st.exception(e)
            with confirm_col2:
                cancel_key = f"cancel_delete_{job['id']}"
                if st.button("Cancel", key=cancel_key):
                    if f'delete_confirm_{job["id"]}' in st.session_state:
                        del st.session_state[f'delete_confirm_{job["id"]}']
                    if f'delete_job_id' in st.session_state:
                        del st.session_state[f'delete_job_id']
                    st.rerun()
    
    # Get job skills
    job_skills = db.get_job_skills(job['id'])
    if job_skills:
        st.subheader("Required Skills")
        if job_skills.required_skills:
            _display_skills_by_category(job_skills.required_skills)
        else:
            st.write("None specified")
        
        if job_skills.preferred_skills:
            st.subheader("Preferred Skills")
            _display_skills_by_category(job_skills.preferred_skills)
        
        if job_skills.soft_skills:
            st.subheader("Soft Skills")
            st.write(", ".join(job_skills.soft_skills))
    
    # Note: Workflow and match details handling is now done at the top of the function
    # (right after buttons) to ensure they appear before job description


def _handle_generate_resume(db: Database, job_id: int):
    """Handle resume generation workflow."""
    from src.matching.resume_reuse_checker import ResumeReuseChecker
    from src.storage.resume_manager import ResumeManager
    from src.gui.resume_preview import render_resume_preview
    
    # Get job and skills
    job = db.get_job(job_id)
    if not job:
        st.error("Job not found.")
        return
    
    job_skills = db.get_job_skills(job_id)
    if not job_skills:
        # Try to extract skills from job description
        st.info("Job skills not found. Extracting skills from job description...")
        try:
            from src.extractors.job_skills import JobSkillExtractor
            extractor = JobSkillExtractor()
            job_skills = extractor.extract_skills(job)
            # Save extracted skills to database
            db.save_job(job, job_skills=job_skills)
            st.success("Skills extracted and saved!")
        except Exception as e:
            st.error(f"Could not extract skills: {e}")
            return
    
    # Check for existing resume in organized storage
    resume_manager = ResumeManager()
    existing_resume_path = resume_manager.get_resume_by_job(job)
    
    if existing_resume_path and existing_resume_path.exists():
        st.success(f"Found existing resume for this job!")
        render_resume_preview(existing_resume_path, {"company": job.company, "title": job.title})
        
        if st.button("Generate New Resume", type="primary"):
            st.session_state['generate_new'] = True
            st.rerun()
        return
    
    # Check for reusable resume
    ontology = SkillOntology()
    matcher = SkillMatcher(ontology)
    reuse_checker = ResumeReuseChecker(db, matcher)
    
    reusable = reuse_checker.find_reusable_resume(
        job_skills,
        target_job_id=job_id,
        min_fit_score=0.90,
        min_similarity=0.85,
    )
    
    if reusable:
        resume_id, reused_resume, fit_score, similarity = reusable
        st.success(f"Found reusable resume! (ID: {resume_id}, Fit: {fit_score:.2%}, Similarity: {similarity:.2%})")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Use Existing Resume", type="primary"):
                # Save using ResumeManager
                resume_dir = resume_manager.save_resume(
                    reused_resume,
                    job=job,
                    is_customized=True
                )
                # Save to database
                resume_db_id = db.save_resume(
                    reused_resume,
                    file_path=str(resume_dir),
                    job_id=job_id,
                    is_customized=True
                )
                st.success(f"Resume saved! (ID: {resume_db_id})")
                st.rerun()
        with col2:
            if st.button("Generate New Resume"):
                st.session_state['generate_new'] = True
                st.rerun()
    else:
        # Get latest resume - try database first, then file
        resume = db.get_latest_resume()
        if not resume:
            # Try loading from file
            resume_path = Path("data/resume.json")
            if resume_path.exists():
                try:
                    import json
                    with open(resume_path, 'r', encoding='utf-8') as f:
                        resume_data = json.load(f)
                    resume = Resume.model_validate(resume_data)
                    st.info("Loaded resume from data/resume.json")
                except Exception as e:
                    st.error(f"Failed to load resume from file: {e}")
                    return
            else:
                st.error("No resume found. Please convert LaTeX resume to JSON first using: `ats convert-latex templates/resume.tex`")
                return
        
        # Match job
        job_match = matcher.match_job(resume, job_skills)
        
        st.info(f"Job fit score: {job_match.fit_score:.2%}")
        
        # Generate resume button - trigger full workflow
        if st.button("Generate Customized Resume", type="primary", key=f"gen_resume_{job_id}"):
            st.session_state['resume_generation_state'] = 'start'
            st.session_state['resume_generation_job_id'] = job_id
            st.session_state['original_resume_for_diff'] = resume.model_dump_json()  # Store for diff
            st.rerun()
        
        # Show match details
        with st.expander("View Match Details", expanded=False):
            # Add refresh button
            refresh_col1, refresh_col2 = st.columns([1, 10])
            with refresh_col1:
                if st.button("↻", help="Refresh match details", key=f"refresh_match_{job_id}"):
                    # Re-run matching
                    job_match = matcher.match_job(resume, job_skills)
                    resume_id = db.get_latest_resume_id()
                    if resume_id:
                        db.save_job_match(job_match, job_id, resume_id)
                    st.rerun()
            
            st.write(f"**Fit Score:** {job_match.fit_score:.2%}")
            
            if job_match.matching_skills:
                st.write(f"**Matching Skills ({len(job_match.matching_skills)}):**")
                st.write(", ".join(job_match.matching_skills[:20]))
                if len(job_match.matching_skills) > 20:
                    st.write(f"... and {len(job_match.matching_skills) - 20} more")
            
            if job_match.skill_gaps.get("required_missing"):
                st.write(f"**Missing Required Skills ({len(job_match.skill_gaps['required_missing'])}):**")
                st.write(", ".join(job_match.skill_gaps["required_missing"][:20]))
            
            if job_match.skill_gaps.get("preferred_missing"):
                st.write(f"**Missing Preferred Skills ({len(job_match.skill_gaps['preferred_missing'])}):**")
                st.write(", ".join(job_match.skill_gaps["preferred_missing"][:20]))
            
            if job_match.missing_skills:
                st.write(f"**Skills Not in Resume ({len(job_match.missing_skills)}):**")
                st.write(", ".join(job_match.missing_skills[:20]))
            
            if job_match.recommendations:
                st.write("**Recommendations:****")
                for rec in job_match.recommendations:
                    st.write(f"- {rec}")


def _handle_resume_generation_workflow(
    db: Database, 
    job_id: int, 
    resume: Resume, 
    job_skills, 
    matcher: SkillMatcher,
    resume_manager,
    job
):
    """Handle the full resume generation workflow with thinking process and approval."""
    from src.compilation.resume_rewriter import ResumeRewriter
    from src.gui.approval_workflow import render_approval_workflow
    from src.gui.resume_preview import render_resume_preview
    from src.rendering.latex_renderer import LaTeXRenderer
    import tempfile
    
    state = st.session_state.get('resume_generation_state', 'start')
    
    if state == 'start':
        st.header("Resume Generation Workflow")
        st.progress(0.25, text="Step 1 of 4: Analyzing job requirements...")
        
        # Match job to get gap analysis
        with st.spinner("Analyzing job requirements and identifying improvements..."):
            job_match = matcher.match_job(resume, job_skills)
        
        st.write(f"**Initial Fit Score:** {job_match.fit_score:.2%}")
        
        if job_match.skill_gaps.get("required_missing"):
            st.write(f"**Missing Required Skills:** {', '.join(job_match.skill_gaps['required_missing'][:10])}")
        if job_match.skill_gaps.get("preferred_missing"):
            st.write(f"**Missing Preferred Skills:** {', '.join(job_match.skill_gaps['preferred_missing'][:10])}")
        
        # Initialize rewriter with user skills to prevent fabricated technologies
        from src.models.skills import UserSkills
        from pathlib import Path as _Path
        import json as _json
        
        user_skills_obj = None
        skills_path = _Path("data/user_skills.json")
        if skills_path.exists():
            try:
                with skills_path.open("r", encoding="utf-8") as f:
                    user_skills_data = _json.load(f)
                user_skills_obj = UserSkills.model_validate(user_skills_data)
            except Exception:
                # If loading fails, fall back to None (no whitelist) but do not break flow
                user_skills_obj = None
        
        rewriter = ResumeRewriter(user_skills=user_skills_obj)
        
        # Generate proposals (default to emphasize_skills mode)
        st.progress(0.5, text="Step 2 of 4: Generating bullet variations with reasoning...")
        with st.spinner("Generating bullet variations with reasoning..."):
            default_intent = "emphasize_skills"
            proposals = rewriter.generate_variations(resume, job_match, SkillOntology(), rewrite_intent=default_intent)
        
        if not proposals:
            st.info("No bullets need adjustment. Your resume is already well-matched!")
            if st.button("Save Resume Anyway"):
                resume_dir = resume_manager.save_resume(resume, job=job, is_customized=True)
                resume_db_id = db.save_resume(resume, file_path=str(resume_dir), job_id=job_id, is_customized=True)
                st.success(f"Resume saved! (ID: {resume_db_id})")
                del st.session_state['resume_generation_state']
                st.rerun()
            return
        
        st.success(f"Found {len(proposals)} bullets that can be improved!")
        st.session_state['resume_proposals'] = proposals
        st.session_state['resume_generation_state'] = 'approval'
        st.session_state['current_bullet_index'] = 0
        st.session_state['approved_bullets'] = {}
        st.session_state['resume_rewriter'] = rewriter
        st.session_state['job_match_for_approval'] = job_match
        
        # Store original resume for ATS keyword tracking and content optimization
        import json
        st.session_state['original_resume_for_ats'] = resume.model_dump_json()
        st.session_state['ats_job_skills'] = job_skills
        st.session_state['job_match_for_optimization'] = job_match.model_dump_json()
        
        st.rerun()
    
    elif state == 'approval':
        proposals = st.session_state.get('resume_proposals', {})
        bullet_index = st.session_state.get('current_bullet_index', 0)
        approved_bullets = st.session_state.get('approved_bullets', {})
        
        bullet_keys = list(proposals.keys())
        total_bullets = len(bullet_keys)
        progress = 0.5 + (bullet_index / total_bullets) * 0.3  # 50% to 80%
        st.progress(progress, text=f"Step 3 of 4: Reviewing bullets ({bullet_index + 1}/{total_bullets})...")
        
        if bullet_index >= len(bullet_keys):
            # All bullets processed, move to preview
            st.session_state['resume_generation_state'] = 'preview'
            st.rerun()
            return
        
        bullet_key = bullet_keys[bullet_index]
        reasoning, variations = proposals[bullet_key]
        
        # Find the original bullet
        original_bullet = None
        if bullet_key.startswith('exp_'):
            # Experience bullet
            parts = bullet_key.split('_', 2)
            org = parts[1]
            idx = int(parts[2]) if len(parts) > 2 else 0
            for exp in resume.experience:
                if exp.organization == org:
                    if idx < len(exp.bullets):
                        original_bullet = exp.bullets[idx]
                    break
        elif bullet_key.startswith('proj_'):
            # Project bullet
            parts = bullet_key.split('_', 2)
            proj_name = parts[1]
            idx = int(parts[2]) if len(parts) > 2 else 0
            for proj in resume.projects:
                if proj.name == proj_name:
                    if idx < len(proj.bullets):
                        original_bullet = proj.bullets[idx]
                    break
        
        if not original_bullet:
            st.error(f"Could not find original bullet for {bullet_key}")
            st.session_state['current_bullet_index'] += 1
            st.rerun()
            return
        
        # Build project context map for regeneration
        project_context_map = {}
        project_name_map = {}
        bullet_id = 0
        for proj in resume.projects:
            for bullet in proj.bullets:
                proj_key = f"proj_{proj.name}_{bullet_id}"
                project_context_map[proj_key] = proj.tech_stack
                project_name_map[proj_key] = proj.name
                bullet_id += 1
        
        # Get current rewrite intent from session state or default
        current_rewrite_intent = st.session_state.get(f'rewrite_intent_{bullet_key}', None)
        
        # Get rewriter instance (store in session state if not available)
        if 'resume_rewriter' not in st.session_state:
            from src.models.skills import UserSkills
            from pathlib import Path as _Path
            import json as _json
            user_skills_obj = None
            skills_path = _Path("data/user_skills.json")
            if skills_path.exists():
                try:
                    with skills_path.open("r", encoding="utf-8") as f:
                        user_skills_data = _json.load(f)
                    user_skills_obj = UserSkills.model_validate(user_skills_data)
                except Exception:
                    user_skills_obj = None
            st.session_state['resume_rewriter'] = ResumeRewriter(user_skills=user_skills_obj)
            st.session_state['user_skills_obj'] = user_skills_obj
        
        rewriter = st.session_state['resume_rewriter']
        job_match = st.session_state.get('job_match_for_approval')
        if not job_match:
            # Recreate job match if needed
            ontology = SkillOntology()
            matcher = SkillMatcher(ontology)
            job_skills = st.session_state.get('ats_job_skills')
            if job_skills:
                job_match = matcher.match_job(resume, job_skills)
                st.session_state['job_match_for_approval'] = job_match
        
        # Render approval workflow
        result = render_approval_workflow(
            original_bullet,
            reasoning,
            variations,
            bullet_index + 1,
            len(bullet_keys),
            rewrite_intent=current_rewrite_intent
        )
        
        if result[0] is True:  # Approved
            selected_idx = result[1]
            approved_bullets[bullet_key] = variations[selected_idx]
            st.session_state['approved_bullets'] = approved_bullets
            st.session_state['current_bullet_index'] += 1
            st.rerun()
        elif result[0] is False:  # Rejected
            st.session_state['current_bullet_index'] += 1
            st.rerun()
        elif result[2] is not None:  # Rewrite intent changed - regenerate
            # Store new intent and regenerate
            st.session_state[f'rewrite_intent_{bullet_key}'] = result[2]
            # Regenerate with new intent
            if job_match:
                new_reasoning = rewriter._generate_reasoning(original_bullet, job_match, SkillOntology())
                new_candidates = rewriter._generate_candidates_with_reasoning(
                    original_bullet, new_reasoning, job_match, SkillOntology(),
                    project_context=project_context_map.get(bullet_key),
                    project_name=project_name_map.get(bullet_key),
                    rewrite_intent=result[2]
                )
                # Validate candidates
                allowed_job_skills = rewriter._get_allowed_job_skills_for_user(job_match)
                valid_candidates = []
                for candidate in new_candidates:
                    is_valid, errors = rewriter.validator.validate(
                        candidate, 
                        original_bullet.text, 
                        job_skills=allowed_job_skills if allowed_job_skills else None,
                        rewrite_intent=result[2]
                    )
                    if is_valid:
                        valid_candidates.append(candidate)
                # Rank candidates
                if valid_candidates:
                    ranked_candidates = rewriter.scorer.rank_candidates(valid_candidates, original_bullet.text, job_match)
                    for candidate in ranked_candidates:
                        candidate.risk_level = rewriter.scorer.calculate_risk_level(candidate, original_bullet.text)
                    new_candidates = ranked_candidates
                # Update proposals
                proposals[bullet_key] = (new_reasoning, new_candidates)
                st.session_state['resume_proposals'] = proposals
            st.rerun()
        # If None, waiting for user input
    
    elif state == 'preview':
        st.header("Final Resume Preview")
        st.progress(0.9, text="Step 4 of 4: Generating PDF preview...")
        st.write("**Review your customized resume before confirming:**")
        
        # Apply approved changes to resume
        updated_resume = resume.model_copy(deep=True)
        approved_bullets = st.session_state.get('approved_bullets', {})
        
        # Import Bullet model for conversion
        from src.models.resume import Bullet, BulletCandidate
        
        # Apply changes to experience bullets
        bullet_id = 0
        for exp in updated_resume.experience:
            for i, bullet in enumerate(exp.bullets):
                bullet_key = f"exp_{exp.organization}_{bullet_id}"
                if bullet_key in approved_bullets:
                    approved = approved_bullets[bullet_key]
                    # Convert BulletCandidate to Bullet if needed
                    if isinstance(approved, BulletCandidate):
                        # Create new Bullet with text from BulletCandidate, preserve skills from original
                        exp.bullets[i] = Bullet(
                            text=approved.text,
                            skills=bullet.skills.copy() if bullet.skills else [],
                            evidence=bullet.evidence,
                            history=bullet.history.copy() if bullet.history else []
                        )
                    else:
                        # Already a Bullet object
                        exp.bullets[i] = approved
                bullet_id += 1
        
        # Apply changes to project bullets
        bullet_id = 0
        for proj in updated_resume.projects:
            for i, bullet in enumerate(proj.bullets):
                bullet_key = f"proj_{proj.name}_{bullet_id}"
                if bullet_key in approved_bullets:
                    approved = approved_bullets[bullet_key]
                    # Convert BulletCandidate to Bullet if needed
                    if isinstance(approved, BulletCandidate):
                        # Create new Bullet with text from BulletCandidate, preserve skills from original
                        proj.bullets[i] = Bullet(
                            text=approved.text,
                            skills=bullet.skills.copy() if bullet.skills else [],
                            evidence=bullet.evidence,
                            history=bullet.history.copy() if bullet.history else []
                        )
                    else:
                        # Already a Bullet object
                        proj.bullets[i] = approved
                bullet_id += 1
        
        # Update skills section - ONLY use skills from user_skills.json (skills page)
        from src.utils.skill_categorizer import categorize_skills, validate_and_clean_skills_with_openai
        from src.models.skills import UserSkills
        import json
        import time
        from pathlib import Path
        
        # #region agent log
        with open('/home/swesan/repos/ats-pipeline/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run3","hypothesisId":"A","location":"job_details.py:564","message":"Original resume.skills","data":{"original_skills":resume.skills},"timestamp":int(time.time()*1000)}) + '\n')
        # #endregion
        
        # Load skills ONLY from user_skills.json (skills page)
        skills_file = Path("data/user_skills.json")
        user_skills_list = []
        if skills_file.exists():
            try:
                with open(skills_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    user_skills_obj = UserSkills.model_validate(data)
                    user_skills_list = [skill.name for skill in user_skills_obj.skills]
            except Exception as e:
                st.warning(f"Could not load user skills: {e}")
        
        # #region agent log
        with open('/home/swesan/repos/ats-pipeline/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run3","hypothesisId":"A","location":"job_details.py:580","message":"Skills from user_skills.json","data":{"user_skills_list":user_skills_list},"timestamp":int(time.time()*1000)}) + '\n')
        # #endregion
        
        # Get job skills for prioritization
        job_skills_list = []
        if job_skills:
            job_skills_list = job_skills.required_skills + job_skills.preferred_skills
        
        # Validate and clean skills with OpenAI
        validated_skills = validate_and_clean_skills_with_openai(user_skills_list, job_skills_list)
        
        # #region agent log
        with open('/home/swesan/repos/ats-pipeline/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run3","hypothesisId":"A","location":"job_details.py:590","message":"After OpenAI validation","data":{"validated_skills":validated_skills},"timestamp":int(time.time()*1000)}) + '\n')
        # #endregion
        
        # Categorize and update skills section (without "Other" category)
        categorized_skills = categorize_skills(validated_skills, job_skills_list)
        
        # #region agent log
        with open('/home/swesan/repos/ats-pipeline/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run3","hypothesisId":"C","location":"job_details.py:600","message":"Final categorized skills","data":{"categorized_skills":categorized_skills},"timestamp":int(time.time()*1000)}) + '\n')
        # #endregion
        
        updated_resume.skills = categorized_skills
        
        # Optimize content order within sections by job relevance
        if job_skills and 'job_match_for_optimization' in st.session_state:
            try:
                from src.compilation.content_optimizer import ResumeContentOptimizer
                from src.models.job import JobMatch
                job_match = JobMatch.model_validate_json(st.session_state['job_match_for_optimization'])
                optimizer = ResumeContentOptimizer(job_match, job_skills)
                updated_resume = optimizer.optimize_all(updated_resume)
            except Exception as e:
                # If optimization fails, continue without it
                pass
        
        # Show diff view - get original resume from session state if stored
        original_for_diff = resume
        if 'original_resume_for_diff' in st.session_state:
            try:
                import json
                original_for_diff = Resume.model_validate_json(st.session_state['original_resume_for_diff'])
            except:
                pass  # Use current resume if parsing fails
        
        from src.gui.resume_diff import render_resume_diff
        # Pass job_skills for ATS highlighting in both PDFs
        render_resume_diff(original_for_diff, updated_resume, job, job_skills=job_skills)
        
        # Generate PDF preview
        try:
            renderer = LaTeXRenderer()
            preview_path = Path("data/resume_preview_temp.pdf")
            preview_path.parent.mkdir(exist_ok=True, parents=True)
            
            # Create ATS keyword tracker for highlighting
            # Note: The renderer uses updated_resume's bullet text, and the tracker's job_relevant_keywords
            # are based on job_skills (not the resume), so highlighting will work correctly on updated bullets
            ats_tracker = None
            if 'original_resume_for_ats' in st.session_state and 'ats_job_skills' in st.session_state:
                try:
                    original_resume = Resume.model_validate_json(st.session_state['original_resume_for_ats'])
                    from src.utils.ats_keyword_tracker import ATSKeywordTracker
                    # Tracker is initialized with original resume for change tracking, but job_relevant_keywords
                    # come from job_skills, so highlighting works on updated resume bullets
                    ats_tracker = ATSKeywordTracker(original_resume, st.session_state['ats_job_skills'])
                except Exception as e:
                    # If tracker creation fails, continue without it
                    pass
            
            with st.spinner("Generating PDF preview..."):
                renderer.render_pdf(updated_resume, preview_path, ats_tracker)
            
            if preview_path.exists():
                st.progress(1.0, text="PDF preview ready!")
                render_resume_preview(preview_path, {"company": job.company, "title": job.title})
            
            # Confirmation buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Confirm and Save", type="primary"):
                    # Save using ResumeManager
                    resume_dir = resume_manager.save_resume(updated_resume, job=job, is_customized=True)
                    resume_db_id = db.save_resume(updated_resume, file_path=str(resume_dir), job_id=job_id, is_customized=True)
                    st.success(f"Resume saved! (ID: {resume_db_id})")
                    # Clean up
                    for key in ['resume_generation_state', 'resume_proposals', 'current_bullet_index', 'approved_bullets', 'resume_generation_job_id']:
                        if key in st.session_state:
                            del st.session_state[key]
                    if preview_path.exists():
                        preview_path.unlink()  # Clean up temp file
                    st.rerun()
            
            with col2:
                if st.button("Cancel"):
                    for key in ['resume_generation_state', 'resume_proposals', 'current_bullet_index', 'approved_bullets', 'resume_generation_job_id']:
                        if key in st.session_state:
                            del st.session_state[key]
                    if preview_path.exists():
                        preview_path.unlink()
                    st.rerun()
        except Exception as e:
            st.error(f"Error generating preview: {e}")
            import traceback
            st.exception(e)


def _handle_view_match_details(db: Database, job_id: int):
    """Handle view match details workflow."""
    # Get job and skills
    job = db.get_job(job_id)
    if not job:
        st.error("Job not found.")
        return
    
    job_skills = db.get_job_skills(job_id)
    if not job_skills:
        # Try to extract skills from job description
        st.info("Job skills not found. Extracting skills from job description...")
        try:
            from src.extractors.job_skills import JobSkillExtractor
            extractor = JobSkillExtractor()
            job_skills = extractor.extract_skills(job)
            # Save extracted skills to database
            db.save_job(job, job_skills=job_skills)
            st.success("Skills extracted and saved!")
        except Exception as e:
            st.error(f"Could not extract skills: {e}")
            return
    
    # Get resume - try database first, then file
    resume = db.get_latest_resume()
    if not resume:
        # Try loading from file
        resume_path = Path("data/resume.json")
        if resume_path.exists():
            try:
                import json
                with open(resume_path, 'r', encoding='utf-8') as f:
                    resume_data = json.load(f)
                resume = Resume.model_validate(resume_data)
            except Exception as e:
                st.error(f"Failed to load resume from file: {e}")
                return
        else:
            st.error("No resume found. Please convert LaTeX resume to JSON first using: `ats convert-latex templates/resume.tex`")
            return
    
    # Match job
    ontology = SkillOntology()
    matcher = SkillMatcher(ontology)
    job_match = matcher.match_job(resume, job_skills)
    
    # Display match details
    st.subheader("Match Details")
    st.write(f"**Job:** {job.title} at {job.company}")
    if job.location:
        st.write(f"**Location:** {job.location}")
    st.write(f"**Fit Score:** {job_match.fit_score:.1%}")
    
    st.divider()
    
    # Display job requirements in organized format
    st.subheader("Job Requirements")
    
    if job_skills.required_skills:
        st.write("**Required Skills:**")
        _display_skills_by_category(job_skills.required_skills)
    
    if job_skills.preferred_skills:
        st.write("**Preferred Skills:**")
        _display_skills_by_category(job_skills.preferred_skills)
    
    if job_skills.soft_skills:
        st.write("**Soft Skills:**")
        st.write(", ".join(job_skills.soft_skills))
    
    st.divider()
    
    if job_match.matching_skills:
        st.subheader(f"Matching Skills ({len(job_match.matching_skills)})")
        # Display in columns if many
        if len(job_match.matching_skills) > 20:
            cols = st.columns(2)
            mid = len(job_match.matching_skills) // 2
            with cols[0]:
                for skill in job_match.matching_skills[:mid]:
                    st.write(f"- {skill}")
            with cols[1]:
                for skill in job_match.matching_skills[mid:]:
                    st.write(f"- {skill}")
        else:
            for skill in job_match.matching_skills:
                st.write(f"✓ {skill}")
    
    st.divider()
    
    if job_match.skill_gaps.get("required_missing"):
        st.subheader(f"Missing Required Skills ({len(job_match.skill_gaps['required_missing'])})")
        for skill in job_match.skill_gaps["required_missing"]:
            st.write(f"- {skill}")
    
    if job_match.skill_gaps.get("preferred_missing"):
        st.subheader(f"Missing Preferred Skills ({len(job_match.skill_gaps['preferred_missing'])})")
        for skill in job_match.skill_gaps["preferred_missing"]:
            st.write(f"- {skill}")
    
    if job_match.missing_skills:
        st.subheader(f"Skills Not in Resume ({len(job_match.missing_skills)})")
        st.write("These skills are required/preferred but not found in your resume:")
        for skill in job_match.missing_skills:
            st.write(f"• {skill}")
    
    st.divider()
    
    if job_match.recommendations:
        st.subheader("Recommendations")
        for rec in job_match.recommendations:
            st.write(f"• {rec}")

