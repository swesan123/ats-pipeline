"""LaTeX renderer for converting Resume JSON to LaTeX and PDF."""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from src.models.resume import Resume


class LaTeXRenderer:
    """Render Resume JSON to LaTeX and compile to PDF."""
    
    def __init__(self, template_path: Optional[Path] = None):
        """Initialize renderer with LaTeX template."""
        if template_path is None:
            template_path = Path(__file__).parent.parent.parent / "templates" / "resume.tex"
        self.template_path = Path(template_path)
        self._load_template()
    
    def _load_template(self) -> None:
        """Load LaTeX template."""
        with open(self.template_path, 'r', encoding='utf-8') as f:
            self.template_content = f.read()
    
    def render(self, resume: Resume) -> str:
        """Render Resume to LaTeX source."""
        # Build LaTeX content by replacing sections
        latex_output = self.template_content
        
        # Replace header
        header = self._build_header(resume)
        # Find and replace header section
        import re
        # In raw strings, \\ becomes a single \ in the regex pattern, which matches \ in the template
        header_pattern = r'%----------HEADING----------.*?\\end\{center\}'
        # Use lambda to avoid escape sequence interpretation in replacement string
        latex_output = re.sub(header_pattern, lambda m: header, latex_output, flags=re.DOTALL)
        
        # Replace education
        education = self._build_education(resume)
        edu_pattern = r'%-----------EDUCATION-----------.*?\\resumeSubHeadingListEnd'
        latex_output = re.sub(edu_pattern, lambda m: education, latex_output, flags=re.DOTALL)
        
        # Replace skills
        skills = self._build_skills(resume)
        skills_pattern = r'%-----------TECHNICAL SKILLS-----------.*?\\end\{itemize\}'
        latex_output = re.sub(skills_pattern, lambda m: skills, latex_output, flags=re.DOTALL)
        
        # Replace experience
        experience = self._build_experience(resume)
        exp_pattern = r'%-----------WORK EXPERIENCE-----------.*?\\resumeSubHeadingListEnd'
        latex_output = re.sub(exp_pattern, lambda m: experience, latex_output, flags=re.DOTALL)
        
        # Replace projects
        projects = self._build_projects(resume)
        proj_pattern = r'%-----------PROJECTS-----------.*?\\resumeSubHeadingListEnd'
        latex_output = re.sub(proj_pattern, lambda m: projects, latex_output, flags=re.DOTALL)
        
        # Replace hobbies
        hobbies = self._build_hobbies(resume)
        hobbies_pattern = r'%-----------HOBBIES-----------.*?\\resumeSubHeadingListEnd'
        latex_output = re.sub(hobbies_pattern, lambda m: hobbies, latex_output, flags=re.DOTALL)
        
        # Replace courses
        courses = self._build_courses(resume)
        courses_pattern = r'%-----------COURSES-----------.*?\\resumeSubHeadingListEnd'
        latex_output = re.sub(courses_pattern, lambda m: courses, latex_output, flags=re.DOTALL)
        
        return latex_output
    
    def _build_header(self, resume: Resume) -> str:
        """Build header section."""
        lines = ["%----------HEADING----------", "\\begin{center}"]
        lines.append(f"  {{\\fontsize{{20pt}}{{20pt}}\\selectfont \\textbf{{{resume.name}}}}} \\\\[-2pt]")
        if resume.citizenship:
            lines.append(f"  {{\\graytext{{{resume.citizenship}}}}} \\\\[2pt]")
        
        contact_parts = []
        if resume.phone:
            contact_parts.append(resume.phone)
        if resume.email:
            contact_parts.append(f"\\href{{mailto:{resume.email}}}{{\\underline{{{resume.email}}}}}")
        if resume.linkedin:
            linkedin_display = resume.linkedin.replace("https://", "").replace("http://", "")
            contact_parts.append(f"\\href{{{resume.linkedin}}}{{\\underline{{{linkedin_display}}}}}")
        if resume.github:
            github_display = resume.github.replace("https://", "").replace("http://", "")
            contact_parts.append(f"\\href{{{resume.github}}}{{\\underline{{{github_display}}}}}")
        
        if contact_parts:
            lines.append(f"  \\small {' $|$ '.join(contact_parts)}")
        lines.append("\\end{center}")
        return "\n".join(lines)
    
    def _build_education(self, resume: Resume) -> str:
        """Build education section."""
        lines = ["%-----------EDUCATION-----------", "\\section{Education}", "\\resumeSubHeadingListStart"]
        for edu in resume.education:
            lines.append("  \\resumeSubheading")
            lines.append(f"    {{{edu.institution}}}{{{edu.location}}}")
            lines.append(f"    {{{edu.degree}}}{{{self._format_dates(edu.start_date, edu.end_date)}}}")
        lines.append("\\resumeSubHeadingListEnd")
        return "\n".join(lines)
    
    def _build_skills(self, resume: Resume) -> str:
        """Build skills section."""
        lines = ["%-----------TECHNICAL SKILLS-----------", "\\section{Technical Skills}"]
        lines.append("\\begin{itemize}[leftmargin=0.15in, label={}]")
        lines.append("  \\small{\\item{")
        
        skill_lines = []
        for category, skills in resume.skills.items():
            skills_str = ", ".join(skills)
            skill_lines.append(f"    \\textbf{{{category}}}{{: {skills_str}}} \\\\")
        
        lines.extend(skill_lines)
        lines.append("  }}")
        lines.append("\\end{itemize}")
        return "\n".join(lines)
    
    def _build_experience(self, resume: Resume) -> str:
        """Build experience section."""
        lines = ["%-----------WORK EXPERIENCE-----------", "\\section{Work Experience}", "\\resumeSubHeadingListStart", ""]
        for exp in resume.experience:
            lines.append("  \\resumeSubheading")
            lines.append(f"    {{{exp.organization}}}{{{exp.location}}}")
            lines.append(f"    {{{exp.role}}}{{{self._format_dates(exp.start_date, exp.end_date)}}}")
            lines.append("    \\resumeItemListStart")
            for bullet in exp.bullets:
                bullet_text = bullet.text
                # Highlight skills BEFORE escaping LaTeX (so \textbf doesn't get escaped)
                for skill in bullet.skills:
                    bullet_text = bullet_text.replace(skill, f"\\textbf{{{skill}}}")
                # Now escape LaTeX special characters
                bullet_text = self._escape_latex(bullet_text)
                lines.append(f"      \\resumeItem{{{bullet_text}}}")
            lines.append("    \\resumeItemListEnd")
            lines.append("")
        lines.append("\\resumeSubHeadingListEnd")
        return "\n".join(lines)
    
    def _build_projects(self, resume: Resume) -> str:
        """Build projects section."""
        lines = ["%-----------PROJECTS-----------", "\\section{Projects}", "\\resumeSubHeadingListStart", ""]
        for proj in resume.projects:
            # Escape project name and tech stack (but not the braces we'll add)
            proj_name_escaped = self._escape_latex(proj.name)
            tech_stack_str = ", ".join(proj.tech_stack)
            tech_stack_escaped = self._escape_latex(tech_stack_str)
            
            lines.append("%--- " + proj.name + " ---")
            lines.append("  \\resumeProjectHeading")
            # Use $|$ format like the template (math mode for pipe character)
            # Don't escape the $ characters here - they're part of the LaTeX math mode syntax
            lines.append(f"    {{\\textbf{{{proj_name_escaped}}} $|$ \\textbf{{{tech_stack_escaped}}}}}{{{self._format_dates(proj.start_date, proj.end_date)}}}")
            lines.append("    \\resumeItemListStart")
            for bullet in proj.bullets:
                bullet_text = bullet.text
                # Highlight skills BEFORE escaping LaTeX (so \textbf doesn't get escaped)
                for skill in bullet.skills:
                    bullet_text = bullet_text.replace(skill, f"\\textbf{{{skill}}}")
                # Now escape LaTeX special characters
                bullet_text = self._escape_latex(bullet_text)
                lines.append(f"      \\resumeItem{{{bullet_text}}}")
            lines.append("    \\resumeItemListEnd")
            lines.append("")
        lines.append("\\resumeSubHeadingListEnd")
        return "\n".join(lines)
    
    def _build_hobbies(self, resume: Resume) -> str:
        """Build hobbies section."""
        lines = ["%-----------HOBBIES-----------", "\\section{Hobbies \\& Interests}", "\\resumeSubHeadingListStart"]
        if resume.hobbies:
            hobbies_str = ", ".join(resume.hobbies)
            # Escape LaTeX special characters in hobbies string
            hobbies_str = self._escape_latex(hobbies_str)
            lines.append(f"  \\item {{\\footnotesize {hobbies_str}.}}")
        lines.append("\\resumeSubHeadingListEnd")
        return "\n".join(lines)
    
    def _build_courses(self, resume: Resume) -> str:
        """Build courses section."""
        lines = ["%-----------COURSES-----------", "\\section{Relevant Courses}", "\\resumeSubHeadingListStart"]
        if resume.courses:
            courses_str = ", ".join(resume.courses)
            # Escape LaTeX special characters in courses string
            courses_str = self._escape_latex(courses_str)
            lines.append(f"  \\item {{\\footnotesize {courses_str}}}")
        lines.append("\\resumeSubHeadingListEnd")
        return "\n".join(lines)
    
    def _format_dates(self, start: Optional[str], end: Optional[str]) -> str:
        """Format date range for LaTeX."""
        if start and end:
            return f"{start} -- {end}"
        elif start:
            return start
        elif end:
            return end
        return ""
    
    def _escape_latex(self, text: str) -> str:
        """Escape LaTeX special characters.
        
        Note: This should be called AFTER adding LaTeX commands like \textbf{},
        so that LaTeX commands are preserved.
        """
        import re
        # Protect LaTeX commands (like \textbf{...}) by replacing them with placeholders
        # Use placeholders without special characters that need escaping
        placeholders = []
        def protect_latex_command(match):
            cmd = match.group(0)
            placeholders.append(cmd)
            return f"LATEXCMDPH{len(placeholders)-1}PH"
        
        # Match LaTeX commands: \command{content}
        text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', protect_latex_command, text)
        
        # Escape LaTeX special characters (order matters - escape % before backslash)
        # First escape characters that create backslash sequences
        replacements_before_backslash = {
            '&': '\\&',
            '%': '\\%',
            '$': '\\$',
            '#': '\\#',
            '^': '\\textasciicircum{}',
            '_': '\\_',
            '{': '\\{',
            '}': '\\}',
            '~': '\\textasciitilde{}',
        }
        for char, replacement in replacements_before_backslash.items():
            text = text.replace(char, replacement)
        
        # Now escape standalone backslashes (not part of LaTeX escape sequences)
        # A backslash followed by a letter is a LaTeX command (already protected)
        # A backslash followed by %, &, $, etc. is an escape sequence (already done)
        # Only escape backslashes that aren't part of these patterns
        def escape_standalone_backslash(match):
            pos = match.start()
            # Check what follows the backslash
            if pos + 1 < len(text):
                next_char = text[pos + 1]
                # If it's a letter, it's a LaTeX command (shouldn't happen due to protection)
                # If it's %, &, $, etc., it's an escape sequence (already escaped)
                # If it's something else, escape it
                if next_char in '%&$#^_{}~':
                    return match.group(0)  # Already part of escape sequence
                elif next_char.isalpha():
                    return match.group(0)  # Part of LaTeX command (shouldn't happen)
                else:
                    return '\\textbackslash{}'  # Standalone backslash
            else:
                return '\\textbackslash{}'  # Backslash at end
        
        text = re.sub(r'\\(?![a-zA-Z%&$#^_{}~])', escape_standalone_backslash, text)
        
        # Restore LaTeX commands
        for i, cmd in enumerate(placeholders):
            text = text.replace(f"LATEXCMDPH{i}PH", cmd)
        
        return text
    
    def render_pdf(self, resume: Resume, output_path: Optional[Path] = None) -> Path:
        """Render Resume to PDF.
        
        Returns: Path to generated PDF.
        """
        if output_path is None:
            output_path = Path("resume.pdf")
        
        output_path = Path(output_path)
        
        # Generate LaTeX
        latex_content = self.render(resume)
        
        # Write to temporary file
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            tex_file = tmpdir_path / "resume.tex"
            
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            # Compile to PDF
            try:
                result1 = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(tmpdir_path), str(tex_file)],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                
                # Check if PDF was generated (pdflatex may return non-zero for warnings but still generate PDF)
                pdf_file = tmpdir_path / "resume.pdf"
                
                if not pdf_file.exists() and result1.returncode != 0:
                    error_msg = result1.stderr or result1.stdout or "Unknown error"
                    raise RuntimeError(f"PDF compilation failed (first pass):\n{error_msg}")
                
                # Run again for references
                result2 = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(tmpdir_path), str(tex_file)],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                
                # Check if PDF exists (warnings are OK if PDF was generated)
                if pdf_file.exists():
                    import shutil
                    shutil.copy(pdf_file, output_path)
                    return output_path
                else:
                    # PDF not generated - check for actual errors
                    error_msg = result2.stderr or result2.stdout or result1.stderr or result1.stdout or "Unknown error"
                    # Check log file for fatal errors
                    log_file = tmpdir_path / "resume.log"
                    error_details = ""
                    if log_file.exists():
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            log_content = f.read()
                            # Extract fatal error lines (not just warnings)
                            fatal_errors = [line for line in log_content.split('\n') if 'Fatal' in line or ('Error' in line and '!' in line)]
                            if fatal_errors:
                                error_details = "\n".join(fatal_errors[-10:])  # Last 10 fatal errors
                    if error_details:
                        raise RuntimeError(f"PDF compilation failed:\n{error_details}")
                    else:
                        raise RuntimeError(f"PDF compilation failed - output file not found.\n{error_msg}")
            
            except RuntimeError:
                raise
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else e.stdout.decode('utf-8', errors='ignore') if e.stdout else "Unknown error"
                raise RuntimeError(f"PDF compilation failed: {error_msg}")
            except FileNotFoundError:
                raise RuntimeError("pdflatex not found. Please install LaTeX distribution.")

