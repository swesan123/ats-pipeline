#!/usr/bin/env python3
"""One-time conversion utility to convert LaTeX resume to JSON."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parsers.latex_resume import LaTeXResumeParser


def main():
    """Convert LaTeX resume to JSON."""
    if len(sys.argv) < 3:
        print("Usage: python convert_latex_to_json.py <input.tex> <output.json>")
        sys.exit(1)
    
    input_tex = Path(sys.argv[1])
    output_json = Path(sys.argv[2])
    
    if not input_tex.exists():
        print(f"Error: Input file not found: {input_tex}")
        sys.exit(1)
    
    try:
        # Parse LaTeX
        parser = LaTeXResumeParser.from_file(input_tex)
        resume = parser.parse()
        
        # Validate
        resume.model_validate(resume.model_dump())
        
        # Write JSON
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(resume.model_dump(), f, indent=2, default=str)
        
        print(f"✓ Successfully converted {input_tex} to {output_json}")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

