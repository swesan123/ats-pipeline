"""Parser for extracting information from README.md files."""

import re
from typing import Any, Dict, List, Optional


class ReadmeParser:
    """Parse README.md to extract project information."""
    
    
    def parse(self, readme_content: str) -> Dict[str, Any]:
        """Parse README content to extract project information.
        
        Args:
            readme_content: Raw markdown content of README
            
        Returns:
            Dictionary with:
            - description: Project description (first paragraph or description section)
            - bullets: List of bullet point strings
            - tech_mentions: List of technology names mentioned in README
        """
        if not readme_content:
            return {
                "description": None,
                "bullets": [],
                "tech_mentions": []
            }
        
        # Extract description
        description = self._extract_description(readme_content)
        
        # Extract bullets
        bullets = self._extract_bullets(readme_content)
        
        # Extract tech stack mentions
        tech_mentions = self._extract_tech_mentions(readme_content)
        
        return {
            "description": description,
            "bullets": bullets,
            "tech_mentions": tech_mentions
        }
    
    def _extract_description(self, content: str) -> Optional[str]:
        """Extract project description from README.
        
        Looks for:
        1. Description section (## Description, # Description, etc.)
        2. First paragraph after title
        3. First paragraph in general
        """
        lines = content.split('\n')
        
        # Try to find description section
        desc_section = self._find_section(content, ["description", "about", "overview", "intro"])
        if desc_section:
            # Get first paragraph from description section
            paragraphs = [p.strip() for p in desc_section.split('\n\n') if p.strip()]
            for para in paragraphs:
                # Skip headers, code blocks, lists
                if not para.startswith('#') and not para.startswith('```') and not para.startswith('-') and not para.startswith('*'):
                    cleaned = self._clean_markdown(para)
                    if len(cleaned) > 20:  # Minimum length for meaningful description
                        return cleaned[:500]  # Limit length
        
        # Fallback: Get first substantial paragraph
        for line in lines:
            line = line.strip()
            # Skip empty lines, headers, code blocks, lists
            if (line and 
                not line.startswith('#') and 
                not line.startswith('```') and 
                not line.startswith('-') and 
                not line.startswith('*') and
                not line.startswith('[') and
                len(line) > 20):
                cleaned = self._clean_markdown(line)
                if len(cleaned) > 20:
                    return cleaned[:500]
        
        return None
    
    def _extract_bullets(self, content: str) -> List[str]:
        """Extract bullet points from README.
        
        Looks for bullet lists in sections like:
        - Features
        - Highlights
        - Key Features
        - What it does
        - Capabilities
        """
        bullets = []
        
        # Find relevant sections
        sections = ["features", "highlights", "key features", "what it does", 
                   "capabilities", "functionality", "key points"]
        
        for section_name in sections:
            section_content = self._find_section(content, [section_name])
            if section_content:
                section_bullets = self._extract_bullets_from_text(section_content)
                bullets.extend(section_bullets)
        
        # If no bullets found in specific sections, try to find any substantial bullet list
        if not bullets:
            # Look for bullet lists with at least 3 items
            all_bullets = self._extract_bullets_from_text(content)
            if len(all_bullets) >= 3:
                bullets = all_bullets[:10]  # Limit to 10 bullets
        
        # Clean and filter bullets
        cleaned_bullets = []
        for bullet in bullets:
            cleaned = self._clean_bullet(bullet)
            if cleaned and len(cleaned) > 10:  # Minimum meaningful length
                cleaned_bullets.append(cleaned)
        
        return cleaned_bullets[:10]  # Return max 10 bullets
    
    def _extract_bullets_from_text(self, text: str) -> List[str]:
        """Extract bullet points from text."""
        bullets = []
        lines = text.split('\n')
        
        in_list = False
        current_bullet = []
        
        for line in lines:
            stripped = line.strip()
            
            # Detect bullet point (markdown list item)
            if re.match(r'^[-*+]\s+', stripped) or re.match(r'^\d+\.\s+', stripped):
                # Save previous bullet if exists
                if current_bullet:
                    bullets.append(' '.join(current_bullet))
                    current_bullet = []
                
                # Start new bullet
                bullet_text = re.sub(r'^[-*+]\s+', '', stripped)
                bullet_text = re.sub(r'^\d+\.\s+', '', bullet_text)
                current_bullet.append(bullet_text)
                in_list = True
            elif in_list and (stripped.startswith('  ') or stripped.startswith('\t')):
                # Continuation of bullet (indented)
                current_bullet.append(stripped)
            elif in_list:
                # End of list
                if current_bullet:
                    bullets.append(' '.join(current_bullet))
                    current_bullet = []
                in_list = False
        
        # Add last bullet if exists
        if current_bullet:
            bullets.append(' '.join(current_bullet))
        
        return bullets
    
    def _extract_tech_mentions(self, content: str) -> List[str]:
        """Extract technology mentions from README.
        
        Looks for:
        - Tech stack sections
        - Built with sections
        - Technology lists
        - Common tech names in text
        """
        tech_mentions = set()
        
        # Common technology names to look for
        common_techs = [
            # Languages
            "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust",
            "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB",
            # Frameworks
            "React", "Vue", "Angular", "Django", "Flask", "FastAPI", "Express",
            "Spring", "Laravel", "Rails", "Next.js", "Nuxt", "Svelte",
            # Libraries
            "TensorFlow", "PyTorch", "scikit-learn", "pandas", "numpy",
            "Node.js", "jQuery", "Bootstrap", "Tailwind",
            # Databases
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Cassandra",
            # Tools
            "Docker", "Kubernetes", "Git", "AWS", "Azure", "GCP", "Heroku",
            "Jenkins", "GitHub Actions", "CI/CD", "Terraform", "Ansible"
        ]
        
        # Look for tech stack section
        tech_section = self._find_section(content, ["tech stack", "technologies", "built with", 
                                                    "tools", "stack", "tech", "technologies used"])
        search_text = tech_section if tech_section else content
        
        # Find mentions of common technologies
        content_lower = search_text.lower()
        for tech in common_techs:
            # Case-insensitive search with word boundaries
            pattern = r'\b' + re.escape(tech.lower()) + r'\b'
            if re.search(pattern, content_lower, re.IGNORECASE):
                tech_mentions.add(tech)
        
        # Also look for badge-style mentions (e.g., ![Python](...))
        badge_pattern = r'!\[([^\]]+)\]'
        badges = re.findall(badge_pattern, content)
        for badge in badges:
            # Check if badge text contains tech name
            for tech in common_techs:
                if tech.lower() in badge.lower():
                    tech_mentions.add(tech)
        
        return sorted(list(tech_mentions))
    
    def _find_section(self, content: str, section_names: List[str]) -> Optional[str]:
        """Find a section in markdown by header name.
        
        Args:
            content: Markdown content
            section_names: List of possible section names to search for
            
        Returns:
            Section content (text between this header and next header), or None
        """
        lines = content.split('\n')
        in_section = False
        section_lines = []
        section_level = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Check if this is a header
            header_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
            if header_match:
                level = len(header_match.group(1))
                header_text = header_match.group(2).lower()
                
                # Check if this is one of our target sections
                if any(name.lower() in header_text for name in section_names):
                    in_section = True
                    section_level = level
                    section_lines = []
                    continue
                
                # If we're in a section and hit another header at same or higher level, stop
                if in_section and level <= section_level:
                    break
            
            # Collect lines if in section
            if in_section:
                section_lines.append(line)
        
        if section_lines:
            return '\n'.join(section_lines)
        return None
    
    def _clean_markdown(self, text: str) -> str:
        """Remove markdown formatting from text."""
        # Remove links but keep text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # Remove images
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)
        # Remove inline code
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # Remove bold/italic
        text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^\*]+)\*', r'\1', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text.strip()
    
    def _clean_bullet(self, bullet: str) -> str:
        """Clean a bullet point string."""
        # Remove markdown formatting
        cleaned = self._clean_markdown(bullet)
        # Remove leading/trailing punctuation
        cleaned = cleaned.strip('.,;:')
        return cleaned
