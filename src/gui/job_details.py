"""Job details component for displaying job information."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Dict, List
import streamlit as st
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
    
    st.write(f"**Company:** {job['company']}")
    st.write(f"**Title:** {job['title']}")
    if job.get('location'):
        st.write(f"**Location:** {job['location']}")
    
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
    
    # Handle generate resume action
    if 'generate_resume_job_id' in st.session_state:
        _handle_generate_resume(db, st.session_state['generate_resume_job_id'])
        del st.session_state['generate_resume_job_id']
    
    # Handle view match details action
    if 'view_match_job_id' in st.session_state:
        _handle_view_match_details(db, st.session_state['view_match_job_id'])
        del st.session_state['view_match_job_id']


def _handle_generate_resume(db: Database, job_id: int):
    """Handle resume generation workflow."""
    from src.matching.resume_reuse_checker import ResumeReuseChecker
    
    # Get job and skills
    job = db.get_job(job_id)
    if not job:
        st.error("Job not found.")
        return
    
    job_skills = db.get_job_skills(job_id)
    if not job_skills:
        st.error("Job skills not found. Please extract skills first.")
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
                st.session_state['selected_resume_id'] = resume_id
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
        st.info("Resume rewrite workflow would start here...")
        
        # Show match details
        with st.expander("View Match Details", expanded=True):
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
                st.write("**Recommendations:**")
                for rec in job_match.recommendations:
                    st.write(f"- {rec}")


def _handle_view_match_details(db: Database, job_id: int):
    """Handle view match details workflow."""
    # Get job and skills
    job = db.get_job(job_id)
    if not job:
        st.error("Job not found.")
        return
    
    job_skills = db.get_job_skills(job_id)
    if not job_skills:
        st.error("Job skills not found. Please extract skills first.")
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

