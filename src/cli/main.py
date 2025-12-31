"""CLI commands for ATS pipeline."""

import json
import sys
import traceback
from pathlib import Path
from typing import Optional
import click
from src.parsers.latex_resume import LaTeXResumeParser
from src.extractors.job_skills import JobSkillExtractor
from src.matching.skill_matcher import SkillMatcher
from src.compilation.resume_rewriter import ResumeRewriter
from src.approval.interactive_approval import ResumeApprovalWorkflow
from src.rendering.latex_renderer import LaTeXRenderer
from src.models.resume import Resume, ProjectItem
from src.models.job import JobPosting, JobSkills
from src.models.skills import SkillOntology, UserSkills
from src.db.database import Database
from src.projects.project_library import ProjectLibrary
from src.projects.project_selector import ProjectSelector


def _load_job_skills_from_file(job_path: Path) -> tuple[JobSkills, Optional[JobPosting]]:
    """Load job skills from JSON file, handling both old and new formats.
    
    Returns:
        Tuple of (JobSkills, Optional[JobPosting])
    """
    with open(job_path, 'r', encoding='utf-8') as f:
        job_data = json.load(f)
    
    # Handle both formats: old (just job_skills) and new (job_posting + job_skills)
    if 'job_skills' in job_data:
        job_skills = JobSkills.model_validate(job_data['job_skills'])
        job_posting = JobPosting.model_validate(job_data.get('job_posting')) if 'job_posting' in job_data else None
    else:
        # Old format - assume entire file is job_skills
        job_skills = JobSkills.model_validate(job_data)
        job_posting = None
    
    return job_skills, job_posting


def _load_skill_ontology(ontology_path: Optional[str]) -> SkillOntology:
    """Load skill ontology from file or return empty ontology.
    
    Args:
        ontology_path: Optional path to ontology JSON file
        
    Returns:
        SkillOntology instance
    """
    if ontology_path and Path(ontology_path).exists():
        with open(ontology_path, 'r', encoding='utf-8') as f:
            ontology_data = json.load(f)
            return SkillOntology.model_validate(ontology_data)
    return SkillOntology()


def _ensure_data_dir() -> Path:
    """Ensure data directory exists and return its path.
    
    Returns:
        Path to data directory
    """
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return data_dir


@click.group()
def cli():
    """ATS Pipeline CLI - Job application pipeline with skill matching and resume compilation."""
    pass


