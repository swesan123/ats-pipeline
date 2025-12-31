"""Extract project information from GitHub repositories."""

from typing import Optional, List
from src.extractors.github_api import GitHubAPIClient
from src.extractors.readme_parser import ReadmeParser
from src.extractors.dependency_parser import DependencyParser
from src.extractors.bullet_formatter import BulletFormatter
from src.models.resume import ProjectItem, Bullet


class GitHubRepoExtractor:
    """Extract project information from GitHub repository URLs."""
    
    # Common dependency file paths to check
    DEPENDENCY_FILES = [
        "package.json",
        "requirements.txt",
        "pyproject.toml",
        "pom.xml",
        "build.gradle",
        "Cargo.toml",
        "go.mod",
        "setup.py",
    ]
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize GitHub repository extractor.
        
        Args:
            github_token: GitHub personal access token (optional)
        """
        self.api_client = GitHubAPIClient(token=github_token)
        self.readme_parser = ReadmeParser()
        self.dependency_parser = DependencyParser()
        try:
            self.bullet_formatter = BulletFormatter()
        except ValueError:
            # If OpenAI API key not available, bullet formatter will be None
            self.bullet_formatter = None
    
    def extract_project(self, repo_url: str) -> ProjectItem:
        """Extract project information from GitHub repository URL.
        
        Args:
            repo_url: GitHub repository URL (e.g., https://github.com/owner/repo)
            
        Returns:
            ProjectItem with extracted information
            
        Raises:
            ValueError: If URL is invalid
            requests.HTTPError: If API request fails
        """
        # Parse URL
        owner, repo = self.api_client.parse_github_url(repo_url)
        
        # Fetch repository metadata
        repo_data = self.api_client.get_repository(owner, repo)
        repo_name = repo_data.get("name", repo)
        created_at = repo_data.get("created_at")
        start_date = self.api_client.format_creation_date(created_at) if created_at else None
        
        # Fetch README
        readme_content = self.api_client.get_readme(owner, repo)
        readme_info = self.readme_parser.parse(readme_content) if readme_content else {}
        
        # Fetch languages from GitHub API
        languages = self.api_client.get_languages(owner, repo)
        language_techs = list(languages.keys()) if languages else []
        
        # Fetch and parse dependency files
        dependency_techs = []
        for dep_file in self.DEPENDENCY_FILES:
            dep_content = self.api_client.get_file_content(owner, repo, dep_file)
            if dep_content:
                techs = self.dependency_parser.parse(dep_file, dep_content)
                dependency_techs.extend(techs)
        
        # Merge tech stack from all sources
        tech_stack = self._merge_tech_stack(
            readme_info.get("tech_mentions", []),
            language_techs,
            dependency_techs
        )
        
        # Extract bullets from README
        raw_bullets = readme_info.get("bullets", [])
        
        # If no bullets found, create one from description
        if not raw_bullets and readme_info.get("description"):
            raw_bullets = [readme_info["description"]]
        
        # Format bullets using AI if formatter is available
        if self.bullet_formatter and raw_bullets:
            try:
                formatted_bullets = self.bullet_formatter.format_bullets(
                    raw_bullets=raw_bullets,
                    project_name=repo_name,
                    tech_stack=tech_stack,
                    project_description=readme_info.get("description")
                )
            except Exception as e:
                # Fallback to raw bullets if formatting fails
                print(f"Warning: Bullet formatting failed: {e}")
                formatted_bullets = raw_bullets
        else:
            # Use raw bullets if formatter not available
            formatted_bullets = raw_bullets
        
        # Convert to Bullet objects
        bullets = []
        for bullet_text in formatted_bullets:
            # Extract skills mentioned in bullet (simple keyword matching)
            skills = self._extract_skills_from_bullet(bullet_text, tech_stack)
            bullets.append(Bullet(text=bullet_text, skills=skills, evidence=None))
        
        # Create ProjectItem
        project = ProjectItem(
            name=repo_name,
            tech_stack=tech_stack,
            start_date=start_date,
            end_date=None,  # GitHub doesn't provide end date
            bullets=bullets if bullets else [
                Bullet(text=f"Repository: {repo_url}", skills=[], evidence=None)
            ]
        )
        
        return project
    
    def _merge_tech_stack(self, readme_techs: List[str], language_techs: List[str], 
                         dependency_techs: List[str]) -> List[str]:
        """Merge and deduplicate tech stack from multiple sources.
        
        Args:
            readme_techs: Technologies mentioned in README
            language_techs: Languages from GitHub API
            dependency_techs: Technologies from dependency files
            
        Returns:
            Merged and deduplicated list of technologies
        """
        # Combine all sources
        all_techs = set()
        
        # Add languages (these are reliable)
        for lang in language_techs:
            # Normalize language names
            normalized = self._normalize_language(lang)
            if normalized:
                all_techs.add(normalized)
        
        # Add dependency techs
        for tech in dependency_techs:
            all_techs.add(tech)
        
        # Add README techs (but prioritize others if there's overlap)
        for tech in readme_techs:
            # Only add if not already covered by languages/dependencies
            if not any(tech.lower() in existing.lower() or existing.lower() in tech.lower() 
                      for existing in all_techs):
                all_techs.add(tech)
        
        # Sort and return
        return sorted(list(all_techs))
    
    def _normalize_language(self, lang: str) -> Optional[str]:
        """Normalize language name from GitHub API.
        
        Args:
            lang: Language name from GitHub API
            
        Returns:
            Normalized language name, or None if not a recognized language
        """
        # GitHub API returns language names like "Python", "JavaScript", etc.
        # Most are already normalized, but handle some edge cases
        lang_lower = lang.lower()
        
        mappings = {
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "python": "Python",
            "java": "Java",
            "c++": "C++",
            "c#": "C#",
            "go": "Go",
            "rust": "Rust",
            "ruby": "Ruby",
            "php": "PHP",
            "swift": "Swift",
            "kotlin": "Kotlin",
            "scala": "Scala",
            "r": "R",
            "matlab": "MATLAB",
            "html": "HTML",
            "css": "CSS",
            "shell": "Shell",
            "powershell": "PowerShell",
        }
        
        if lang_lower in mappings:
            return mappings[lang_lower]
        
        # If already capitalized properly, return as-is
        if lang and lang[0].isupper():
            return lang
        
        return None
    
    def _extract_skills_from_bullet(self, bullet_text: str, tech_stack: List[str]) -> List[str]:
        """Extract skills mentioned in a bullet point.
        
        Args:
            bullet_text: Bullet text
            tech_stack: List of technologies used in the project
            
        Returns:
            List of skills mentioned in the bullet
        """
        skills = []
        bullet_lower = bullet_text.lower()
        
        # Check which tech stack items are mentioned in the bullet
        for tech in tech_stack:
            # Simple word boundary matching
            tech_lower = tech.lower()
            # Check if tech name appears in bullet (with word boundaries)
            import re
            pattern = r'\b' + re.escape(tech_lower) + r'\b'
            if re.search(pattern, bullet_lower):
                skills.append(tech)
        
        return skills