"""Job details component for displaying job information."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Dict, List
import streamlit as st
from pathlib import Path
from src.db.database import Database
from src.matching.skill_matcher import SkillMatcher
from src.models.skills import SkillOntology
from src.models.resume import Resume


def _categorize_skills(skills: List[str]) -> Dict[str, List[str]]:
    """Categorize skills into groups for better organization.
    
    Returns: Dict mapping category name to list of skills
    """
    # Define skill categories with keywords (order matters - more specific first)
    # Check more specific categories first to avoid false matches
    skill_categories = {
        # Infrastructure categories (check first - most specific)
        "Kubernetes & Orchestration": ["kubernetes", "k8s", "rke", "kopf", "kube-ovn", "kubevirt", "operator", "cncf", "helm"],
        "Virtualization & Bare Metal": ["vmware", "esxi", "vcenter", "kvm", "xen", "ironic", "metal3", "virtualization", "bare-metal", "provisioning"],
        "Storage": ["ceph", "weka", "qumulo", "nfs", "s3", "powerstore", "rook", "storage", "object storage", "block storage", "file storage"],
        "Networking": ["bgp", "evpn", "sonic", "infiniband", "rdma", "roce", "leaf/spine", "topology", "network fabric", "throughput", "tcp/ip"],
        "Cloud & Infrastructure": ["aws", "azure", "gcp", "cloudformation", "cloud", "infrastructure", "iaas", "paas", "saas"],
        "DevOps & CI/CD": ["terraform", "ansible", "jenkins", "gitlab", "github actions", "circleci", "travis", "bamboo", "devops", "ci/cd", "pipeline", "deployment", "automation", "iac"],
        "Operating Systems": ["ubuntu", "debian", "centos", "rhel", "windows", "linux", "os management", "kernel", "system"],
        "Hardware & Platforms": ["supermicro", "dell", "hardware", "platform", "architecture", "compute", "data center", "datacenter"],
        # AI/ML (check before languages to catch HPC terms)
        "AI/ML & HPC": ["tensorflow", "pytorch", "keras", "scikit-learn", "numpy", "pandas", "nccl", "nvidia", "gpu", "a100", "h200", "gh200", "blackwell", "hopper", "ampere", "hpc", "high-performance", "distributed training", "machine learning", "deep learning", "neural", "cnn", "rnn"],
        # APIs (check before languages to catch FastAPI, etc.)
        "APIs & Microservices": ["fastapi", "rest", "graphql", "api", "microservices", "backend api", "asyncio", "pydantic"],
        # Databases (check before languages)
        "Databases": ["postgresql", "mysql", "mongodb", "redis", "cassandra", "dynamodb", "elasticsearch", "sql", "nosql", "database", "db", "relational"],
        # Languages (check later - less specific)
        "Languages": ["python", "java", "c++", "c#", "javascript", "typescript", "go", "golang", "rust", "ruby", "php", "r", "matlab", "swift", "kotlin", "scala", "clojure", "c", "cpp"],
        # Frameworks (check after languages)
        "Frameworks & Libraries": ["react", "vue", "angular", "django", "flask", "express", "spring", "rails", "laravel", "framework", "library"],
        "Security": ["security", "firewall", "vpn", "ssl", "tls", "encryption", "authentication", "authorization", "jwt", "oauth", "saml", "gateway", "policy"],
        "Monitoring & Observability": ["prometheus", "grafana", "datadog", "new relic", "splunk", "elk", "monitoring", "logging", "observability", "metrics", "troubleshooting", "root-cause"],
        "Other": []  # Uncategorized skills
    }
    
    categorized = {category: [] for category in skill_categories.keys()}
    
    for skill in skills:
        skill_lower = skill.lower()
        categorized_flag = False
        
        # Try to match skill to a category (check more specific categories first)
        for category, patterns in skill_categories.items():
            if category == "Other":
                continue
            
            # Handle both dict format (new) and list format (old)
            if isinstance(patterns, dict):
                keywords = patterns.get("keywords", [])
                exclude = patterns.get("exclude", [])
            else:
                # Old format - list of keywords
                keywords = patterns
                exclude = []
            
            # Skip if skill contains excluded terms (unless it's a very specific match)
            if exclude and any(exc in skill_lower for exc in exclude):
                # Only skip if it's a generic match, not a specific one
                has_specific_match = any(kw == skill_lower or kw in skill_lower.split() for kw in keywords)
                if not has_specific_match:
                    continue
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                # Check for exact word match or if keyword is contained in skill
                if (keyword_lower == skill_lower or
                    keyword_lower in skill_lower or
                    any(word == keyword_lower for word in skill_lower.split()) or
                    any(keyword_lower in word for word in skill_lower.split())):
                    categorized[category].append(skill)
                    categorized_flag = True
                    break
            if categorized_flag:
                break
        
        # If not categorized, add to "Other"
        if not categorized_flag:
            categorized["Other"].append(skill)
    
    # Remove empty categories
    return {cat: skills_list for cat, skills_list in categorized.items() if skills_list}


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
        
        # Display job description
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
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Generate Resume", type="primary"):
            st.session_state['generate_resume_job_id'] = job['id']
            st.rerun()
    
    with col2:
        if st.button("View Match Details"):
            st.session_state['view_match_job_id'] = job['id']
            st.rerun()
    
    with col3:
        if st.button("Generate Cover Letter"):
            st.info("Cover letter generation coming soon (P1)")
    
    # Check if workflow is active FIRST (before handling generate_resume_job_id)
    # This ensures the workflow continues even after generate_resume_job_id is deleted
    if 'resume_generation_state' in st.session_state and st.session_state.get('resume_generation_job_id') == job['id']:
        # Get job and resume for workflow
        job_obj = db.get_job(job['id'])
        if not job_obj:
            st.error("Job not found.")
            return
        
        job_skills = db.get_job_skills(job['id'])
        if not job_skills:
            st.error("Job skills not found. Please extract skills first.")
            return
        
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
        
        _handle_resume_generation_workflow(db, job['id'], resume, job_skills, matcher, resume_manager, job_obj)
        return  # Exit early to prevent _handle_generate_resume from running
    
    # Handle generate resume action - only if workflow is not already active
    # Keep the key until workflow actually starts (button is clicked)
    if 'generate_resume_job_id' in st.session_state and 'resume_generation_state' not in st.session_state:
        _handle_generate_resume(db, st.session_state['generate_resume_job_id'])
        # Only delete the key if workflow didn't start (button wasn't clicked)
        if 'resume_generation_state' not in st.session_state:
            # Don't delete - keep it so button is rendered on next render
            # The key will be deleted when workflow actually starts
            pass
        else:
            del st.session_state['generate_resume_job_id']
    
    # Handle view match details action
    if 'view_match_job_id' in st.session_state:
        _handle_view_match_details(db, st.session_state['view_match_job_id'])
        del st.session_state['view_match_job_id']


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
        
        # Initialize rewriter
        rewriter = ResumeRewriter()
        
        # Generate proposals
        st.progress(0.5, text="Step 2 of 4: Generating bullet variations with reasoning...")
        with st.spinner("Generating bullet variations with reasoning..."):
            proposals = rewriter.generate_variations(resume, job_match, SkillOntology())
        
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
        
        # Render approval workflow
        result = render_approval_workflow(
            original_bullet,
            reasoning,
            variations,
            bullet_index + 1,
            len(bullet_keys)
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
        # If None, waiting for user input
    
    elif state == 'preview':
        st.header("Final Resume Preview")
        st.progress(0.9, text="Step 4 of 4: Generating PDF preview...")
        st.write("**Review your customized resume before confirming:**")
        
        # Apply approved changes to resume
        updated_resume = resume.model_copy(deep=True)
        approved_bullets = st.session_state.get('approved_bullets', {})
        
        # Apply changes to experience bullets
        bullet_id = 0
        for exp in updated_resume.experience:
            for i, bullet in enumerate(exp.bullets):
                bullet_key = f"exp_{exp.organization}_{bullet_id}"
                if bullet_key in approved_bullets:
                    approved = approved_bullets[bullet_key]
                    exp.bullets[i] = approved
                bullet_id += 1
        
        # Apply changes to project bullets
        bullet_id = 0
        for proj in updated_resume.projects:
            for i, bullet in enumerate(proj.bullets):
                bullet_key = f"proj_{proj.name}_{bullet_id}"
                if bullet_key in approved_bullets:
                    approved = approved_bullets[bullet_key]
                    proj.bullets[i] = approved
                bullet_id += 1
        
        # Show diff view - get original resume from session state if stored
        original_for_diff = resume
        if 'original_resume_for_diff' in st.session_state:
            try:
                import json
                original_for_diff = Resume.model_validate_json(st.session_state['original_resume_for_diff'])
            except:
                pass  # Use current resume if parsing fails
        
        from src.gui.resume_diff import render_resume_diff
        render_resume_diff(original_for_diff, updated_resume, job)
        
        # Generate PDF preview
        try:
            renderer = LaTeXRenderer()
            preview_path = Path("data/resume_preview_temp.pdf")
            preview_path.parent.mkdir(exist_ok=True, parents=True)
            
            with st.spinner("Generating PDF preview..."):
                renderer.render_pdf(updated_resume, preview_path)
            
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