@cli.command()
@click.argument('input_tex', type=click.Path(exists=True))
def convert_latex(input_tex):
    """Convert LaTeX resume to JSON. Output is saved to data/resume.json"""
    try:
        data_dir = _ensure_data_dir()
        output_json = data_dir / "resume.json"
        
        parser = LaTeXResumeParser.from_file(Path(input_tex))
        resume = parser.parse()
        
        # Validate
        resume.model_validate(resume.model_dump())
        
        # Write JSON
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(resume.model_dump(), f, indent=2, default=str)
        
        click.echo(f"Successfully converted {input_tex} to {output_json}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('job_input')
@click.option('--use-playwright', is_flag=True, help='Force use of Playwright for scraping (handles JavaScript)')
def extract_skills(job_input, use_playwright):
    """Extract skills from job URL or description file. Output is saved to data/job_skills.json"""
    try:
        data_dir = _ensure_data_dir()
        output_json = data_dir / "job_skills.json"
        
        # Check if input is a URL or file path
        is_url = job_input.startswith(('http://', 'https://'))
        
        if is_url:
            # Extract from URL
            from src.extractors.job_url_scraper import JobURLScraper
            
            click.echo(f"Extracting job content from URL: {job_input}")
            scraper = JobURLScraper(use_playwright=use_playwright)
            job_data = scraper.extract_job_content(job_input)
            
            job_posting = JobPosting(
                company=job_data['company'],
                title=job_data['title'],
                location=job_data.get('location'),
                description=job_data['description'],
                source_url=job_data['source_url'],
            )
            
            click.echo(f"  Company: {job_posting.company}")
            click.echo(f"  Title: {job_posting.title}")
            if job_posting.location:
                click.echo(f"  Location: {job_posting.location}")
        else:
            # Read from file (existing behavior)
            job_path = Path(job_input)
            if not job_path.exists():
                click.echo(f"✗ Error: File not found: {job_input}", err=True)
                sys.exit(1)
            
            with open(job_path, 'r', encoding='utf-8') as f:
                description = f.read()
            
            job_posting = JobPosting(
                company="Unknown",
                title="Unknown",
                description=description,
            )
        
        # Extract skills
        click.echo("Extracting skills from job description...")
        extractor = JobSkillExtractor()
        job_skills = extractor.extract_skills(job_posting)
        
        # Save job posting and skills to JSON
        job_output = {
            'job_posting': job_posting.model_dump(),
            'job_skills': job_skills.model_dump()
        }
        
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(job_output, f, indent=2, default=str)
        
        click.echo(f"Successfully extracted skills to {output_json}")
        click.echo(f"  Required: {len(job_skills.required_skills)} skills")
        click.echo(f"  Preferred: {len(job_skills.preferred_skills)} skills")
        click.echo(f"  Soft: {len(job_skills.soft_skills)} skills")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--resume-json', type=click.Path(), default='data/resume.json', help='Resume JSON file (default: data/resume.json)')
@click.option('--job-json', type=click.Path(), default='data/job_skills.json', help='Job skills JSON file (default: data/job_skills.json)')
@click.option('--ontology', type=click.Path(), help='Skill ontology JSON file')
def match_job(resume_json, job_json, ontology):
    """Score job fit and show gap analysis."""
    try:
        resume_path = Path(resume_json)
        if not resume_path.exists():
            click.echo(f"✗ Error: Resume file not found: {resume_path}", err=True)
            click.echo(f"  Run 'ats convert-latex <input.tex>' first to create resume.json", err=True)
            sys.exit(1)
        
        job_path = Path(job_json)
        if not job_path.exists():
            click.echo(f"✗ Error: Job skills file not found: {job_path}", err=True)
            click.echo(f"  Run 'ats extract-skills <job_description.txt>' first", err=True)
            sys.exit(1)
        
        # Load resume
        with open(resume_path, 'r', encoding='utf-8') as f:
            resume = Resume.model_validate_json(f.read())
        
        # Load job skills
        job_skills, _ = _load_job_skills_from_file(job_path)
        
        # Load ontology
        skill_ontology = _load_skill_ontology(ontology)
        
        # Match
        matcher = SkillMatcher(skill_ontology)
        job_match = matcher.match_job(resume, job_skills)
        
        # Display results
        click.echo(f"\n{'='*80}")
        click.echo(f"JOB MATCH ANALYSIS")
        click.echo(f"{'='*80}")
        click.echo(f"\nFit Score: {job_match.fit_score:.1%}")
        click.echo(f"\nMatching Skills ({len(job_match.matching_skills)}):")
        for skill in job_match.matching_skills[:10]:
            click.echo(f"  - {skill}")
        
        if job_match.skill_gaps.get("required_missing"):
            click.echo(f"\nMissing Required Skills ({len(job_match.skill_gaps['required_missing'])}):")
            for skill in job_match.skill_gaps["required_missing"][:10]:
                click.echo(f"  - {skill}")
        
        if job_match.missing_skills:
            click.echo(f"\nSkills Not in Resume ({len(job_match.missing_skills)}):")
            for skill in job_match.missing_skills[:10]:
                click.echo(f"  - {skill}")
        
        click.echo(f"\nRecommendations:")
        for rec in job_match.recommendations:
            click.echo(f"  • {rec}")
        click.echo()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--resume-json', type=click.Path(), default='data/resume.json', help='Resume JSON file (default: data/resume.json)')
@click.option('--job-json', type=click.Path(), default='data/job_skills.json', help='Job skills JSON file (default: data/job_skills.json)')
@click.option('--ontology', type=click.Path(), help='Skill ontology JSON file')
@click.option('--user-skills', type=click.Path(), help='User skills JSON file (prevents skill fabrication)')
@click.option('--reuse-threshold', type=float, default=0.90, help='Minimum fit score to reuse existing resume (default: 0.90)')
@click.option('--similarity-threshold', type=float, default=0.85, help='Minimum job similarity to consider reuse (default: 0.85)')
@click.option('--force-new', is_flag=True, help='Force generation of new resume even if reuse is available')
def rewrite_resume(resume_json, job_json, ontology, user_skills, reuse_threshold, similarity_threshold, force_new):
    """Generate resume rewrite proposals with interactive approval. Output is saved to data/resume_updated.json"""
    try:
        data_dir = _ensure_data_dir()
        output_path = data_dir / "resume_updated.json"
        
        resume_path = Path(resume_json)
        if not resume_path.exists():
            click.echo(f"✗ Error: Resume file not found: {resume_path}", err=True)
            sys.exit(1)
        
        job_path = Path(job_json)
        if not job_path.exists():
            click.echo(f"✗ Error: Job skills file not found: {job_path}", err=True)
            sys.exit(1)
        
        # Load resume
        with open(resume_path, 'r', encoding='utf-8') as f:
            resume = Resume.model_validate_json(f.read())
        
        # Load job skills and posting
        job_skills, job_posting = _load_job_skills_from_file(job_path)
        
        # Load ontology
        skill_ontology = _load_skill_ontology(ontology)
        
        # Load user skills if provided
        user_skills_obj = None
        if user_skills and Path(user_skills).exists():
            with open(user_skills, 'r', encoding='utf-8') as f:
                user_skills_data = json.load(f)
                user_skills_obj = UserSkills.model_validate(user_skills_data)
        
        # Check for reusable resume (if database is available)
        if not force_new:
            try:
                from src.matching.resume_reuse_checker import ResumeReuseChecker
                from src.db.database import Database
                
                db = Database()
                matcher = SkillMatcher(skill_ontology)
                reuse_checker = ResumeReuseChecker(db, matcher)
                
                # Try to find reusable resume (using target_job_id=None for now)
                reusable = reuse_checker.find_reusable_resume(
                    job_skills, 
                    target_job_id=None, 
                    min_fit_score=reuse_threshold,
                    min_similarity=similarity_threshold
                )
                
                if reusable:
                    resume_id, reused_resume, fit_score, similarity = reusable
                    click.echo(f"\n{'='*80}")
                    click.echo(f"REUSABLE RESUME FOUND")
                    click.echo(f"{'='*80}")
                    click.echo(f"Resume ID: {resume_id}")
                    click.echo(f"Fit Score: {fit_score:.1%}")
                    click.echo(f"Job Similarity: {similarity:.1%}")
                    
                    choice = input("\nUse this resume? [y/n]: ").strip().lower()
                    if choice == 'y':
                        # Save using ResumeManager
                        from src.storage.resume_manager import ResumeManager
                        resume_manager = ResumeManager()
                        resume_dir = resume_manager.save_resume(
                            reused_resume,
                            job=job_posting,
                            is_customized=job_posting is not None
                        )
                        # Also save to legacy location
                        with open(output_path, 'w', encoding='utf-8') as f:
                            json.dump(reused_resume.model_dump(), f, indent=2, default=str)
                        click.echo(f"Reused resume saved to organized folder: {resume_dir}")
                        click.echo(f"Also saved to: {output_path}")
                        return
            except Exception as e:
                # If reuse check fails, continue with normal flow
                click.echo(f"Note: Resume reuse check failed, proceeding with new generation: {e}")
        
        # Select relevant projects from library (if available)
        try:
            selector = ProjectSelector()
            library_projects = selector.library.get_all_projects()
            if library_projects:
                click.echo(f"\nFound {len(library_projects)} project(s) in library. Selecting most relevant...")
                selected_projects = selector.select_projects(job_skills, max_projects=4, min_score=0.3)
                if selected_projects:
                    click.echo(f"Selected {len(selected_projects)} project(s) for this job:")
                    for i, project in enumerate(selected_projects, 1):
                        score = selector._score_project(project, job_skills)
                        click.echo(f"  {i}. {project.name} (relevance: {score:.1%})")
                    # Replace resume projects with selected ones
                    resume.projects = selected_projects
                    click.echo()
        except Exception as e:
            # If project selection fails, continue with existing projects
            click.echo(f"Note: Project selection skipped: {e}")
        
        # Match job first
        matcher = SkillMatcher(skill_ontology)
        job_match = matcher.match_job(resume, job_skills)
        
        click.echo(f"Job fit score: {job_match.fit_score:.1%}")
        
        # Show what's missing for debugging
        if job_match.fit_score < 0.5:
            click.echo(f"Missing required skills: {len(job_match.skill_gaps.get('required_missing', []))}")
            click.echo(f"Missing preferred skills: {len(job_match.skill_gaps.get('preferred_missing', []))}")
            click.echo(f"Skills not in resume: {len(job_match.missing_skills)}")
        
        click.echo("Generating resume rewrite proposals...")
        
        # Generate variations (with user skills restriction if provided)
        rewriter = ResumeRewriter(user_skills=user_skills_obj)
        proposals = rewriter.generate_variations(resume, job_match, skill_ontology)
        
        if not proposals:
            click.echo("No bullets need adjustment.")
            if job_match.fit_score < 0.5:
                click.echo("Note: Low fit score detected but no bullets identified for adjustment.")
                click.echo("This may indicate the resume needs more significant changes or new experience sections.")
            return
        
        click.echo(f"Found {len(proposals)} bullets to adjust.")
        
        # Interactive approval
        workflow = ResumeApprovalWorkflow(rewriter)
        updated_resume = workflow.process_resume_rewrite(resume, proposals)
        
        # Save using ResumeManager for organized storage
        from src.storage.resume_manager import ResumeManager
        resume_manager = ResumeManager()
        resume_dir = resume_manager.save_resume(
            updated_resume,
            job=job_posting,
            is_customized=job_posting is not None
        )
        
        # Also save to legacy location for backward compatibility
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(updated_resume.model_dump(), f, indent=2, default=str)
        
        click.echo(f"Updated resume saved to organized folder: {resume_dir}")
        click.echo(f"Also saved to: {output_path}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--resume-json', type=click.Path(), default='data/resume.json', help='Resume JSON file to add projects from')
@click.option('--name', type=str, help='Project name (if not provided, will add all projects from resume)')
def add_project(resume_json, name):
    """Add projects from resume JSON to project library."""
    try:
        # Load resume
        with open(resume_json, 'r', encoding='utf-8') as f:
            resume = Resume.model_validate_json(f.read())
        
        library = ProjectLibrary()
        
        if name:
            # Add specific project by name
            project = None
            for p in resume.projects:
                if p.name == name:
                    project = p
                    break
            if not project:
                click.echo(f"✗ Error: Project '{name}' not found in resume", err=True)
                sys.exit(1)
            library.add_project(project)
            click.echo(f"Added project '{project.name}' to library")
        else:
            # Add all projects from resume
            added_count = 0
            for project in resume.projects:
                library.add_project(project)
                added_count += 1
            click.echo(f"Added {added_count} project(s) to library")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def list_projects():
    """List all projects in the library."""
    try:
        library = ProjectLibrary()
        projects = library.get_all_projects()
        
        if not projects:
            click.echo("No projects in library. Use 'ats add-project' to add projects.")
            return
        
        click.echo(f"\nProjects in library ({len(projects)} total):\n")
        for i, project in enumerate(projects, 1):
            tech_stack_str = ", ".join(project.tech_stack) if project.tech_stack else "No tech stack"
            click.echo(f"{i}. {project.name}")
            click.echo(f"   Tech: {tech_stack_str}")
            click.echo(f"   Bullets: {len(project.bullets)}")
            click.echo()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--name', type=str, required=True, help='Project name to remove')
def remove_project(name):
    """Remove a project from the library."""
    try:
        library = ProjectLibrary()
        if library.remove_project(name):
            click.echo(f"Removed project '{name}' from library")
        else:
            click.echo(f"✗ Error: Project '{name}' not found in library", err=True)
            sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--job-json', type=click.Path(), default='data/job_skills.json', help='Job skills JSON file (default: data/job_skills.json)')
@click.option('--max-projects', type=int, default=4, help='Maximum number of projects to select (default: 4)')
@click.option('--min-score', type=float, default=0.3, help='Minimum relevance score to include (default: 0.3)')
@click.option('--output', type=click.Path(), help='Output JSON file (default: data/selected_projects.json)')
def select_projects(job_json, max_projects, min_score, output):
    """Select most relevant projects for a job posting."""
    try:
        # Load job skills
        job_skills, _ = _load_job_skills_from_file(Path(job_json))
        
        # Select projects
        selector = ProjectSelector()
        selected = selector.select_projects(job_skills, max_projects=max_projects, min_score=min_score)
        
        if not selected:
            click.echo("No projects found matching the job requirements.")
            return
        
        # Output results
        click.echo(f"\nSelected {len(selected)} project(s) for this job:\n")
        for i, project in enumerate(selected, 1):
            score = selector._score_project(project, job_skills)
            click.echo(f"{i}. {project.name} (relevance: {score:.1%})")
            click.echo(f"   Tech: {', '.join(project.tech_stack)}")
        
        # Save to file if requested
        if output:
            output_path = Path(output)
        else:
            output_path = Path("data/selected_projects.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([p.model_dump() for p in selected], f, indent=2, default=str)
        click.echo(f"\nSaved selected projects to {output_path}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('job_url')
@click.option('--resume-json', type=click.Path(), default='data/resume.json', help='Resume JSON file (default: data/resume.json)')
@click.option('--user-skills', type=click.Path(), default='data/user_skills.json', help='User skills JSON file (default: data/user_skills.json)')
@click.option('--skip-match', is_flag=True, help='Skip match-job step (optional)')
@click.option('--use-playwright', is_flag=True, help='Force use of Playwright for scraping')
@click.option('--reuse-threshold', type=float, default=0.90, help='Minimum fit score to reuse existing resume (default: 0.90)')
@click.option('--similarity-threshold', type=float, default=0.85, help='Minimum job similarity to consider reuse (default: 0.85)')
@click.option('--force-new', is_flag=True, help='Force generation of new resume even if reuse is available')
def apply(job_url, resume_json, user_skills, skip_match, use_playwright, reuse_threshold, similarity_threshold, force_new):
    """Run the entire application flow: extract-skills → match-job → rewrite-resume → render-pdf"""
    try:
        data_dir = _ensure_data_dir()
        
        job_skills_path = data_dir / "job_skills.json"
        resume_updated_path = data_dir / "resume_updated.json"
        pdf_path = data_dir / "resume.pdf"
        
        click.echo(f"\n{'='*80}")
        click.echo("ATS PIPELINE - FULL APPLICATION FLOW")
        click.echo(f"{'='*80}\n")
        
        # Step 1: Extract skills
        click.echo("Step 1/4: Extracting skills from job posting...")
        from src.extractors.job_url_scraper import JobURLScraper
        from src.extractors.job_skills import JobSkillExtractor
        
        scraper = JobURLScraper(use_playwright=use_playwright)
        job_data = scraper.extract_job_content(job_url)
        
        job_posting = JobPosting(
            company=job_data['company'],
            title=job_data['title'],
            location=job_data.get('location'),
            description=job_data['description'],
            source_url=job_data['source_url'],
        )
        
        click.echo(f"  Company: {job_posting.company}")
        click.echo(f"  Title: {job_posting.title}")
        
        extractor = JobSkillExtractor()
        job_skills = extractor.extract_skills(job_posting)
        
        job_output = {
            'job_posting': job_posting.model_dump(),
            'job_skills': job_skills.model_dump()
        }
        
        with open(job_skills_path, 'w', encoding='utf-8') as f:
            json.dump(job_output, f, indent=2, default=str)
        
        click.echo(f"Skills extracted to {job_skills_path}")
        click.echo(f"  Required: {len(job_skills.required_skills)} skills")
        click.echo(f"  Preferred: {len(job_skills.preferred_skills)} skills")
        click.echo()
        
        # Step 2: Match job (optional)
        if not skip_match:
            click.echo("Step 2/4: Matching resume to job requirements...")
            resume_path = Path(resume_json)
            if not resume_path.exists():
                click.echo(f"✗ Error: Resume file not found: {resume_path}", err=True)
                sys.exit(1)
            
            with open(resume_path, 'r', encoding='utf-8') as f:
                resume = Resume.model_validate_json(f.read())
            
            skill_ontology = SkillOntology()
            matcher = SkillMatcher(skill_ontology)
            job_match = matcher.match_job(resume, job_skills)
            
            click.echo(f"  Fit Score: {job_match.fit_score:.1%}")
            click.echo(f"  Matching Skills: {len(job_match.matching_skills)}")
            click.echo(f"  Missing Required: {len(job_match.skill_gaps.get('required_missing', []))}")
            click.echo()
        else:
            click.echo("Step 2/4: Skipping match-job (--skip-match)\n")
        
        # Step 3: Rewrite resume
        click.echo("Step 3/4: Rewriting resume with interactive approval...")
        
        # Load user skills if provided
        user_skills_obj = None
        if user_skills and Path(user_skills).exists():
            with open(user_skills, 'r', encoding='utf-8') as f:
                user_skills_data = json.load(f)
                user_skills_obj = UserSkills.model_validate(user_skills_data)
                click.echo(f"  Using {len(user_skills_obj.skills)} user-provided skills (prevents fabrication)")
        elif user_skills:
            click.echo(f"  Warning: User skills file not found: {user_skills}", err=True)
        
        # Call rewrite_resume logic (reuse existing function)
        resume_path = Path(resume_json)
        if not resume_path.exists():
            click.echo(f"✗ Error: Resume file not found: {resume_path}", err=True)
            sys.exit(1)
        
        with open(resume_path, 'r', encoding='utf-8') as f:
            resume = Resume.model_validate_json(f.read())
        
        skill_ontology = SkillOntology()
        
        # Select relevant projects from library
        try:
            selector = ProjectSelector()
            library_projects = selector.library.get_all_projects()
            if library_projects:
                click.echo(f"  Found {len(library_projects)} project(s) in library. Selecting most relevant...")
                selected_projects = selector.select_projects(job_skills, max_projects=4, min_score=0.3)
                if selected_projects:
                    click.echo(f"  Selected {len(selected_projects)} project(s) for this job")
                    resume.projects = selected_projects
        except Exception as e:
            click.echo(f"  Note: Project selection skipped: {e}")
        
        # Match job
        matcher = SkillMatcher(skill_ontology)
        job_match = matcher.match_job(resume, job_skills)
        
        click.echo(f"  Job fit score: {job_match.fit_score:.1%}")
        
        # Generate variations
        rewriter = ResumeRewriter(user_skills=user_skills_obj)
        proposals = rewriter.generate_variations(resume, job_match, skill_ontology)
        
        if not proposals:
            click.echo("  No bullets need adjustment.")
        else:
            click.echo(f"  Found {len(proposals)} bullets to adjust.")
            workflow = ResumeApprovalWorkflow(rewriter)
            resume = workflow.process_resume_rewrite(resume, proposals)
        
        # Save updated resume using ResumeManager
        from src.storage.resume_manager import ResumeManager
        resume_manager = ResumeManager()
        resume_dir = resume_manager.save_resume(
            resume,
            job=job_posting,
            is_customized=True
        )
        
        # Also save to legacy location
        with open(resume_updated_path, 'w', encoding='utf-8') as f:
            json.dump(resume.model_dump(), f, indent=2, default=str)
        
        click.echo(f"Updated resume saved to organized folder: {resume_dir}")
        click.echo(f"Also saved to: {resume_updated_path}")
        click.echo()
        
        # Step 4: Render PDF
        click.echo("Step 4/4: Rendering PDF...")
        renderer = LaTeXRenderer()
        pdf_path = renderer.render_pdf(resume, pdf_path)
        
        click.echo(f"PDF generated: {pdf_path}")
        click.echo()
        click.echo(f"{'='*80}")
        click.echo("APPLICATION FLOW COMPLETE")
        click.echo(f"{'='*80}")
        click.echo(f"\nOutput files:")
        click.echo(f"  - Job skills: {job_skills_path}")
        click.echo(f"  - Updated resume: {resume_updated_path}")
        click.echo(f"  - PDF: {pdf_path}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--credentials', type=click.Path(exists=True), required=True, help='Path to Google service account JSON credentials')
@click.option('--spreadsheet-id', required=True, help='Google Sheets spreadsheet ID')
@click.option('--sheet-name', default='Sheet1', help='Sheet name to sync from (default: Sheet1)')
@click.option('--dry-run', is_flag=True, help='Show what would be synced without making changes')
def sync_sheet(credentials, spreadsheet_id, sheet_name, dry_run):
    """Sync jobs from Google Sheets to database."""
    try:
        from src.sync.google_sheets_client import GoogleSheetsClient
        from src.sync.sheet_sync import SheetSyncService
        from src.db.database import Database
        
        click.echo(f"\n{'='*80}")
        click.echo("GOOGLE SHEETS SYNC")
        click.echo(f"{'='*80}\n")
        
        if dry_run:
            click.echo("DRY RUN MODE - No changes will be made\n")
        
        # Initialize client
        click.echo("Connecting to Google Sheets...")
        client = GoogleSheetsClient(credentials, spreadsheet_id)
        click.echo(f"Connected to spreadsheet: {spreadsheet_id}")
        click.echo(f"Reading sheet: {sheet_name}\n")
        
        # Initialize sync service
        db = Database()
        sync_service = SheetSyncService(db, client)
        
        # Perform sync
        click.echo("Finding sheet with required columns...")
        if sheet_name:
            click.echo(f"Using specified sheet: {sheet_name}")
        else:
            click.echo("Auto-detecting sheet...")
        
        click.echo("Syncing jobs...")
        stats = sync_service.sync_from_sheet(sheet_name, dry_run=dry_run)
        
        click.echo(f"\n{'='*80}")
        click.echo("SYNC COMPLETE")
        click.echo(f"{'='*80}")
        click.echo(f"Sheet used: {stats.get('sheet_name', 'Unknown')}")
        click.echo(f"Jobs added: {stats['added']}")
        click.echo(f"Jobs updated: {stats['updated']}")
        click.echo(f"Errors: {stats['errors']}")
        
        if dry_run:
            click.echo("\nThis was a dry run. Run without --dry-run to apply changes.")
        
    except ImportError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("\nInstall required packages: pip install gspread google-auth", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--resume-json', type=click.Path(), default='data/resume_updated.json', help='Resume JSON file (default: data/resume_updated.json)')
def render_pdf(resume_json):
    """Generate PDF from JSON resume. Output is saved to data/resume.pdf"""
    try:
        data_dir = _ensure_data_dir()
        output_path = data_dir / "resume.pdf"
        
        resume_path = Path(resume_json)
        if not resume_path.exists():
            click.echo(f"✗ Error: Resume file not found: {resume_path}", err=True)
            sys.exit(1)
        
        # Load resume
        with open(resume_path, 'r', encoding='utf-8') as f:
            resume = Resume.model_validate_json(f.read())
        
        # Render PDF
        renderer = LaTeXRenderer()
        pdf_path = renderer.render_pdf(resume, output_path)
        
        click.echo(f"Successfully generated PDF: {pdf_path}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def deduplicate_jobs():
    """Remove duplicate jobs from database, keeping the most recent one for each company+title combination."""
    try:
        db = Database()
        stats = db.deduplicate_jobs()
        click.echo(f"Deduplication complete!")
        click.echo(f"- Removed: {stats['removed']} duplicate jobs")
        click.echo(f"- Kept: {stats['kept']} unique jobs")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        traceback.print_exc()
        sys.exit(1)


def main():
    """Entry point for CLI (backward compatibility)."""
    cli()


if __name__ == '__main__':
    cli()

