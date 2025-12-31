"""Tests for README parser."""

from src.extractors.readme_parser import ReadmeParser


def test_parse_empty_content():
    """Test parsing empty README content."""
    parser = ReadmeParser()
    result = parser.parse("")
    
    assert result["description"] is None
    assert result["bullets"] == []
    assert result["tech_mentions"] == []


def test_extract_description_from_section():
    """Test extracting description from description section."""
    parser = ReadmeParser()
    
    content = """# My Project

## Description
This is a test project that does amazing things.
It uses Python and React.

## Features
- Feature 1
- Feature 2
"""
    result = parser.parse(content)
    
    assert "test project" in result["description"].lower()
    assert len(result["description"]) > 0


def test_extract_description_from_first_paragraph():
    """Test extracting description from first paragraph when no section."""
    parser = ReadmeParser()
    
    content = """# My Project

This is a test project that does amazing things with Python and React.

## Features
- Feature 1
"""
    result = parser.parse(content)
    
    assert "test project" in result["description"].lower()
    assert len(result["description"]) > 0


def test_extract_bullets_from_features_section():
    """Test extracting bullets from Features section."""
    parser = ReadmeParser()
    
    content = """# My Project

## Features
- Implemented feature A that does something important
- Built feature B with Python and React framework
- Created feature C using React library for UI components
"""
    result = parser.parse(content)
    
    # Should extract bullets from Features section (minimum length is 10 chars after cleaning)
    assert len(result["bullets"]) >= 3
    # Check that bullets contain expected keywords
    bullet_texts = " ".join(b.lower() for b in result["bullets"])
    assert "feature" in bullet_texts or "implemented" in bullet_texts
    assert "python" in bullet_texts or "react" in bullet_texts


def test_extract_bullets_from_highlights():
    """Test extracting bullets from Highlights section."""
    parser = ReadmeParser()
    
    content = """# My Project

## Highlights
- Highlight 1: Something important
- Highlight 2: Another important thing
"""
    result = parser.parse(content)
    
    assert len(result["bullets"]) >= 2
    assert any("highlight 1" in b.lower() for b in result["bullets"])


def test_extract_bullets_fallback():
    """Test extracting bullets when no specific section found."""
    parser = ReadmeParser()
    
    content = """# My Project

Some description here.

- Bullet point 1
- Bullet point 2
- Bullet point 3
- Bullet point 4
"""
    result = parser.parse(content)
    
    # Should find bullets if there are at least 3
    assert len(result["bullets"]) >= 3


def test_extract_tech_mentions():
    """Test extracting technology mentions from README."""
    parser = ReadmeParser()
    
    content = """# My Project

Built with Python, React, and TensorFlow.
Uses PostgreSQL for the database.
"""
    result = parser.parse(content)
    
    assert "Python" in result["tech_mentions"]
    assert "React" in result["tech_mentions"]
    assert "TensorFlow" in result["tech_mentions"]
    assert "PostgreSQL" in result["tech_mentions"]


def test_extract_tech_mentions_from_section():
    """Test extracting tech mentions from tech stack section."""
    parser = ReadmeParser()
    
    content = """# My Project

## Tech Stack
- Python
- React
- Docker
"""
    result = parser.parse(content)
    
    assert "Python" in result["tech_mentions"]
    assert "React" in result["tech_mentions"]
    assert "Docker" in result["tech_mentions"]


def test_clean_markdown():
    """Test markdown cleaning removes formatting."""
    parser = ReadmeParser()
    
    text = "This is **bold** and [a link](url) with `code`"
    cleaned = parser._clean_markdown(text)
    
    assert "**bold**" not in cleaned
    assert "[a link](url)" not in cleaned
    assert "`code`" not in cleaned
    assert "bold" in cleaned
    assert "a link" in cleaned
    assert "code" in cleaned


def test_find_section():
    """Test finding a section by header name."""
    parser = ReadmeParser()
    
    content = """# My Project

## Description
This is the description section.
It has multiple lines.

## Features
- Feature 1
"""
    section = parser._find_section(content, ["description"])
    
    assert section is not None
    assert "description section" in section.lower()
    assert "features" not in section.lower()


def test_clean_bullet():
    """Test bullet cleaning removes markdown and punctuation."""
    parser = ReadmeParser()
    
    bullet = "**Implemented** feature with [link](url)."
    cleaned = parser._clean_bullet(bullet)
    
    assert "**" not in cleaned
    assert "[link](url)" not in cleaned
    assert cleaned.endswith(".") is False  # Should strip trailing punctuation
