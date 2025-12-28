"""Project library management for storing and retrieving projects."""

import json
from pathlib import Path
from typing import List, Optional
from src.models.resume import ProjectItem


class ProjectLibrary:
    """Manage a library of all user projects."""
    
    def __init__(self, library_path: Optional[Path] = None):
        """Initialize project library.
        
        Args:
            library_path: Path to JSON file storing projects. Defaults to data/projects_library.json
        """
        if library_path is None:
            library_path = Path("data/projects_library.json")
        self.library_path = Path(library_path)
        self._ensure_library_exists()
    
    def _ensure_library_exists(self) -> None:
        """Ensure library file and directory exist."""
        self.library_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.library_path.exists():
            # Initialize with empty list
            with open(self.library_path, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2)
    
    def add_project(self, project: ProjectItem) -> None:
        """Add a project to the library."""
        projects = self.get_all_projects()
        
        # Check if project with same name already exists
        for i, existing in enumerate(projects):
            if existing.name == project.name:
                # Update existing project
                projects[i] = project
                self._save_projects(projects)
                return
        
        # Add new project
        projects.append(project)
        self._save_projects(projects)
    
    def remove_project(self, name: str) -> bool:
        """Remove a project from the library by name.
        
        Returns:
            True if project was found and removed, False otherwise
        """
        projects = self.get_all_projects()
        original_count = len(projects)
        projects = [p for p in projects if p.name != name]
        
        if len(projects) < original_count:
            self._save_projects(projects)
            return True
        return False
    
    def get_all_projects(self) -> List[ProjectItem]:
        """Get all projects from the library."""
        if not self.library_path.exists():
            return []
        
        with open(self.library_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        projects = []
        for item_data in data:
            try:
                project = ProjectItem.model_validate(item_data)
                projects.append(project)
            except Exception as e:
                # Skip invalid projects
                print(f"Warning: Skipping invalid project: {e}")
                continue
        
        return projects
    
    def get_project(self, name: str) -> Optional[ProjectItem]:
        """Get a specific project by name."""
        projects = self.get_all_projects()
        for project in projects:
            if project.name == name:
                return project
        return None
    
    def _save_projects(self, projects: List[ProjectItem]) -> None:
        """Save projects to library file."""
        data = [project.model_dump() for project in projects]
        with open(self.library_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

