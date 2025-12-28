"""Experience library management for storing and retrieving work experience."""

import json
from pathlib import Path
from typing import List, Optional
from src.models.resume import ExperienceItem


class ExperienceLibrary:
    """Manage a library of all user work experience."""
    
    def __init__(self, library_path: Optional[Path] = None):
        """Initialize experience library.
        
        Args:
            library_path: Path to JSON file storing experience. Defaults to data/experience_library.json
        """
        if library_path is None:
            library_path = Path("data/experience_library.json")
        self.library_path = Path(library_path)
        self._ensure_library_exists()
    
    def _ensure_library_exists(self) -> None:
        """Ensure library file and directory exist."""
        self.library_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.library_path.exists():
            # Initialize with empty list
            with open(self.library_path, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2)
    
    def add_experience(self, experience: ExperienceItem) -> None:
        """Add an experience item to the library."""
        experiences = self.get_all_experience()
        
        # Check if experience with same organization and role already exists
        for i, existing in enumerate(experiences):
            if existing.organization == experience.organization and existing.role == experience.role:
                # Update existing experience
                experiences[i] = experience
                self._save_experience(experiences)
                return
        
        # Add new experience
        experiences.append(experience)
        self._save_experience(experiences)
    
    def get_all_experience(self) -> List[ExperienceItem]:
        """Get all experience items from the library."""
        if not self.library_path.exists():
            return []
        
        with open(self.library_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        experiences = []
        for item_data in data:
            try:
                exp = ExperienceItem.model_validate(item_data)
                experiences.append(exp)
            except Exception as e:
                # Skip invalid experience
                print(f"Warning: Skipping invalid experience: {e}")
                continue
        
        return experiences
    
    def _save_experience(self, experiences: List[ExperienceItem]) -> None:
        """Save experience to library file."""
        data = [exp.model_dump() for exp in experiences]
        with open(self.library_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

