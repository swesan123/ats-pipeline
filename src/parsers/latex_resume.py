"""LaTeX resume parser with regex-based extraction."""

import re
from pathlib import Path
from typing import List, Optional
from src.models.resume import Resume, ExperienceItem, EducationItem, ProjectItem, Bullet


class LaTeXResumeParser:
    """Parser for LaTeX resume format."""
    
    # Regex patterns (with multiline support)
    # Note: These patterns handle nested braces by matching balanced braces
    RESUME_SUBHEADING = re.compile(r'\\resumeSubheading\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', re.DOTALL)
    RESUME_ITEM = re.compile(r'\\resumeItem\{((?:[^{}]|\{[^{}]*\})*)\}', re.DOTALL)
    RESUME_PROJECT = re.compile(r'\\resumeProjectHeading\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', re.DOTALL)
    SKILL_EXTRACTION = re.compile(r'\\textbf\{([^}]+)\}')
    SECTION_START = re.compile(r'\\section\{([^}]+)\}')
    HEADER_NAME = re.compile(r'\\textbf\{([^}]+)\}')
    HEADER_LINK = re.compile(r'\\href\{([^}]+)\}\{([^}]+)\}')
    GRAYTEXT = re.compile(r'\\graytext\{([^}]+)\}')
    
    def __init__(self, latex_content: str):
        """Initialize parser with LaTeX content."""
        self.latex_content = latex_content
        self.lines = latex_content.split('\n')
    
    @classmethod
    def from_file(cls, file_path: Path) -> 'LaTeXResumeParser':
        """Create parser from LaTeX file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return cls(content)
    
    def parse(self) -> Resume:
        """Parse LaTeX content into Resume model."""
        # Extract header
        name, phone, email, linkedin, github, citizenship = self._parse_header()
        
        # Extract sections
        education = self._parse_education()
        skills = self._parse_skills()
        experience = self._parse_experience()
        projects = self._parse_projects()
        hobbies = self._parse_hobbies()
        courses = self._parse_courses()
        
        return Resume(
            name=name,
            phone=phone,
            email=email,
            linkedin=linkedin,
            github=github,
            citizenship=citizenship,
            education=education,
            skills=skills,
            experience=experience,
            projects=projects,
            hobbies=hobbies,
            courses=courses,
        )
    
    def _parse_header(self) -> tuple[str, Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Parse header section (name, contact info)."""
        name = ""
        phone = None
        email = None
        linkedin = None
        github = None
        citizenship = None
        
        # Find center block
        in_center = False
        center_lines = []
        
        for i, line in enumerate(self.lines):
            if '\\begin{center}' in line:
                in_center = True
                continue
            if '\\end{center}' in line:
                in_center = False
                break
            if in_center:
                center_lines.append(line)
        
        center_text = '\n'.join(center_lines)
        
        # Extract name (first \textbf in center)
        name_match = self.HEADER_NAME.search(center_text)
        if name_match:
            name = name_match.group(1)
        
        # Extract citizenship (graytext)
        citizenship_match = self.GRAYTEXT.search(center_text)
        if citizenship_match:
            citizenship = citizenship_match.group(1)
        
        # Extract phone (pattern: +1-XXX-XXX-XXXX or similar, before $|$)
        phone_match = re.search(r'(\+?[\d\-\(\)\s]+?)(?:\s*\$\\|\$\s*|$)', center_text)
        if phone_match:
            phone = phone_match.group(1).strip()
        
        # Extract all href links
        for link_match in self.HEADER_LINK.finditer(center_text):
            url = link_match.group(1)
            link_text = link_match.group(2)
            
            # Check if it's an email
            if 'mailto:' in url or '@' in url:
                email = url.replace('mailto:', '')
            # Check if it's LinkedIn
            elif 'linkedin' in url.lower() or 'linkedin' in link_text.lower():
                linkedin = url
            # Check if it's GitHub
            elif 'github' in url.lower() or 'github' in link_text.lower():
                github = url
        
        return name, phone, email, linkedin, github, citizenship
    
    def _parse_education(self) -> List[EducationItem]:
        """Parse education section."""
        education_items = []
        
        # Find education section
        section_start = self._find_section_start('Education')
        if section_start == -1:
            return education_items
        
        # Find section end (next section or end of document)
        section_end = self._find_section_end(section_start)
        
        section_text = '\n'.join(self.lines[section_start:section_end])
        
        # Find all resumeSubheading in education section (handle multiline)
        # First normalize whitespace
        section_text = re.sub(r'\s+', ' ', section_text)
        
        for match in self.RESUME_SUBHEADING.finditer(section_text):
            org = match.group(1).strip()
            location = match.group(2).strip()
            degree = match.group(3).strip()
            dates = match.group(4).strip()
            
            # Parse dates
            start_date, end_date = self._parse_date_range(dates)
            
            education_items.append(EducationItem(
                institution=org,
                location=location,
                degree=degree,
                start_date=start_date,
                end_date=end_date,
            ))
        
        return education_items
    
    def _parse_skills(self) -> dict[str, List[str]]:
        """Parse technical skills section."""
        skills_dict = {}
        
        section_start = self._find_section_start('Technical Skills')
        if section_start == -1:
            return skills_dict
        
        section_end = self._find_section_end(section_start)
        section_text = '\n'.join(self.lines[section_start:section_end])
        
        # Find all \textbf{Category}{: skills} patterns
        # Pattern: \textbf{Category}{: skill1, skill2, ...} \\
        # Match balanced braces for the second group
        def find_balanced_braces(text, start_pos):
            """Find the end of a balanced brace group starting at start_pos."""
            if start_pos >= len(text) or text[start_pos] != '{':
                return -1
            depth = 0
            i = start_pos
            for i in range(start_pos, len(text)):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        return i
            return -1
        
        # Find all \textbf{Category} patterns
        for match in re.finditer(r'\\textbf\{([^}]+)\}', section_text):
            category = match.group(1).strip()
            # Find the opening brace after \textbf{Category}
            brace_start = match.end()
            if brace_start < len(section_text) and section_text[brace_start] == '{':
                # Find the closing brace
                brace_end = find_balanced_braces(section_text, brace_start)
                if brace_end > brace_start:
                    skills_text = section_text[brace_start+1:brace_end]
                    # Remove the colon if present
                    skills_text = re.sub(r'^:\s*', '', skills_text)
                    # Remove trailing backslashes
                    skills_text = re.sub(r'\\+$', '', skills_text).strip()
                    # Split by comma
                    skills = [s.strip() for s in re.split(r',', skills_text) if s.strip()]
                    if skills:
                        skills_dict[category] = skills
        
        return skills_dict
    
    def _parse_experience(self) -> List[ExperienceItem]:
        """Parse work experience section."""
        experience_items = []
        
        section_start = self._find_section_start('Work Experience')
        if section_start == -1:
            return experience_items
        
        section_end = self._find_section_end(section_start)
        section_text = '\n'.join(self.lines[section_start:section_end])
        
        # Find all resumeSubheading matches (handles multiline)
        for match in self.RESUME_SUBHEADING.finditer(section_text):
            org = match.group(1).strip()
            location = match.group(2).strip()
            role = match.group(3).strip()
            dates = match.group(4).strip()
            
            start_date, end_date = self._parse_date_range(dates)
            
            # Extract bullets for this experience item
            # Find text after this match until next resumeSubheading or end
            match_end = match.end()
            next_match = section_text.find('\\resumeSubheading', match_end)
            if next_match == -1:
                item_text = section_text[match_end:]
            else:
                item_text = section_text[match_end:next_match]
            
            bullets = self._extract_bullets(item_text)
            
            experience_items.append(ExperienceItem(
                organization=org,
                role=role,
                location=location,
                start_date=start_date,
                end_date=end_date,
                bullets=bullets,
            ))
        
        return experience_items
    
    def _parse_projects(self) -> List[ProjectItem]:
        """Parse projects section."""
        projects = []
        
        section_start = self._find_section_start('Projects')
        if section_start == -1:
            return projects
        
        section_end = self._find_section_end(section_start)
        section_text = '\n'.join(self.lines[section_start:section_end])
        
        # Find all resumeProjectHeading
        for match in self.RESUME_PROJECT.finditer(section_text):
            project_info = match.group(1).strip()
            dates = match.group(2).strip()
            
            # Split project name and tech stack by |
            if '|' in project_info:
                parts = project_info.split('|')
                name = parts[0].strip()
                tech_stack_text = parts[1].strip() if len(parts) > 1 else ""
            else:
                name = project_info
                tech_stack_text = ""
            
            # Clean project name (remove LaTeX formatting)
            name = self._clean_latex(name)
            # Remove $ characters (math mode delimiters)
            name = name.replace('$', '').strip()
            
            # Extract tech stack (remove \textbf markers)
            tech_stack = []
            if tech_stack_text:
                tech_stack = [t.strip() for t in tech_stack_text.split(',') if t.strip()]
                # Clean \textbf markers and $ characters
                tech_stack = [re.sub(r'\\textbf\{([^}]+)\}', r'\1', t) for t in tech_stack]
                tech_stack = [t.replace('$', '').strip() for t in tech_stack if t.replace('$', '').strip()]
            
            start_date, end_date = self._parse_date_range(dates)
            
            # Extract bullets for this project
            # Find the section after this project heading
            project_start = match.end()
            next_project = section_text.find('\\resumeProjectHeading', project_start)
            if next_project == -1:
                project_text = section_text[project_start:]
            else:
                project_text = section_text[project_start:next_project]
            
            bullets = self._extract_bullets(project_text)
            
            projects.append(ProjectItem(
                name=name,
                tech_stack=tech_stack,
                start_date=start_date,
                end_date=end_date,
                bullets=bullets,
            ))
        
        return projects
    
    def _parse_hobbies(self) -> List[str]:
        """Parse hobbies section."""
        # Try both "Hobbies" and "Hobbies \& Interests"
        section_start = self._find_section_start('Hobbies')
        if section_start == -1:
            # Try alternative section name
            pattern = re.compile(r'\\section\{Hobbies.*Interests')
            for i, line in enumerate(self.lines):
                if pattern.search(line):
                    section_start = i
                    break
        if section_start == -1:
            return []
        
        section_end = self._find_section_end(section_start)
        section_text = '\n'.join(self.lines[section_start:section_end])
        
        # Extract text from \item, handling \footnotesize
        item_match = re.search(r'\\item\s*(?:\\footnotesize\s*)?\{?([^}]+)\}?', section_text)
        if item_match:
            hobbies_text = item_match.group(1).strip()
            # Remove LaTeX commands
            hobbies_text = re.sub(r'\\footnotesize\s*', '', hobbies_text)
            # Remove trailing period if present
            hobbies_text = hobbies_text.rstrip('.')
            # Split by comma
            hobbies = [h.strip() for h in hobbies_text.split(',') if h.strip()]
            return hobbies
        
        return []
    
    def _parse_courses(self) -> List[str]:
        """Parse relevant courses section."""
        section_start = self._find_section_start('Relevant Courses')
        if section_start == -1:
            return []
        
        section_end = self._find_section_end(section_start)
        section_text = '\n'.join(self.lines[section_start:section_end])
        
        # Extract text from \item, handling \footnotesize
        item_match = re.search(r'\\item\s*(?:\\footnotesize\s*)?\{?([^}]+)\}?', section_text)
        if item_match:
            courses_text = item_match.group(1).strip()
            # Remove LaTeX commands
            courses_text = re.sub(r'\\footnotesize\s*', '', courses_text)
            courses_text = re.sub(r'\\&', '&', courses_text)
            # Split by comma
            courses = [c.strip() for c in courses_text.split(',') if c.strip()]
            return courses
        
        return []
    
    def _extract_bullets(self, text: str) -> List[Bullet]:
        """Extract bullet points from text."""
        bullets = []
        
        # Find text between resumeItemListStart and resumeItemListEnd
        start_marker = '\\resumeItemListStart'
        end_marker = '\\resumeItemListEnd'
        
        start_idx = text.find(start_marker)
        if start_idx == -1:
            return bullets
        
        end_idx = text.find(end_marker, start_idx)
        if end_idx == -1:
            return bullets
        
        bullet_text = text[start_idx:end_idx]
        
        # Extract all resumeItem
        for match in self.RESUME_ITEM.finditer(bullet_text):
            bullet_content = match.group(1)
            
            # Clean LaTeX commands
            cleaned_text = self._clean_latex(bullet_content)
            
            # Extract skills from \textbf{skill}
            skills = self.SKILL_EXTRACTION.findall(bullet_content)
            
            bullets.append(Bullet(
                text=cleaned_text,
                skills=skills,
            ))
        
        return bullets
    
    def _clean_latex(self, text: str) -> str:
        """Clean LaTeX commands from text."""
        # Remove \textbf{...} but keep content
        text = re.sub(r'\\textbf\{([^}]+)\}', r'\1', text)
        # Convert \% to %
        text = text.replace('\\%', '%')
        # Convert \& to &
        text = text.replace('\\&', '&')
        # Remove other common LaTeX commands (but preserve content)
        text = re.sub(r'\\(footnotesize|small|textit|textsc|textcolor\{[^}]+\})\s*', '', text)
        text = re.sub(r'\\[a-zA-Z]+\{([^}]+)\}', r'\1', text)
        # Clean up whitespace
        text = ' '.join(text.split())
        return text
    
    def _parse_date_range(self, date_str: str) -> tuple[Optional[str], Optional[str]]:
        """Parse date range like 'Sep 2021 -- Apr 2026' or 'May 2024 -- Aug 2025'."""
        date_str = date_str.strip()
        
        if '--' in date_str:
            parts = date_str.split('--')
            start = parts[0].strip() if len(parts) > 0 else None
            end = parts[1].strip() if len(parts) > 1 else None
            return start, end
        elif '–' in date_str:  # En dash
            parts = date_str.split('–')
            start = parts[0].strip() if len(parts) > 0 else None
            end = parts[1].strip() if len(parts) > 1 else None
            return start, end
        else:
            # Single date or "Present"
            if 'Present' in date_str:
                return date_str.replace('Present', '').strip(), 'Present'
            return date_str, None
    
    def _find_section_start(self, section_name: str) -> int:
        """Find the line number where a section starts."""
        pattern = re.compile(r'\\section\{' + re.escape(section_name) + r'\}')
        for i, line in enumerate(self.lines):
            if pattern.search(line):
                return i
        return -1
    
    def _find_section_end(self, section_start: int) -> int:
        """Find the line number where a section ends (next section or end of document)."""
        for i in range(section_start + 1, len(self.lines)):
            if self.SECTION_START.search(self.lines[i]):
                return i
        return len(self.lines)

