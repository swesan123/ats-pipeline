"""GitHub API client for fetching repository information."""

import base64
import os
import re
from datetime import datetime
from typing import Dict, Optional, Tuple

import requests


class GitHubAPIClient:
    """Client for interacting with GitHub API."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub API client.
        
        Args:
            token: GitHub personal access token. If None, reads from GITHUB_TOKEN env var.
                  If not set, uses unauthenticated requests (lower rate limits).
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.session = requests.Session()
        
        # Set headers
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ATS-Pipeline"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        
        self.session.headers.update(headers)
    
    def parse_github_url(self, url: str) -> Tuple[str, str]:
        """Parse GitHub URL to extract owner and repo name.
        
        Args:
            url: GitHub repository URL (e.g., https://github.com/owner/repo)
            
        Returns:
            Tuple of (owner, repo)
            
        Raises:
            ValueError: If URL is invalid or not a GitHub repository URL
        """
        # Handle various GitHub URL formats
        patterns = [
            r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?(?:/.*)?$',
            r'github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/.*)?$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                owner = match.group(1)
                repo = match.group(2).rstrip('/')
                return owner, repo
        
        raise ValueError(f"Invalid GitHub URL format: {url}")
    
    def get_repository(self, owner: str, repo: str) -> Dict:
        """Get repository metadata.
        
        Args:
            owner: Repository owner/username
            repo: Repository name
            
        Returns:
            Dictionary with repository information including:
            - name: Repository name
            - description: Repository description
            - created_at: Creation date (ISO format)
            - updated_at: Last update date
            - language: Primary language
            - full_name: Full repository name (owner/repo)
            
        Raises:
            requests.HTTPError: If API request fails
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def get_readme(self, owner: str, repo: str) -> Optional[str]:
        """Get README.md content.
        
        Args:
            owner: Repository owner/username
            repo: Repository name
            
        Returns:
            README content as string, or None if README doesn't exist
            
        Raises:
            requests.HTTPError: If API request fails (except 404)
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/readme"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Decode base64 content
            content = base64.b64decode(data.get("content", "")).decode("utf-8")
            return content
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    def get_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """Get repository languages with byte counts.
        
        Args:
            owner: Repository owner/username
            repo: Repository name
            
        Returns:
            Dictionary mapping language names to byte counts
            (e.g., {"Python": 5000, "JavaScript": 3000})
            
        Raises:
            requests.HTTPError: If API request fails
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/languages"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def get_file_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        """Get file content from repository.
        
        Args:
            owner: Repository owner/username
            repo: Repository name
            path: File path in repository (e.g., "package.json")
            
        Returns:
            File content as string, or None if file doesn't exist
            
        Raises:
            requests.HTTPError: If API request fails (except 404)
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Handle both file and directory responses
            if isinstance(data, list):
                # Directory listing, find the file
                for item in data:
                    if item.get("name") == path.split("/")[-1] and item.get("type") == "file":
                        content_url = item.get("download_url")
                        if content_url:
                            file_response = self.session.get(content_url, timeout=10)
                            file_response.raise_for_status()
                            return file_response.text
                return None
            
            # Single file response
            if data.get("type") == "file":
                # Decode base64 content
                content = base64.b64decode(data.get("content", "")).decode("utf-8")
                return content
            
            return None
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    def format_creation_date(self, created_at: str) -> Optional[str]:
        """Format GitHub API date to project date format.
        
        Args:
            created_at: ISO format date string from GitHub API
            
        Returns:
            Formatted date string (e.g., "Jan 2024"), or None if parsing fails
        """
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            return dt.strftime("%b %Y")
        except (ValueError, AttributeError):
            return None
