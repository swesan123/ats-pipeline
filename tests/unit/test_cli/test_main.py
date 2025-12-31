"""Unit tests for CLI helper functions."""

import json
import pytest
from pathlib import Path
from src.cli.main import _load_job_skills_from_file, _load_skill_ontology, _ensure_data_dir
from src.models.job import JobPosting, JobSkills
from src.models.skills import SkillOntology


class TestLoadJobSkillsFromFile:
    """Tests for _load_job_skills_from_file helper function."""
    
    def test_load_new_format_with_job_posting(self, tmp_path, sample_job_skills, sample_job_posting):
        """Test loading job skills from new format with job_posting."""
        job_file = tmp_path / "job.json"
        job_data = {
            "job_posting": sample_job_posting.model_dump(),
            "job_skills": sample_job_skills.model_dump()
        }
        with open(job_file, 'w', encoding='utf-8') as f:
            json.dump(job_data, f)
        
        job_skills, job_posting = _load_job_skills_from_file(job_file)
        
        assert isinstance(job_skills, JobSkills)
        assert job_skills.required_skills == sample_job_skills.required_skills
        assert isinstance(job_posting, JobPosting)
        assert job_posting.company == sample_job_posting.company
    
    def test_load_new_format_without_job_posting(self, tmp_path, sample_job_skills):
        """Test loading job skills from new format without job_posting."""
        job_file = tmp_path / "job.json"
        job_data = {
            "job_skills": sample_job_skills.model_dump()
        }
        with open(job_file, 'w', encoding='utf-8') as f:
            json.dump(job_data, f)
        
        job_skills, job_posting = _load_job_skills_from_file(job_file)
        
        assert isinstance(job_skills, JobSkills)
        assert job_skills.required_skills == sample_job_skills.required_skills
        assert job_posting is None
    
    def test_load_old_format(self, tmp_path, sample_job_skills):
        """Test loading job skills from old format (just job_skills)."""
        job_file = tmp_path / "job.json"
        job_data = sample_job_skills.model_dump()
        with open(job_file, 'w', encoding='utf-8') as f:
            json.dump(job_data, f)
        
        job_skills, job_posting = _load_job_skills_from_file(job_file)
        
        assert isinstance(job_skills, JobSkills)
        assert job_skills.required_skills == sample_job_skills.required_skills
        assert job_posting is None
    
    def test_load_invalid_file_raises_error(self, tmp_path):
        """Test that loading invalid JSON raises appropriate error."""
        job_file = tmp_path / "invalid.json"
        with open(job_file, 'w', encoding='utf-8') as f:
            f.write("invalid json content")
        
        with pytest.raises((json.JSONDecodeError, ValueError)):
            _load_job_skills_from_file(job_file)
    
    def test_load_missing_file_raises_error(self, tmp_path):
        """Test that loading non-existent file raises FileNotFoundError."""
        job_file = tmp_path / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            _load_job_skills_from_file(job_file)


class TestLoadSkillOntology:
    """Tests for _load_skill_ontology helper function."""
    
    def test_load_ontology_from_file(self, tmp_path):
        """Test loading skill ontology from existing file."""
        ontology_file = tmp_path / "ontology.json"
        ontology_data = {
            "skills": [
                {"name": "Python", "category": "Language"},
                {"name": "React", "category": "Framework"}
            ]
        }
        with open(ontology_file, 'w', encoding='utf-8') as f:
            json.dump(ontology_data, f)
        
        ontology = _load_skill_ontology(str(ontology_file))
        
        assert isinstance(ontology, SkillOntology)
    
    def test_load_ontology_none_returns_empty(self):
        """Test that passing None returns empty ontology."""
        ontology = _load_skill_ontology(None)
        
        assert isinstance(ontology, SkillOntology)
    
    def test_load_ontology_empty_string_returns_empty(self):
        """Test that passing empty string returns empty ontology."""
        ontology = _load_skill_ontology("")
        
        assert isinstance(ontology, SkillOntology)
    
    def test_load_ontology_nonexistent_file_returns_empty(self, tmp_path):
        """Test that non-existent file returns empty ontology."""
        ontology_file = tmp_path / "nonexistent.json"
        
        ontology = _load_skill_ontology(str(ontology_file))
        
        assert isinstance(ontology, SkillOntology)
    
    def test_load_ontology_invalid_file_raises_error(self, tmp_path):
        """Test that invalid JSON file raises appropriate error."""
        ontology_file = tmp_path / "invalid.json"
        with open(ontology_file, 'w', encoding='utf-8') as f:
            f.write("invalid json")
        
        with pytest.raises((json.JSONDecodeError, ValueError)):
            _load_skill_ontology(str(ontology_file))
    
    def test_load_ontology_with_valid_skill_ontology_data(self, tmp_path):
        """Test loading ontology with valid skill ontology structure."""
        ontology_file = tmp_path / "ontology.json"
        # Create a minimal valid ontology structure
        ontology_data = {
            "skills": []
        }
        with open(ontology_file, 'w', encoding='utf-8') as f:
            json.dump(ontology_data, f)
        
        ontology = _load_skill_ontology(str(ontology_file))
        
        assert isinstance(ontology, SkillOntology)


class TestEnsureDataDir:
    """Tests for _ensure_data_dir helper function."""
    
    def test_creates_data_directory_if_missing(self, tmp_path, monkeypatch):
        """Test that data directory is created if it doesn't exist."""
        # Change to tmp_path for testing
        original_cwd = Path.cwd()
        monkeypatch.chdir(tmp_path)
        
        try:
            data_dir = _ensure_data_dir()
            
            assert data_dir.exists()
            assert data_dir.is_dir()
            assert data_dir.name == "data"
        finally:
            monkeypatch.chdir(original_cwd)
    
    def test_returns_existing_data_directory(self, tmp_path, monkeypatch):
        """Test that existing data directory is returned."""
        # Change to tmp_path for testing
        original_cwd = Path.cwd()
        monkeypatch.chdir(tmp_path)
        
        try:
            # Create data directory first
            data_dir_manual = tmp_path / "data"
            data_dir_manual.mkdir()
            
            data_dir = _ensure_data_dir()
            
            assert data_dir.exists()
            # Compare resolved paths since _ensure_data_dir returns relative path
            assert data_dir.resolve() == data_dir_manual.resolve()
        finally:
            monkeypatch.chdir(original_cwd)
    
    def test_returns_path_object(self, tmp_path, monkeypatch):
        """Test that function returns Path object."""
        original_cwd = Path.cwd()
        monkeypatch.chdir(tmp_path)
        
        try:
            data_dir = _ensure_data_dir()
            
            assert isinstance(data_dir, Path)
        finally:
            monkeypatch.chdir(original_cwd)
