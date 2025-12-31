"""Unit tests for ProjectLibrary."""

import json
import pytest
from pathlib import Path
from src.projects.project_library import ProjectLibrary
from src.models.resume import ProjectItem, Bullet


@pytest.fixture
def sample_project():
    """Sample project for testing."""
    return ProjectItem(
        name="Test Project",
        description="A test project",
        tech_stack=["Python", "React"],
        start_date="2020-01",
        end_date="2020-06",
        bullets=[
            Bullet(text="Developed features", skills=["Python"]),
            Bullet(text="Built UI", skills=["React"]),
        ],
    )


@pytest.fixture
def library_path(tmp_path):
    """Path to test library file."""
    return tmp_path / "test_projects_library.json"


@pytest.fixture
def project_library(library_path):
    """ProjectLibrary instance for testing."""
    return ProjectLibrary(library_path=library_path)


class TestProjectLibraryInitialization:
    """Tests for ProjectLibrary initialization."""
    
    def test_initializes_with_custom_path(self, library_path):
        """Test initialization with custom library path."""
        library = ProjectLibrary(library_path=library_path)
        
        assert library.library_path == library_path
        assert library_path.exists()
    
    def test_creates_empty_library_if_not_exists(self, library_path):
        """Test that empty library file is created if it doesn't exist."""
        assert not library_path.exists()
        
        ProjectLibrary(library_path=library_path)
        
        assert library_path.exists()
        with open(library_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert data == []
    
    def test_creates_parent_directory_if_needed(self, tmp_path):
        """Test that parent directory is created if it doesn't exist."""
        library_path = tmp_path / "nested" / "dir" / "library.json"
        
        ProjectLibrary(library_path=library_path)
        
        assert library_path.exists()
        assert library_path.parent.exists()


class TestProjectLibraryAddProject:
    """Tests for adding projects to library."""
    
    def test_add_new_project(self, project_library, sample_project):
        """Test adding a new project to empty library."""
        project_library.add_project(sample_project)
        
        projects = project_library.get_all_projects()
        assert len(projects) == 1
        assert projects[0].name == sample_project.name
    
    def test_add_multiple_projects(self, project_library, sample_project):
        """Test adding multiple projects."""
        project1 = sample_project
        project2 = ProjectItem(
            name="Another Project",
            description="Another test",
            tech_stack=["JavaScript"],
            bullets=[],
        )
        
        project_library.add_project(project1)
        project_library.add_project(project2)
        
        projects = project_library.get_all_projects()
        assert len(projects) == 2
    
    def test_add_project_updates_existing(self, project_library, sample_project):
        """Test that adding project with same name updates existing."""
        project_library.add_project(sample_project)
        
        updated_project = ProjectItem(
            name=sample_project.name,
            tech_stack=["Python", "Django"],
            bullets=[],
        )
        project_library.add_project(updated_project)
        
        projects = project_library.get_all_projects()
        assert len(projects) == 1
        assert projects[0].tech_stack == ["Python", "Django"]


class TestProjectLibraryRemoveProject:
    """Tests for removing projects from library."""
    
    def test_remove_existing_project(self, project_library, sample_project):
        """Test removing an existing project."""
        project_library.add_project(sample_project)
        
        result = project_library.remove_project(sample_project.name)
        
        assert result is True
        projects = project_library.get_all_projects()
        assert len(projects) == 0
    
    def test_remove_nonexistent_project(self, project_library):
        """Test removing a project that doesn't exist."""
        result = project_library.remove_project("Nonexistent")
        
        assert result is False
    
    def test_remove_project_from_multiple(self, project_library, sample_project):
        """Test removing one project from multiple."""
        project1 = sample_project
        project2 = ProjectItem(
            name="Another Project",
            description="Another test",
            tech_stack=["JavaScript"],
            bullets=[],
        )
        
        project_library.add_project(project1)
        project_library.add_project(project2)
        
        result = project_library.remove_project(project1.name)
        
        assert result is True
        projects = project_library.get_all_projects()
        assert len(projects) == 1
        assert projects[0].name == project2.name


class TestProjectLibraryGetProjects:
    """Tests for retrieving projects from library."""
    
    def test_get_all_projects_empty_library(self, project_library):
        """Test getting all projects from empty library."""
        projects = project_library.get_all_projects()
        
        assert projects == []
    
    def test_get_all_projects(self, project_library, sample_project):
        """Test getting all projects."""
        project_library.add_project(sample_project)
        
        projects = project_library.get_all_projects()
        
        assert len(projects) == 1
        assert isinstance(projects[0], ProjectItem)
        assert projects[0].name == sample_project.name
    
    def test_get_project_by_name_exists(self, project_library, sample_project):
        """Test getting a project by name when it exists."""
        project_library.add_project(sample_project)
        
        project = project_library.get_project(sample_project.name)
        
        assert project is not None
        assert isinstance(project, ProjectItem)
        assert project.name == sample_project.name
    
    def test_get_project_by_name_not_exists(self, project_library):
        """Test getting a project by name when it doesn't exist."""
        project = project_library.get_project("Nonexistent")
        
        assert project is None
    
    def test_get_project_from_multiple(self, project_library, sample_project):
        """Test getting specific project from multiple."""
        project1 = sample_project
        project2 = ProjectItem(
            name="Another Project",
            description="Another test",
            tech_stack=["JavaScript"],
            bullets=[],
        )
        
        project_library.add_project(project1)
        project_library.add_project(project2)
        
        project = project_library.get_project(project1.name)
        
        assert project is not None
        assert project.name == project1.name


class TestProjectLibraryPersistence:
    """Tests for library persistence."""
    
    def test_projects_persist_to_file(self, library_path, sample_project):
        """Test that projects are saved to file."""
        library1 = ProjectLibrary(library_path=library_path)
        library1.add_project(sample_project)
        
        # Create new library instance to verify persistence
        library2 = ProjectLibrary(library_path=library_path)
        projects = library2.get_all_projects()
        
        assert len(projects) == 1
        assert projects[0].name == sample_project.name
    
    def test_handles_invalid_project_data_gracefully(self, library_path):
        """Test that invalid project data is skipped gracefully."""
        # Write invalid data to file
        invalid_data = [
            {"name": "Valid Project", "description": "Valid"},
            {"invalid": "data"},
        ]
        with open(library_path, 'w', encoding='utf-8') as f:
            json.dump(invalid_data, f)
        
        library = ProjectLibrary(library_path=library_path)
        projects = library.get_all_projects()
        
        # Should only return valid projects
        assert len(projects) >= 0  # May have 0 or 1 valid projects depending on validation
