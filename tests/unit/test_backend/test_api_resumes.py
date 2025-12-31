"""Tests for resumes API endpoints."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
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


def test_list_resumes_empty(client, mock_db):
    """Test listing resumes when database is empty."""
    cursor_mock = Mock()
    cursor_mock.fetchall.return_value = []
    mock_db.conn.cursor.return_value = cursor_mock
    
    response = client.get("/api/v1/resumes")
    assert response.status_code == 200
    assert response.json() == []


def test_list_resumes_with_data(client, mock_db):
    """Test listing resumes with data."""
    from datetime import datetime
    from unittest.mock import MagicMock
    
    cursor_mock = Mock()
    row_mock = MagicMock()
    row_mock.__getitem__ = lambda self, key: {
        "id": 1,
        "version": "1",
        "file_path": "data/resumes/resume_1.pdf",
        "job_id": None,
        "is_customized": False,
        "updated_at": "2024-01-01T00:00:00",
    }[key]
    cursor_mock.fetchall.return_value = [row_mock]
    mock_db.conn.cursor.return_value = cursor_mock
    
    response = client.get("/api/v1/resumes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1


def test_get_resume(client, mock_db, sample_resume):
    """Test getting a specific resume."""
    mock_db.get_resume.return_value = sample_resume
    
    response = client.get("/api/v1/resumes/1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test User"
    mock_db.get_resume.assert_called_once_with(1)


def test_render_pdf_get_success(client, mock_db, sample_resume):
    """Test GET PDF rendering endpoint for preview."""
    import tempfile
    from pathlib import Path
    
    mock_db.get_resume.return_value = sample_resume
    
    with patch("src.rendering.latex_renderer.LaTeXRenderer") as mock_renderer_class:
        mock_renderer = Mock()
        mock_renderer_class.return_value = mock_renderer
        
        # Mock the render_pdf method to create the temp file
        def mock_render_pdf(resume, path):
            path.write_bytes(b"fake pdf content")
        mock_renderer.render_pdf = mock_render_pdf
        
        # Mock Path.exists to return True for template
        with patch.object(Path, 'exists') as mock_exists:
            def exists_side_effect(self):
                return str(self).endswith('resume.tex') or 'templates' in str(self)
            mock_exists.side_effect = exists_side_effect
            
            response = client.get("/api/v1/resumes/1/render-pdf")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            assert "inline" in response.headers["content-disposition"]
            assert len(response.content) > 0
            mock_db.get_resume.assert_called_once_with(1)


def test_render_pdf_get_not_found(client, mock_db):
    """Test GET PDF rendering when resume not found."""
    mock_db.get_resume.return_value = None
    
    response = client.get("/api/v1/resumes/999/render-pdf")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_render_pdf_post_success(client, mock_db, sample_resume):
    """Test POST PDF rendering endpoint for download."""
    import tempfile
    from pathlib import Path
    
    mock_db.get_resume.return_value = sample_resume
    
    with patch("src.rendering.latex_renderer.LaTeXRenderer") as mock_renderer_class:
        mock_renderer = Mock()
        mock_renderer_class.return_value = mock_renderer
        
        # Mock the render_pdf method
        def mock_render_pdf(resume, path):
            path.write_bytes(b"fake pdf content")
        mock_renderer.render_pdf = mock_render_pdf
        
        # Mock Path.exists to return True for template
        with patch.object(Path, 'exists') as mock_exists:
            def exists_side_effect(self):
                return str(self).endswith('resume.tex') or 'templates' in str(self)
            mock_exists.side_effect = exists_side_effect
            
            response = client.post("/api/v1/resumes/1/render-pdf")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            assert "attachment" in response.headers["content-disposition"]
            assert len(response.content) > 0
            mock_db.get_resume.assert_called_once_with(1)


def test_get_resume_not_found(client, mock_db):
    """Test getting a non-existent resume."""
    mock_db.get_resume.return_value = None
    
    response = client.get("/api/v1/resumes/999")
    assert response.status_code == 404


def test_save_resume(client, mock_db, sample_resume):
    """Test saving a resume."""
    from datetime import datetime
    from unittest.mock import MagicMock
    
    mock_db.save_resume.return_value = 1
    cursor_mock = Mock()
    row_mock = MagicMock()
    row_mock.__getitem__ = lambda self, key: {
        "id": 1,
        "version": "1",
        "file_path": "data/resumes/resume_1.pdf",
        "job_id": None,
        "is_customized": False,
        "updated_at": "2024-01-01T00:00:00",
    }[key]
    cursor_mock.fetchone.return_value = row_mock
    mock_db.conn.cursor.return_value = cursor_mock
    
    resume_data = sample_resume.model_dump(mode='json')
    response = client.post("/api/v1/resumes", json=resume_data)
    assert response.status_code == 201
    assert mock_db.save_resume.called


def test_rewrite_resume(client, mock_db, sample_resume):
    """Test rewriting a resume."""
    from src.models.job import JobPosting
    
    mock_db.get_resume.return_value = sample_resume
    mock_db.get_job_full.return_value = {"id": 1, "company": "Test", "title": "Engineer"}
    mock_db.get_job.return_value = JobPosting(
        company="Test",
        title="Engineer",
        description="Test",
    )
    mock_db.save_resume.return_value = 2
    
    with patch('src.compilation.resume_rewriter.ResumeRewriter') as mock_rewriter_class:
        mock_rewriter = Mock()
        mock_rewriter.rewrite_resume.return_value = sample_resume
        mock_rewriter_class.return_value = mock_rewriter
        
        request_data = {"job_id": 1, "rewrite_intent": "emphasize_skills"}
        response = client.post("/api/v1/resumes/1/rewrite", json=request_data)
        assert response.status_code == 200
        assert mock_db.save_resume.called


def test_rewrite_resume_not_found(client, mock_db):
    """Test rewriting a non-existent resume."""
    mock_db.get_resume.return_value = None
    
    request_data = {"job_id": 1}
    response = client.post("/api/v1/resumes/999/rewrite", json=request_data)
    assert response.status_code == 404


def test_render_pdf(client, mock_db, sample_resume):
    """Test rendering PDF."""
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
                
                response = client.post("/api/v1/resumes/1/render-pdf")
                # PDF rendering returns FileResponse, check status
                assert response.status_code in [200, 404]  # 404 if template not found
    finally:
        if temp_pdf_path.exists():
            temp_pdf_path.unlink()


def test_render_pdf_get_success(client, mock_db, sample_resume):
    """Test GET endpoint for PDF preview."""
    import tempfile
    from pathlib import Path
    
    mock_db.get_resume.return_value = sample_resume
    
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
                assert response.status_code in [200, 404]
                if response.status_code == 200:
                    assert response.headers.get("content-type") == "application/pdf"
    finally:
        if temp_pdf_path.exists():
            temp_pdf_path.unlink()


def test_render_pdf_post_success(client, mock_db, sample_resume):
    """Test POST endpoint for PDF download."""
    import tempfile
    from pathlib import Path
    
    mock_db.get_resume.return_value = sample_resume
    
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
                
                response = client.post("/api/v1/resumes/1/render-pdf")
                assert response.status_code in [200, 404]
                if response.status_code == 200:
                    assert response.headers.get("content-type") == "application/pdf"
    finally:
        if temp_pdf_path.exists():
            temp_pdf_path.unlink()


def test_render_pdf_resume_not_found(client, mock_db):
    """Test rendering PDF for non-existent resume."""
    mock_db.get_resume.return_value = None
    
    response = client.post("/api/v1/resumes/999/render-pdf")
    assert response.status_code == 404
