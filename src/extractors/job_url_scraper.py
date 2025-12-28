"""Job URL scraper for extracting job posting content from URLs."""

import re
from typing import Optional, Dict
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class JobURLScraper:
    """Extract job posting content from URLs."""
    
    def __init__(self, use_playwright: bool = False):
        """Initialize scraper.
        
        Args:
            use_playwright: If True, use Playwright for scraping (handles JS).
                           If False, try requests first, fallback to Playwright.
        """
        self.use_playwright = use_playwright
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def extract_job_content(self, url: str) -> Dict[str, Optional[str]]:
        """
        Extract job posting content from URL.
        Returns dict with: title, company, location, description, source_url
        """
        # Detect job board type
        board_type = self._detect_job_board(url)
        
        if self.use_playwright or board_type in ['greenhouse', 'lever', 'ashby']:
            if not PLAYWRIGHT_AVAILABLE:
                raise ImportError("Playwright is required for this job board. Install with: pip install playwright && playwright install")
            return self._extract_with_playwright(url, board_type)
        else:
            # Try requests first, fallback to Playwright
            try:
                return self._extract_with_requests(url, board_type)
            except Exception as e:
                # Fallback to Playwright for JS-heavy sites
                if PLAYWRIGHT_AVAILABLE:
                    return self._extract_with_playwright(url, board_type)
                else:
                    raise Exception(f"Failed to extract with requests. Playwright not available. Error: {e}")
    
    def _detect_job_board(self, url: str) -> str:
        """Detect which job board the URL belongs to."""
        domain = urlparse(url).netloc.lower()
        
        if 'greenhouse.io' in domain:
            return 'greenhouse'
        elif 'lever.co' in domain:
            return 'lever'
        elif 'ashbyhq.com' in domain:
            return 'ashby'
        elif 'linkedin.com' in domain:
            return 'linkedin'
        elif 'indeed.com' in domain:
            return 'indeed'
        elif 'glassdoor.com' in domain:
            return 'glassdoor'
        else:
            return 'generic'
    
    def _extract_with_requests(self, url: str, board_type: str) -> Dict[str, Optional[str]]:
        """Extract using requests + BeautifulSoup (fast, for static HTML)."""
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Use board-specific extractors
        if board_type == 'greenhouse':
            return self._extract_greenhouse(soup, url)
        elif board_type == 'lever':
            return self._extract_lever(soup, url)
        elif board_type == 'linkedin':
            return self._extract_linkedin(soup, url)
        else:
            return self._extract_generic(soup, url)
    
    def _extract_with_playwright(self, url: str, board_type: str) -> Dict[str, Optional[str]]:
        """Extract using Playwright (handles JavaScript)."""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is not installed. Install with: pip install playwright && playwright install")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Wait for job content to load
                page.wait_for_selector('body', timeout=10000)
                
                html = page.content()
                soup = BeautifulSoup(html, 'lxml')
                
                if board_type == 'greenhouse':
                    result = self._extract_greenhouse(soup, url)
                elif board_type == 'lever':
                    result = self._extract_lever(soup, url)
                elif board_type == 'linkedin':
                    result = self._extract_linkedin(soup, url)
                else:
                    result = self._extract_generic(soup, url)
                
                return result
                
            finally:
                browser.close()
    
    def _extract_greenhouse(self, soup: BeautifulSoup, url: str) -> Dict[str, Optional[str]]:
        """Extract from Greenhouse job board."""
        title = soup.find('h1', class_='app-title') or soup.find('h1')
        title = title.get_text(strip=True) if title else "Unknown"
        
        company = soup.find('div', class_='company-name') or soup.find('a', class_='company-name')
        company = company.get_text(strip=True) if company else "Unknown"
        
        location = soup.find('div', class_='location') or soup.find('div', {'id': 'location'})
        location = location.get_text(strip=True) if location else None
        
        # Job description
        description_elem = soup.find('div', {'id': 'content'}) or soup.find('div', class_='content')
        description = description_elem.get_text(separator='\n', strip=True) if description_elem else ""
        
        return {
            'title': title,
            'company': company,
            'location': location,
            'description': description,
            'source_url': url
        }
    
    def _extract_lever(self, soup: BeautifulSoup, url: str) -> Dict[str, Optional[str]]:
        """Extract from Lever job board."""
        title = soup.find('h2', class_='posting-headline') or soup.find('h2')
        title = title.get_text(strip=True) if title else "Unknown"
        
        company = soup.find('a', class_='main-header-logo') or soup.find('div', class_='main-header-logo')
        company = company.get_text(strip=True) if company else "Unknown"
        
        location = soup.find('div', class_='posting-categories')
        location = location.get_text(strip=True) if location else None
        
        description_elem = soup.find('div', class_='section') or soup.find('div', class_='content')
        description = description_elem.get_text(separator='\n', strip=True) if description_elem else ""
        
        return {
            'title': title,
            'company': company,
            'location': location,
            'description': description,
            'source_url': url
        }
    
    def _extract_linkedin(self, soup: BeautifulSoup, url: str) -> Dict[str, Optional[str]]:
        """Extract from LinkedIn job posting."""
        title = soup.find('h1', class_='topcard__title') or soup.find('h1')
        title = title.get_text(strip=True) if title else "Unknown"
        
        company = soup.find('a', class_='topcard__org-name-link') or soup.find('span', class_='topcard__flavor')
        company = company.get_text(strip=True) if company else "Unknown"
        
        location = soup.find('span', class_='topcard__flavor--bullet') or soup.find('span', class_='topcard__flavor')
        location = location.get_text(strip=True) if location else None
        
        description_elem = soup.find('div', class_='description__text') or soup.find('div', class_='show-more-less-html__markup')
        description = description_elem.get_text(separator='\n', strip=True) if description_elem else ""
        
        return {
            'title': title,
            'company': company,
            'location': location,
            'description': description,
            'source_url': url
        }
    
    def _extract_generic(self, soup: BeautifulSoup, url: str) -> Dict[str, Optional[str]]:
        """Generic extraction for unknown job boards."""
        # Try common selectors
        title = (
            soup.find('h1') or 
            soup.find('title') or
            soup.find('meta', property='og:title')
        )
        if title:
            title = title.get_text(strip=True) if hasattr(title, 'get_text') else title.get('content', 'Unknown')
        else:
            title = "Unknown"
        
        # Try to extract main content
        description_elem = (
            soup.find('div', class_=re.compile(r'description|content|job', re.I)) or
            soup.find('article') or
            soup.find('main') or
            soup.find('div', id=re.compile(r'description|content|job', re.I))
        )
        
        # Remove script and style tags
        if description_elem:
            for script in description_elem(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()
            description = description_elem.get_text(separator='\n', strip=True)
        else:
            # Fallback: extract from body, excluding common non-content elements
            body = soup.find('body')
            if body:
                for element in body(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                    element.decompose()
                description = body.get_text(separator='\n', strip=True)
            else:
                description = ""
        
        return {
            'title': title,
            'company': 'Unknown',
            'location': None,
            'description': description,
            'source_url': url
        }

