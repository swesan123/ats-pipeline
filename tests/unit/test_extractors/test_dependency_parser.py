"""Tests for dependency parser."""

from src.extractors.dependency_parser import DependencyParser


def test_detect_project_type_nodejs():
    """Test detecting Node.js project."""
    parser = DependencyParser()
    
    file_paths = ["src/index.js", "package.json", "README.md"]
    result = parser.detect_project_type(file_paths)
    
    assert result == "nodejs"


def test_detect_project_type_python():
    """Test detecting Python project."""
    parser = DependencyParser()
    
    file_paths = ["src/main.py", "requirements.txt", "README.md"]
    result = parser.detect_project_type(file_paths)
    
    assert result == "python"
    
    # Test with pyproject.toml
    file_paths = ["pyproject.toml", "src/main.py"]
    result = parser.detect_project_type(file_paths)
    assert result == "python"


def test_detect_project_type_java():
    """Test detecting Java project."""
    parser = DependencyParser()
    
    file_paths = ["src/Main.java", "pom.xml", "README.md"]
    result = parser.detect_project_type(file_paths)
    
    assert result == "java"
    
    # Test with build.gradle
    file_paths = ["build.gradle", "src/Main.java"]
    result = parser.detect_project_type(file_paths)
    assert result == "java"


def test_detect_project_type_rust():
    """Test detecting Rust project."""
    parser = DependencyParser()
    
    file_paths = ["src/main.rs", "Cargo.toml", "README.md"]
    result = parser.detect_project_type(file_paths)
    
    assert result == "rust"


def test_detect_project_type_go():
    """Test detecting Go project."""
    parser = DependencyParser()
    
    file_paths = ["main.go", "go.mod", "README.md"]
    result = parser.detect_project_type(file_paths)
    
    assert result == "go"


def test_parse_package_json():
    """Test parsing package.json."""
    parser = DependencyParser()
    
    content = """{
  "name": "test-project",
  "dependencies": {
    "react": "^18.0.0",
    "express": "^4.18.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0"
  }
}
"""
    result = parser.parse("package.json", content)
    
    assert "React" in result
    assert "Express.js" in result
    assert "TypeScript" in result


def test_parse_requirements_txt():
    """Test parsing requirements.txt."""
    parser = DependencyParser()
    
    content = """django==4.2.0
flask>=2.0.0
tensorflow==2.13.0
# Comment line
pandas==2.0.0
"""
    result = parser.parse("requirements.txt", content)
    
    assert "Django" in result
    assert "Flask" in result
    assert "TensorFlow" in result


def test_parse_pom_xml():
    """Test parsing pom.xml."""
    parser = DependencyParser()
    
    content = """<?xml version="1.0"?>
<project>
  <dependencies>
    <dependency>
      <artifactId>spring-boot-starter</artifactId>
    </dependency>
  </dependencies>
</project>
"""
    result = parser.parse("pom.xml", content)
    
    assert "Spring Boot" in result
    assert "Spring" in result


def test_parse_cargo_toml():
    """Test parsing Cargo.toml."""
    parser = DependencyParser()
    
    content = """[package]
name = "test"

[dependencies]
tokio = "1.0"
serde = "1.0"
"""
    result = parser.parse("Cargo.toml", content)
    
    assert "Tokio" in result
    assert "Serde" in result


def test_parse_go_mod():
    """Test parsing go.mod."""
    parser = DependencyParser()
    
    content = """module test

require (
    github.com/gin-gonic/gin v1.9.0
    github.com/gorilla/mux v1.8.0
)
"""
    result = parser.parse("go.mod", content)
    
    assert "Gin" in result
    assert "Gorilla" in result


def test_parse_pyproject_toml():
    """Test parsing pyproject.toml."""
    parser = DependencyParser()
    
    content = """[project]
name = "test"

[project.dependencies]
django = ">=4.0"
flask = ">=2.0"
"""
    result = parser.parse("pyproject.toml", content)
    
    assert "Django" in result
    assert "Flask" in result


def test_normalize_tech_name():
    """Test technology name normalization."""
    parser = DependencyParser()
    
    # Direct mapping
    assert parser._normalize_tech_name("react") == "React"
    assert parser._normalize_tech_name("django") == "Django"
    
    # Contains mapping
    assert parser._normalize_tech_name("react-dom") == "React"
    
    # Common language
    assert parser._normalize_tech_name("python") == "Python"
    assert parser._normalize_tech_name("javascript") == "Javascript"
    
    # Unknown tech
    assert parser._normalize_tech_name("unknown-package") is None


def test_parse_invalid_json():
    """Test parsing invalid JSON returns empty list."""
    parser = DependencyParser()
    
    result = parser.parse("package.json", "invalid json {")
    assert result == []


def test_parse_unknown_file():
    """Test parsing unknown file type returns empty list."""
    parser = DependencyParser()
    
    result = parser.parse("unknown.txt", "some content")
    assert result == []
