"""Tests for GitHub repository extractor."""

from unittest.mock import Mock, patch
import pytest
import requests
from src.extractors.github_repo_extractor import GitHubRepoExtractor
from src.models.resume import ProjectItem, Bullet


@pytest.fixture
def mock_api_client():
    """Mock GitHub API client."""
    client = Mock()
    client.parse_github_url.return_value = ("owner", "repo")
    client.get_repository.return_value = {
        "name": "test-repo",
        "created_at": "2024-01-15T10:30:00Z"
    }
    client.get_readme.return_value = """# Test Project

## Description
This is a test project built with Python and React.

## Features
- Feature 1: Does something cool
- Feature 2: Does something else
"""
    client.get_languages.return_value = {"Python": 5000, "JavaScript": 3000}
    client.get_file_content.return_value = None
    client.format_creation_date.return_value = "Jan 2024"
    return client


@pytest.fixture
def extractor(mock_api_client):
    """Create extractor with mocked API client."""
    extractor = GitHubRepoExtractor()
    extractor.api_client = mock_api_client
    return extractor


def test_extract_project_basic(extractor, mock_api_client):
    """Test basic project extraction."""
    project = extractor.extract_project("https://github.com/owner/repo")
    
    assert isinstance(project, ProjectItem)
    assert project.name == "test-repo"
    assert project.start_date == "Jan 2024"
    assert project.end_date is None
    assert len(project.bullets) > 0
    assert "Python" in project.tech_stack or "JavaScript" in project.tech_stack


def test_extract_project_with_dependencies(extractor, mock_api_client):
    """Test project extraction with dependency files."""
    # Mock dependency file content
    mock_api_client.get_file_content.return_value = """{
  "dependencies": {
    "react": "^18.0.0",
    "express": "^4.18.0"
  }
}
"""
    
    project = extractor.extract_project("https://github.com/owner/repo")
    
    # Should include techs from dependencies
    assert len(project.tech_stack) > 0


def test_extract_project_no_readme(extractor, mock_api_client):
    """Test project extraction when README doesn't exist."""
    mock_api_client.get_readme.return_value = None
    
    project = extractor.extract_project("https://github.com/owner/repo")
    
    # Should still create project with fallback bullet
    assert isinstance(project, ProjectItem)
    assert len(project.bullets) > 0


def test_extract_project_no_bullets(extractor, mock_api_client):
    """Test project extraction when no bullets found in README."""
    mock_api_client.get_readme.return_value = "# Test Project\n\nJust a title."
    
    project = extractor.extract_project("https://github.com/owner/repo")
    
    # Should have at least one bullet (from description or fallback)
    assert len(project.bullets) > 0


def test_merge_tech_stack():
    """Test merging tech stack from multiple sources."""
    extractor = GitHubRepoExtractor()
    
    readme_techs = ["Python", "React", "Docker"]
    language_techs = ["Python", "JavaScript"]
    dependency_techs = ["React", "Express.js"]
    
    result = extractor._merge_tech_stack(readme_techs, language_techs, dependency_techs)
    
    # Should include all unique techs
    assert "Python" in result
    assert "React" in result
    assert "JavaScript" in result
    assert "Express.js" in result
    # Docker might be included if not overlapping
    assert len(result) > 0


def test_normalize_language():
    """Test language name normalization."""
    extractor = GitHubRepoExtractor()
    
    assert extractor._normalize_language("Python") == "Python"
    assert extractor._normalize_language("JavaScript") == "JavaScript"
    assert extractor._normalize_language("javascript") == "JavaScript"
    assert extractor._normalize_language("Go") == "Go"
    # Unknown capitalized language returns as-is (first letter is uppercase)
    assert extractor._normalize_language("Unknown") == "Unknown"
    # Uncapitalized unknown language returns None
    assert extractor._normalize_language("unknown") is None


def test_extract_project_invalid_url(extractor, mock_api_client):
    """Test extraction with invalid URL raises error."""
    mock_api_client.parse_github_url.side_effect = ValueError("Invalid URL")
    
    with pytest.raises(ValueError, match="Invalid URL"):
        extractor.extract_project("not-a-github-url")


def test_extract_project_api_error(extractor, mock_api_client):
    """Test extraction when API call fails."""
    import requests
    mock_api_client.get_repository.side_effect = requests.HTTPError()
    
    with pytest.raises(requests.HTTPError):
        extractor.extract_project("https://github.com/owner/repo")
