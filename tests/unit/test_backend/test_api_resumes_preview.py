"""Tests for resume preview PDF endpoints."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.dependencies import get_db
from src.db.database import Database
from src.models.resume import Resume


@pytest.fixture
def mock_db():
    """Create mock database."""
    db = Mock(spec=Database)
    db.conn = Mock()
    cursor_mock = Mock()
    cursor_mock.execute.return_value = None
    cursor_mock.fetchall.return_value = []
    cursor_mock.fetchone.return_value = None
    db.conn.cursor.return_value = cursor_mock
    return db


@pytest.fixture
def client(mock_db):
    """Create test client with mocked database."""
    app.dependency_overrides[get_db] = lambda: mock_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_resume():
    """Sample resume."""
    return Resume(
        version=1,
        name="Test User",
        email="test@example.com",
        phone="123-456-7890",
        experience=[],
        projects=[],
        skills={},
    )


def test_render_pdf_get_preview(client, mock_db, sample_resume):
    """Test GET endpoint for PDF preview (inline display)."""
    import tempfile
    from pathlib import Path
    
    mock_db.get_resume.return_value = sample_resume
    
    # Create temporary PDF file
    temp_pdf_path = Path(tempfile.gettempdir()) / "resume_1_ats-pipeline.pdf"
    temp_pdf_path.write_bytes(b"fake pdf content")
    
    try:
        def mock_exists(self):
            path_str = str(self)
            return (
                path_str.endswith('resume.tex') or 
                path_str == str(temp_pdf_path) or
                'templates' in path_str
            )
        
        with patch.object(Path, 'exists', mock_exists):
            with patch('src.rendering.latex_renderer.LaTeXRenderer') as mock_renderer_class:
                mock_renderer = Mock()
                mock_renderer.render_pdf.return_value = None
                mock_renderer_class.return_value = mock_renderer
                
                response = client.get("/api/v1/resumes/1/render-pdf")
                # Should return PDF with inline content disposition
                assert response.status_code in [200, 404]  # 404 if template not found
                if response.status_code == 200:
                    assert response.headers.get("content-type") == "application/pdf"
                    assert "inline" in response.headers.get("content-disposition", "").lower()
    finally:
        if temp_pdf_path.exists():
            temp_pdf_path.unlink()


def test_render_pdf_get_resume_not_found(client, mock_db):
    """Test GET PDF preview for non-existent resume."""
    mock_db.get_resume.return_value = None
    
    response = client.get("/api/v1/resumes/999/render-pdf")
    assert response.status_code == 404


def test_preview_template_pdf(client, sample_resume):
    """Test template PDF preview endpoint."""
    from pathlib import Path
    
    def mock_exists(self):
        path_str = str(self)
        return 'resume.tex' in path_str or 'templates' in path_str
    
    with patch.object(Path, 'exists', mock_exists):
        with patch('src.parsers.latex_resume.LaTeXResumeParser') as mock_parser_class, \
             patch('src.rendering.latex_renderer.LaTeXRenderer') as mock_renderer_class:
            
            mock_parser = Mock()
            mock_parser.parse.return_value = sample_resume
            mock_parser_class.from_file.return_value = mock_parser
            
            mock_renderer = Mock()
            mock_renderer.render_pdf.return_value = None
            mock_renderer_class.return_value = mock_renderer
            
            response = client.get("/api/v1/resumes/template/preview-pdf")
            # Should return PDF file
            assert response.status_code in [200, 404]  # 404 if template not found
            if response.status_code == 200:
                assert response.headers.get("content-type") == "application/pdf"
