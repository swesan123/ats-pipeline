"""Tests for GitHub API client."""

import base64
from unittest.mock import Mock, patch
import pytest
import requests
from src.extractors.github_api import GitHubAPIClient


def test_parse_github_url_valid():
    """Test parsing valid GitHub URLs."""
    client = GitHubAPIClient()
    
    # Standard HTTPS URL
    owner, repo = client.parse_github_url("https://github.com/owner/repo")
    assert owner == "owner"
    assert repo == "repo"
    
    # URL with .git suffix
    owner, repo = client.parse_github_url("https://github.com/owner/repo.git")
    assert owner == "owner"
    assert repo == "repo"
    
    # URL with path
    owner, repo = client.parse_github_url("https://github.com/owner/repo/tree/main")
    assert owner == "owner"
    assert repo == "repo"
    
    # SSH format
    owner, repo = client.parse_github_url("git@github.com:owner/repo.git")
    assert owner == "owner"
    assert repo == "repo"


def test_parse_github_url_invalid():
    """Test parsing invalid GitHub URLs raises ValueError."""
    client = GitHubAPIClient()
    
    with pytest.raises(ValueError, match="Invalid GitHub URL"):
        client.parse_github_url("https://gitlab.com/owner/repo")
    
    with pytest.raises(ValueError, match="Invalid GitHub URL"):
        client.parse_github_url("not-a-url")


def test_init_with_token():
    """Test initialization with token."""
    client = GitHubAPIClient(token="test-token")
    assert client.token == "test-token"
    assert "Authorization" in client.session.headers
    assert client.session.headers["Authorization"] == "token test-token"


def test_init_without_token():
    """Test initialization without token uses env var or None."""
    with patch.dict("os.environ", {}, clear=True):
        client = GitHubAPIClient()
        assert client.token is None
        assert "Authorization" not in client.session.headers


def test_get_repository_success():
    """Test successful repository fetch."""
    client = GitHubAPIClient()
    
    mock_response = Mock()
    mock_response.json.return_value = {
        "name": "test-repo",
        "description": "Test description",
        "created_at": "2024-01-15T10:30:00Z",
        "language": "Python"
    }
    mock_response.raise_for_status = Mock()
    
    with patch.object(client.session, "get", return_value=mock_response):
        result = client.get_repository("owner", "repo")
        assert result["name"] == "test-repo"
        assert result["language"] == "Python"


def test_get_readme_success():
    """Test successful README fetch."""
    client = GitHubAPIClient()
    
    content = "Hello World"
    encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    
    mock_response = Mock()
    mock_response.json.return_value = {"content": encoded_content}
    mock_response.raise_for_status = Mock()
    
    with patch.object(client.session, "get", return_value=mock_response):
        result = client.get_readme("owner", "repo")
        assert result == "Hello World"


def test_get_readme_not_found():
    """Test README fetch when README doesn't exist."""
    client = GitHubAPIClient()
    
    mock_response = Mock()
    mock_response.status_code = 404
    error = requests.HTTPError()
    error.response = mock_response
    
    with patch.object(client.session, "get", side_effect=error):
        result = client.get_readme("owner", "repo")
        assert result is None


def test_get_languages_success():
    """Test successful languages fetch."""
    client = GitHubAPIClient()
    
    mock_response = Mock()
    mock_response.json.return_value = {"Python": 5000, "JavaScript": 3000}
    mock_response.raise_for_status = Mock()
    
    with patch.object(client.session, "get", return_value=mock_response):
        result = client.get_languages("owner", "repo")
        assert result["Python"] == 5000
        assert result["JavaScript"] == 3000


def test_get_file_content_success():
    """Test successful file content fetch."""
    client = GitHubAPIClient()
    
    content = '{"name": "test"}'
    encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    
    mock_response = Mock()
    mock_response.json.return_value = {"type": "file", "content": encoded_content}
    mock_response.raise_for_status = Mock()
    
    with patch.object(client.session, "get", return_value=mock_response):
        result = client.get_file_content("owner", "repo", "package.json")
        assert result == content


def test_get_file_content_not_found():
    """Test file content fetch when file doesn't exist."""
    client = GitHubAPIClient()
    
    mock_response = Mock()
    mock_response.status_code = 404
    error = requests.HTTPError()
    error.response = mock_response
    
    with patch.object(client.session, "get", side_effect=error):
        result = client.get_file_content("owner", "repo", "nonexistent.txt")
        assert result is None


def test_format_creation_date_valid():
    """Test formatting valid creation date."""
    client = GitHubAPIClient()
    
    result = client.format_creation_date("2024-01-15T10:30:00Z")
    assert result == "Jan 2024"
    
    result = client.format_creation_date("2023-12-01T00:00:00Z")
    assert result == "Dec 2023"


def test_format_creation_date_invalid():
    """Test formatting invalid date returns None."""
    client = GitHubAPIClient()
    
    result = client.format_creation_date("invalid-date")
    assert result is None
    
    result = client.format_creation_date("")
    assert result is None
