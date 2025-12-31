"""Parser for extracting tech stack from dependency files."""

import json
import re
from typing import List, Optional


class DependencyParser:
    """Parse dependency files to extract technology stack."""
    
    # Technology name mappings (normalize common variations)
    TECH_MAPPINGS = {
        # Node.js
        "react": "React",
        "react-dom": "React",
        "vue": "Vue.js",
        "angular": "Angular",
        "express": "Express.js",
        "next": "Next.js",
        "nuxt": "Nuxt.js",
        "svelte": "Svelte",
        "typescript": "TypeScript",
        "node": "Node.js",
        
        # Python
        "django": "Django",
        "flask": "Flask",
        "fastapi": "FastAPI",
        "tensorflow": "TensorFlow",
        "torch": "PyTorch",
        "pytorch": "PyTorch",
        "scikit-learn": "scikit-learn",
        "sklearn": "scikit-learn",
        "pandas": "pandas",
        "numpy": "numpy",
        "requests": "requests",
        
        # Java
        "spring-boot": "Spring Boot",
        "spring-core": "Spring",
        "spring": "Spring",
        
        # Rust
        "tokio": "Tokio",
        "serde": "Serde",
        "actix": "Actix",
        
        # Go
        "gin": "Gin",
        "echo": "Echo",
        "fiber": "Fiber",
    }
    
    
    def detect_project_type(self, file_paths: List[str]) -> Optional[str]:
        """Detect project type from available file paths.
        
        Args:
            file_paths: List of file paths in repository
            
        Returns:
            Project type: "nodejs", "python", "java", "rust", "go", or None
        """
        for path in file_paths:
            path_lower = path.lower()
            if "package.json" in path_lower:
                return "nodejs"
            elif "requirements.txt" in path_lower or "pyproject.toml" in path_lower or "setup.py" in path_lower:
                return "python"
            elif "pom.xml" in path_lower or "build.gradle" in path_lower:
                return "java"
            elif "cargo.toml" in path_lower:
                return "rust"
            elif "go.mod" in path_lower:
                return "go"
        return None
    
    def parse(self, file_path: str, content: str) -> List[str]:
        """Parse dependency file to extract technologies.
        
        Args:
            file_path: Path to dependency file
            content: File content as string
            
        Returns:
            List of technology names
        """
        path_lower = file_path.lower()
        
        if "package.json" in path_lower:
            return self._parse_package_json(content)
        elif "requirements.txt" in path_lower:
            return self._parse_requirements_txt(content)
        elif "pom.xml" in path_lower:
            return self._parse_pom_xml(content)
        elif "cargo.toml" in path_lower:
            return self._parse_cargo_toml(content)
        elif "go.mod" in path_lower:
            return self._parse_go_mod(content)
        elif "pyproject.toml" in path_lower:
            return self._parse_pyproject_toml(content)
        
        return []
    
    def _parse_package_json(self, content: str) -> List[str]:
        """Parse package.json to extract technologies."""
        try:
            data = json.loads(content)
            techs = set()
            
            # Get dependencies and devDependencies
            deps = {}
            deps.update(data.get("dependencies", {}))
            deps.update(data.get("devDependencies", {}))
            deps.update(data.get("peerDependencies", {}))
            
            for dep_name in deps.keys():
                normalized = self._normalize_tech_name(dep_name)
                if normalized:
                    techs.add(normalized)
            
            # Check for framework indicators
            if "react" in deps or "react-dom" in deps:
                techs.add("React")
            if "vue" in deps:
                techs.add("Vue.js")
            if "angular" in deps:
                techs.add("Angular")
            if "next" in deps:
                techs.add("Next.js")
            if "express" in deps:
                techs.add("Express.js")
            
            return sorted(list(techs))
        except (json.JSONDecodeError, KeyError):
            return []
    
    def _parse_requirements_txt(self, content: str) -> List[str]:
        """Parse requirements.txt to extract technologies."""
        techs = set()
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse package name (before ==, >=, etc.)
            package_match = re.match(r'^([a-zA-Z0-9_-]+)', line)
            if package_match:
                package_name = package_match.group(1).lower()
                normalized = self._normalize_tech_name(package_name)
                if normalized:
                    techs.add(normalized)
            
            # Check for framework indicators
            if "django" in line.lower():
                techs.add("Django")
            elif "flask" in line.lower():
                techs.add("Flask")
            elif "fastapi" in line.lower():
                techs.add("FastAPI")
            elif "tensorflow" in line.lower():
                techs.add("TensorFlow")
            elif "torch" in line.lower() or "pytorch" in line.lower():
                techs.add("PyTorch")
        
        return sorted(list(techs))
    
    def _parse_pom_xml(self, content: str) -> List[str]:
        """Parse pom.xml to extract technologies."""
        techs = set()
        
        # Look for common Java dependencies
        if "spring" in content.lower():
            techs.add("Spring")
        if "spring-boot" in content.lower():
            techs.add("Spring Boot")
        if "hibernate" in content.lower():
            techs.add("Hibernate")
        if "maven" in content.lower():
            techs.add("Maven")
        
        # Extract artifact IDs (simplified)
        artifact_pattern = r'<artifactId>([^<]+)</artifactId>'
        artifacts = re.findall(artifact_pattern, content, re.IGNORECASE)
        for artifact in artifacts:
            normalized = self._normalize_tech_name(artifact)
            if normalized:
                techs.add(normalized)
        
        return sorted(list(techs))
    
    def _parse_cargo_toml(self, content: str) -> List[str]:
        """Parse Cargo.toml to extract technologies."""
        techs = set()
        
        # Look for common Rust crates
        if "tokio" in content.lower():
            techs.add("Tokio")
        if "serde" in content.lower():
            techs.add("Serde")
        if "actix" in content.lower():
            techs.add("Actix")
        if "rocket" in content.lower():
            techs.add("Rocket")
        
        # Extract dependency names (simplified TOML parsing)
        dep_pattern = r'^\[dependencies\.([^\]]+)\]|^([a-zA-Z0-9_-]+)\s*='
        for line in content.split('\n'):
            match = re.search(dep_pattern, line)
            if match:
                dep_name = (match.group(1) or match.group(2)).strip()
                normalized = self._normalize_tech_name(dep_name)
                if normalized:
                    techs.add(normalized)
        
        return sorted(list(techs))
    
    def _parse_go_mod(self, content: str) -> List[str]:
        """Parse go.mod to extract technologies."""
        techs = set()
        
        # Look for common Go frameworks
        if "gin" in content.lower():
            techs.add("Gin")
        if "echo" in content.lower():
            techs.add("Echo")
        if "fiber" in content.lower():
            techs.add("Fiber")
        if "gorilla" in content.lower():
            techs.add("Gorilla")
        
        # Extract module names (simplified)
        require_pattern = r'require\s+([^\s]+)'
        requires = re.findall(require_pattern, content, re.IGNORECASE)
        for req in requires:
            # Extract package name (last part of path)
            package_name = req.split('/')[-1].lower()
            normalized = self._normalize_tech_name(package_name)
            if normalized:
                techs.add(normalized)
        
        return sorted(list(techs))
    
    def _parse_pyproject_toml(self, content: str) -> List[str]:
        """Parse pyproject.toml to extract technologies."""
        techs = set()
        
        # Look for common Python frameworks
        if "django" in content.lower():
            techs.add("Django")
        if "flask" in content.lower():
            techs.add("Flask")
        if "fastapi" in content.lower():
            techs.add("FastAPI")
        if "pytest" in content.lower():
            techs.add("pytest")
        
        # Extract dependencies (simplified TOML parsing)
        dep_pattern = r'^([a-zA-Z0-9_-]+)\s*='
        in_deps = False
        for line in content.split('\n'):
            if '[project.dependencies]' in line.lower() or '[tool.poetry.dependencies]' in line.lower():
                in_deps = True
                continue
            if in_deps and line.strip().startswith('['):
                in_deps = False
                continue
            if in_deps:
                match = re.search(dep_pattern, line)
                if match:
                    dep_name = match.group(1).lower()
                    normalized = self._normalize_tech_name(dep_name)
                    if normalized:
                        techs.add(normalized)
        
        return sorted(list(techs))
    
    def _normalize_tech_name(self, name: str) -> Optional[str]:
        """Normalize technology name using mappings.
        
        Args:
            name: Raw technology/package name
            
        Returns:
            Normalized technology name, or None if not a recognized tech
        """
        name_lower = name.lower()
        
        # Check direct mappings
        if name_lower in self.TECH_MAPPINGS:
            return self.TECH_MAPPINGS[name_lower]
        
        # Check if name contains a mapped tech
        for key, value in self.TECH_MAPPINGS.items():
            if key in name_lower:
                return value
        
        # Capitalize first letter for common patterns
        if name_lower in ["python", "javascript", "typescript", "java", "go", "rust", "c++", "c#"]:
            return name.capitalize()
        
        # For other packages, return None (not a major tech)
        # Only return well-known technologies
        return None
