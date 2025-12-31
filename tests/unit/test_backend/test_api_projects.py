"""Tests for projects API endpoints."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from src.models.resume import ProjectItem, Bullet


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_project():
    """Sample project."""
    return ProjectItem(
        name="Test Project",
        tech_stack=["Python", "React"],
        start_date="Jan 2024",
        end_date=None,
        bullets=[
            Bullet(text="Built a web app", skills=[], evidence=None)
        ],
    )


def test_list_projects_empty(client):
    """Test listing projects when library is empty."""
    with patch('backend.app.api.v1.projects.ProjectLibrary') as mock_library_class:
        mock_library = Mock()
        mock_library.get_all_projects.return_value = []
        mock_library_class.return_value = mock_library
        
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        assert response.json() == []


def test_list_projects_with_data(client, sample_project):
    """Test listing projects with data."""
    with patch('backend.app.api.v1.projects.ProjectLibrary') as mock_library_class:
        mock_library = Mock()
        mock_library.get_all_projects.return_value = [sample_project]
        mock_library_class.return_value = mock_library
        
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Project"


def test_create_project(client, sample_project):
    """Test creating a project."""
    with patch('backend.app.api.v1.projects.ProjectLibrary') as mock_library_class:
        mock_library = Mock()
        mock_library_class.return_value = mock_library
        
        response = client.post(
            "/api/v1/projects",
            json={
                "name": "Test Project",
                "tech_stack": ["Python", "React"],
                "start_date": "Jan 2024",
                "bullets": [{"text": "Built a web app", "skills": [], "evidence": None}],
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
        mock_library.add_project.assert_called_once()


def test_import_from_github(client, sample_project):
    """Test importing project from GitHub."""
    with patch('backend.app.api.v1.projects.GitHubRepoExtractor') as mock_extractor_class:
        with patch('backend.app.api.v1.projects.ProjectLibrary') as mock_library_class:
            mock_extractor = Mock()
            mock_extractor.extract_project.return_value = sample_project
            mock_extractor_class.return_value = mock_extractor
            
            mock_library = Mock()
            mock_library_class.return_value = mock_library
            
            response = client.post(
                "/api/v1/projects/github",
                json={"url": "https://github.com/user/repo"}
            )
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Test Project"
            mock_library.add_project.assert_called_once()


def test_import_from_github_invalid_url(client):
    """Test importing project with invalid GitHub URL."""
    with patch('backend.app.api.v1.projects.GitHubRepoExtractor') as mock_extractor_class:
        mock_extractor = Mock()
        mock_extractor.extract_project.side_effect = ValueError("Invalid URL")
        mock_extractor_class.return_value = mock_extractor
        
        response = client.post(
            "/api/v1/projects/github",
            json={"url": "invalid-url"}
        )
        assert response.status_code == 400


def test_update_project(client, sample_project):
    """Test updating a project."""
    with patch('backend.app.api.v1.projects.ProjectLibrary') as mock_library_class:
        mock_library = Mock()
        mock_library.get_project.return_value = sample_project
        mock_library_class.return_value = mock_library
        
        response = client.put(
            "/api/v1/projects/Test Project",
            json={"tech_stack": ["Python", "React", "TypeScript"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert "TypeScript" in data["tech_stack"]


def test_update_project_not_found(client):
    """Test updating a non-existent project."""
    with patch('backend.app.api.v1.projects.ProjectLibrary') as mock_library_class:
        mock_library = Mock()
        mock_library.get_project.return_value = None
        mock_library_class.return_value = mock_library
        
        response = client.put(
            "/api/v1/projects/NonExistent",
            json={"tech_stack": ["Python"]}
        )
        assert response.status_code == 404


def test_delete_project(client):
    """Test deleting a project."""
    with patch('backend.app.api.v1.projects.ProjectLibrary') as mock_library_class:
        mock_library = Mock()
        mock_library.remove_project.return_value = True
        mock_library_class.return_value = mock_library
        
        response = client.delete("/api/v1/projects/Test Project")
        assert response.status_code == 204
        mock_library.remove_project.assert_called_once_with("Test Project")


def test_delete_project_not_found(client):
    """Test deleting a non-existent project."""
    with patch('backend.app.api.v1.projects.ProjectLibrary') as mock_library_class:
        mock_library = Mock()
        mock_library.remove_project.return_value = False
        mock_library_class.return_value = mock_library
        
        response = client.delete("/api/v1/projects/NonExistent")
        assert response.status_code == 404


def test_create_project_auto_adds_tech_stack_skills(client):
    """Test that creating a project automatically adds tech stack skills."""
    from unittest.mock import patch
    
    async def mock_add_skills(*args, **kwargs):
        """Mock async function."""
        pass
    
    with patch('backend.app.api.v1.projects.ProjectLibrary') as mock_library_class:
        with patch('backend.app.api.v1.projects._add_tech_stack_skills_to_user_skills', side_effect=mock_add_skills) as mock_add_skills_func:
            mock_library = Mock()
            mock_library_class.return_value = mock_library
            
            response = client.post(
                "/api/v1/projects",
                json={
                    "name": "Test Project",
                    "tech_stack": ["Python", "React"],
                    "start_date": "Jan 2024",
                    "bullets": [{"text": "Built a web app", "skills": [], "evidence": None}],
                }
            )
            assert response.status_code == 201
            # Verify auto-add function was called
            assert mock_add_skills_func.called
            call_args = mock_add_skills_func.call_args[0]
            assert call_args[0] == ["Python", "React"]
            assert call_args[1] == "Test Project"


def test_update_project_auto_adds_tech_stack_skills(client, sample_project):
    """Test that updating a project automatically adds new tech stack skills."""
    from unittest.mock import patch
    
    async def mock_add_skills(*args, **kwargs):
        """Mock async function."""
        pass
    
    with patch('backend.app.api.v1.projects.ProjectLibrary') as mock_library_class:
        with patch('backend.app.api.v1.projects._add_tech_stack_skills_to_user_skills', side_effect=mock_add_skills) as mock_add_skills_func:
            mock_library = Mock()
            mock_library.get_project.return_value = sample_project
            mock_library_class.return_value = mock_library
            
            response = client.put(
                "/api/v1/projects/Test Project",
                json={"tech_stack": ["Python", "React", "TypeScript"]}
            )
            assert response.status_code == 200
            # Verify auto-add function was called with updated tech stack
            assert mock_add_skills_func.called
            call_args = mock_add_skills_func.call_args[0]
            assert call_args[0] == ["Python", "React", "TypeScript"]
            assert call_args[1] == "Test Project"


def test_import_from_github_auto_adds_tech_stack_skills(client, sample_project):
    """Test that importing from GitHub automatically adds tech stack skills."""
    from unittest.mock import patch
    
    async def mock_add_skills(*args, **kwargs):
        """Mock async function."""
        pass
    
    with patch('backend.app.api.v1.projects.GitHubRepoExtractor') as mock_extractor_class:
        with patch('backend.app.api.v1.projects.ProjectLibrary') as mock_library_class:
            with patch('backend.app.api.v1.projects._add_tech_stack_skills_to_user_skills', side_effect=mock_add_skills) as mock_add_skills_func:
                mock_extractor = Mock()
                mock_extractor.extract_project.return_value = sample_project
                mock_extractor_class.return_value = mock_extractor
                
                mock_library = Mock()
                mock_library_class.return_value = mock_library
                
                response = client.post(
                    "/api/v1/projects/github",
                    json={"url": "https://github.com/user/repo"}
                )
                assert response.status_code == 201
                # Verify auto-add function was called
                assert mock_add_skills_func.called
                call_args = mock_add_skills_func.call_args[0]
                assert call_args[0] == ["Python", "React"]
                assert call_args[1] == "Test Project"
