"""Shared utility for categorizing skills."""

from typing import Dict, List, Set, Optional
import json
import time


def _normalize_skill_name(skill: str) -> str:
    """Normalize skill name for deduplication.
    
    Args:
        skill: Raw skill name
        
    Returns:
        Normalized skill name (title case for most, preserve special cases)
    """
    if not skill or not skill.strip():
        return ""
    
    skill = skill.strip()
    
    # Clean up common LaTeX / formatting artifacts before any further processing.
    # This prevents tokens like "\textbf{python" or "Scikit-learn}" from
    # leaking into the skills section and breaking deduplication.
    # Handle various LaTeX artifact patterns:
    # - \textbf{...} or \textbf{... (missing closing brace)
    # - ...} (trailing brace)
    # - {... (leading brace without \textbf)
    # - {react Native (leading brace with space)
    
    # Strip \textbf{ wrapper (with or without closing brace)
    if skill.startswith("\\textbf{"):
        skill = skill[len("\\textbf{") :].strip()
    
    # Strip leading brace if present (handles cases like "{react Native")
    if skill.startswith("{"):
        skill = skill[1:].strip()
    
    # Strip trailing brace if present (handles cases like "Scikit-learn}")
    if skill.endswith("}"):
        skill = skill[:-1].strip()
    
    # Final cleanup - remove any remaining braces
    skill = skill.replace("{", "").replace("}", "").strip()
    
    # Handle special cases that should preserve their casing
    special_cases = {
        "c++": "C++",
        "c#": "C#",
        "f#": "F#",
        "r": "R",
        "ai/ml": "AI/ML",
        "hpc": "HPC",
        "api": "API",
        "rest": "REST",
        "graphql": "GraphQL",
        "jwt": "JWT",
        "oauth": "OAuth",
        "saml": "SAML",
        "ssl": "SSL",
        "tls": "TLS",
        "vpn": "VPN",
        "ci/cd": "CI/CD",
        "iac": "IAC",
        "iaas": "IaaS",
        "paas": "PaaS",
        "saas": "SaaS",
        "sql": "SQL",
        "nosql": "NoSQL",
        "tcp/ip": "TCP/IP",
        "http": "HTTP",
        "https": "HTTPS",
        "dns": "DNS",
        "bgp": "BGP",
        "evpn": "EVPN",
        "rdma": "RDMA",
        "roce": "RoCE",
        "k8s": "K8s",
        "cncf": "CNCF",
        "helm": "Helm",
        "ncc": "NCCL",
        "gpu": "GPU",
        "cpu": "CPU",
        "fpga": "FPGA",
        "asic": "ASIC",
        "rtl": "RTL",
        "hdl": "HDL",
        "uvm": "UVM",
        "sv": "SystemVerilog",
        "vhdl": "VHDL",
        "trpc": "tRPC",
        "node.js": "Node.js",
        "nodejs": "Node.js",
        "react native": "React Native",
        "react-native": "React Native",
        "reactnavigation": "React Navigation",
        "react navigation": "React Navigation",
        "nativewind": "NativeWind",
        "tailwind": "Tailwind",
        "scikit-learn": "Scikit-learn",
        "scikit": "Scikit-learn",
        "tensorflow": "TensorFlow",
        "pytorch": "PyTorch",
        "numpy": "NumPy",
        "pandas": "Pandas",
        "matplotlib": "Matplotlib",
        "postgresql": "PostgreSQL",
        "drizzle": "Drizzle ORM",
        "drizzle orm": "Drizzle ORM",
    }
    
    # Handle multi-word special cases (check before single-word)
    multi_word_special_cases = {
        "react native": "React Native",
        "react-native": "React Native",
        "react navigation": "React Navigation",
        "react-navigation": "React Navigation",
        "nativewind/tailwind": "NativeWind/Tailwind",
        "nativewind tailwind": "NativeWind/Tailwind",
        "rtl design": "RTL Design",
        "digital design": "Digital Design",
        # Treat TensorFlow/Keras combos as plain TensorFlow – user does not list Keras as a separate skill
        "tensorflow/keras": "TensorFlow",
        "tensorflow keras": "TensorFlow",
        "drizzle orm": "Drizzle ORM",
    }
    
    # Check multi-word cases first
    skill_lower_multi = skill.lower().replace("-", " ").replace("_", " ").replace("/", " ")
    for pattern, normalized in multi_word_special_cases.items():
        # Require an exact match on the normalized multi-word phrase.
        # This avoids incorrect mappings for short skills like "C" where
        # the single letter appears inside longer phrases (e.g. "react native").
        if skill_lower_multi == pattern:
            return normalized
    
    skill_lower = skill.lower().strip()
    # Check exact match first (case-insensitive)
    if skill_lower in special_cases:
        return special_cases[skill_lower]
    
    # Check if skill *contains* a special case (e.g., "scikit-learn" in "scikit-learn-1.0"),
    # but only for keys longer than 2 characters to avoid mapping tiny tokens like "c".
    for key, value in special_cases.items():
        if len(key) <= 2:
            continue
        if key in skill_lower:
            # Replace the key with the normalized value, handling common casings
            return (
                skill
                .replace(key, value)
                .replace(key.upper(), value)
                .replace(key.capitalize(), value)
            )
    
    # For multi-word skills, use title case but preserve acronyms
    words = skill.split()
    normalized_words = []
    for word in words:
        word_lower = word.lower()
        if word_lower in special_cases:
            normalized_words.append(special_cases[word_lower])
        elif word.isupper() and len(word) > 1:
            # Preserve all-caps acronyms
            normalized_words.append(word)
        elif word_lower in ["and", "or", "of", "the", "a", "an", "in", "on", "at", "to", "for"]:
            # Keep small words lowercase (unless first word)
            if normalized_words:
                normalized_words.append(word_lower)
            else:
                normalized_words.append(word.capitalize())
        else:
            # Title case for regular words
            normalized_words.append(word.capitalize())
    
    return " ".join(normalized_words)


def _deduplicate_skills(skills: List[str]) -> List[str]:
    """Deduplicate skills by normalizing and comparing case-insensitively.
    
    Args:
        skills: List of skill names (may contain duplicates)
        
    Returns:
        List of unique, normalized skill names
    """
    seen = set()
    unique_skills = []
    
    # #region agent log
    with open('/home/swesan/repos/ats-pipeline/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run2","hypothesisId":"B","location":"skill_categorizer.py:167","message":"Deduplicating skills input","data":{"skills_input":skills},"timestamp":int(time.time()*1000)}) + '\n')
    # #endregion
    
    for skill in skills:
        if not skill or not skill.strip():
            continue
        
        # FIRST normalize the skill (cleans LaTeX, normalizes casing)
        normalized_skill = _normalize_skill_name(skill)
        
        # #region agent log
        with open('/home/swesan/repos/ats-pipeline/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run2","hypothesisId":"D","location":"skill_categorizer.py:185","message":"Normalized skill","data":{"original":skill,"normalized":normalized_skill},"timestamp":int(time.time()*1000)}) + '\n')
        # #endregion
        
        if not normalized_skill:
            continue
        
        # Use normalized version for comparison (lowercase)
        skill_key = normalized_skill.lower().strip()
        
        # Skip if we've seen this skill before
        if skill_key in seen:
            # #region agent log
            with open('/home/swesan/repos/ats-pipeline/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run2","hypothesisId":"B","location":"skill_categorizer.py:195","message":"Duplicate detected after normalization","data":{"skill":skill,"normalized":normalized_skill,"skill_key":skill_key},"timestamp":int(time.time()*1000)}) + '\n')
            # #endregion
            continue
        
        seen.add(skill_key)
        # Use normalized version for consistency
        unique_skills.append(normalized_skill)
    
    return unique_skills


def validate_and_clean_skills_with_openai(skills: List[str], job_skills: Optional[List[str]] = None) -> List[str]:
    """Validate and clean skills using OpenAI to ensure proper formatting.
    
    Args:
        skills: List of skill names to validate
        job_skills: Optional list of job-relevant skills for context
        
    Returns:
        List of validated and cleaned skill names
    """
    if not skills:
        return []
    
    import os
    from openai import OpenAI
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # If no API key, just return deduplicated skills
        return _deduplicate_skills(skills)
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Build prompt for validation
        skills_str = ", ".join(skills[:50])  # Limit to 50 skills for prompt
        job_context = ""
        if job_skills:
            job_context = f"\n\nJob-relevant skills for context: {', '.join(job_skills[:20])}"
        
        prompt = f"""You are a resume skills validator. Clean and normalize the following list of technical skills.

Rules:
1. Remove any LaTeX artifacts like \\textbf{{, }}, {{, }}
2. Normalize casing (Python not python, React Native not react native)
3. Remove duplicates (case-insensitive)
4. Remove non-skills like "Digital Design", "RTL Design", hardware model numbers like "MI300X/MI325X"
5. Keep only valid technical skills
6. Return a JSON array of cleaned skill names

Skills to clean:
{skills_str}{job_context}

Return JSON in format: {{"skills": ["Python", "React Native", ...]}}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a technical skills validator. Return only valid JSON with a 'skills' array."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        
        result = json.loads(response.choices[0].message.content)
        # Try multiple possible keys
        validated = result.get("skills", result.get("cleaned_skills", result.get("validated_skills", skills)))
        
        # Ensure it's a list
        if isinstance(validated, str):
            validated = [validated]
        elif not isinstance(validated, list):
            validated = list(validated) if validated else []
        
        # Final deduplication pass
        return _deduplicate_skills(validated)
        
    except Exception as e:
        # If validation fails, fall back to deduplication
        import json
        with open('/home/swesan/repos/ats-pipeline/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run3","hypothesisId":"A","location":"skill_categorizer.py:260","message":"OpenAI validation failed","data":{"error":str(e)},"timestamp":int(time.time()*1000)}) + '\n')
        return _deduplicate_skills(skills)


def categorize_skills(skills: List[str], job_skills: Optional[List[str]] = None) -> Dict[str, List[str]]:
    """Categorize skills into groups for better organization.
    
    Args:
        skills: List of skill names to categorize
        job_skills: Optional list of job-relevant skills to prioritize
    
    Returns: Dict mapping category name to list of skills (job-relevant skills first in each category)
    """
    # Define skill categories matching original resume structure
    # Languages FIRST, then others
    skill_categories = {
        # Languages FIRST (most important)
        "Languages": ["python", "java", "c++", "c#", "javascript", "typescript", "go", "golang", "rust", "ruby", "php", "r", "matlab", "swift", "kotlin", "scala", "clojure", "c", "cpp", "perl", "bash", "shell", "powershell", "sql"],
        # ML/AI (matching original structure)
        "ML/AI": ["tensorflow", "pytorch", "keras", "scikit-learn", "numpy", "pandas", "matplotlib", "seaborn", "jupyter", "machine learning", "deep learning", "neural networks", "nlp", "computer vision", "llm", "scikit"],
        # Mobile/Web (matching original structure)
        "Mobile/Web": ["react", "react native", "react-native", "expo", "react navigation", "vue", "angular", "next.js", "nuxt", "svelte", "tailwind", "nativewind", "bootstrap", "html", "css"],
        # Backend/DB (matching original structure)
        "Backend/DB": ["node.js", "nodejs", "express", "fastapi", "django", "flask", "spring", "rails", "laravel", "postgresql", "mysql", "mongodb", "redis", "cassandra", "dynamodb", "elasticsearch", "sql", "nosql", "database", "drizzle", "orm"],
        # DevOps (matching original structure)
        "DevOps": ["docker", "kubernetes", "terraform", "ansible", "jenkins", "gitlab ci", "github actions", "circleci", "ci/cd", "devops", "railway", "aws", "azure", "gcp", "cloud"],
        # Operating Systems
        "Operating Systems": ["linux", "ubuntu", "debian", "centos", "rhel", "windows", "unix", "macos"],
        # Security
        "Security": ["security", "cybersecurity", "authentication", "authorization", "encryption", "ssl/tls", "oauth", "jwt", "saml"],
        # Tools
        "Tools": ["git", "jira", "confluence", "slack", "vscode", "vim", "excel", "powerpoint", "word", "outlook", "tableau", "power bi", "splunk", "grafana", "prometheus", "datadog"],
        # Other (uncategorized)
        "Other": []
    }
    
    # First, deduplicate and normalize skills
    # Also split compound skills (e.g., "TensorFlow/Keras" -> ["TensorFlow", "Keras"])
    expanded_skills = []
    for skill in skills:
        if not skill or not skill.strip():
            continue
        # Split on "/" to handle compound skills
        if "/" in skill:
            parts = [s.strip() for s in skill.split("/")]
            expanded_skills.extend(parts)
        else:
            expanded_skills.append(skill)
    
    unique_skills = _deduplicate_skills(expanded_skills)
    
    # Normalize job skills for comparison
    job_skills_set: Set[str] = set()
    if job_skills:
        job_skills_set = {s.lower().strip() for s in job_skills if s.strip()}
    
    categorized = {category: [] for category in skill_categories.keys()}
    categorized_skills_set = set()  # Track which skills we've already categorized
    
    for skill in unique_skills:
        skill_lower = skill.lower()
        categorized_flag = False
        
        # #region agent log
        with open('/home/swesan/repos/ats-pipeline/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"skill_categorizer.py:217","message":"Categorizing skill","data":{"skill":skill,"skill_lower":skill_lower},"timestamp":int(time.time()*1000)}) + '\n')
        # #endregion
        
        # Try to match skill to a category (check more specific categories first)
        for category, patterns in skill_categories.items():
            if category == "Other":
                continue
            
            # Handle both dict format (new) and list format (old)
            if isinstance(patterns, dict):
                keywords = patterns.get("keywords", [])
                exclude = patterns.get("exclude", [])
            else:
                # Old format - list of keywords
                keywords = patterns
                exclude = []
            
            # Skip if skill contains excluded terms (unless it's a very specific match)
            if exclude and any(exc in skill_lower for exc in exclude):
                # Only skip if it's a generic match, not a specific one
                has_specific_match = any(kw == skill_lower or kw in skill_lower.split() for kw in keywords)
                if not has_specific_match:
                    continue
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                # Stricter matching: exact match or whole word match only
                skill_words = skill_lower.split()
                skill_words_with_separators = skill_lower.replace("-", " ").replace("/", " ").replace("_", " ").split()
                
                # Check for exact match
                if keyword_lower == skill_lower:
                    match = True
                # Check for whole word match (handling separators)
                elif any(word == keyword_lower for word in skill_words) or any(word == keyword_lower for word in skill_words_with_separators):
                    match = True
                # Check for compound matches (e.g., "react native" matches "react-native" or "reactnative")
                elif keyword_lower in skill_lower.replace("-", "").replace("_", "").replace("/", ""):
                    # Only match if it's a reasonable compound (not substring)
                    if len(keyword_lower) > 3:
                        match = True
                    else:
                        match = False
                else:
                    match = False
                
                # #region agent log
                if match:
                    with open('/home/swesan/repos/ats-pipeline/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"skill_categorizer.py:260","message":"Match found","data":{"skill":skill,"keyword":keyword,"category":category},"timestamp":int(time.time()*1000)}) + '\n')
                # #endregion
                
                if match:
                    # Only add if not already in this category
                    skill_key = skill.lower().strip()
                    if skill_key not in categorized_skills_set:
                        categorized[category].append(skill)
                        categorized_skills_set.add(skill_key)
                        categorized_flag = True
                    else:
                        # #region agent log
                        with open('/home/swesan/repos/ats-pipeline/.cursor/debug.log', 'a') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"skill_categorizer.py:270","message":"Duplicate skill skipped","data":{"skill":skill,"skill_key":skill_key,"category":category},"timestamp":int(time.time()*1000)}) + '\n')
                        # #endregion
                    break
            if categorized_flag:
                break
        
        # If not categorized, skip it (no "Other" category)
        if not categorized_flag:
            skill_key = skill.lower().strip()
            # #region agent log
            with open('/home/swesan/repos/ats-pipeline/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run3","hypothesisId":"E","location":"skill_categorizer.py:419","message":"Skill not categorized - skipping (no Other category)","data":{"skill":skill,"skill_key":skill_key},"timestamp":int(time.time()*1000)}) + '\n')
            # #endregion
    
    # Prioritize job-relevant skills within each category and ensure uniqueness
    if job_skills_set:
        for category, skills_list in categorized.items():
            # Separate job-relevant and non-job-relevant skills
            job_relevant = []
            non_job_relevant = []
            seen_in_category = set()
            
            for skill in skills_list:
                skill_key = skill.lower().strip()
                # Skip duplicates within category
                if skill_key in seen_in_category:
                    continue
                seen_in_category.add(skill_key)
                
                # Check if skill matches any job skill (case-insensitive, partial match)
                is_relevant = any(
                    job_skill in skill_key or skill_key in job_skill
                    for job_skill in job_skills_set
                )
                
                if is_relevant:
                    job_relevant.append(skill)
                else:
                    non_job_relevant.append(skill)
            
            # Reorder: job-relevant first, then others (alphabetically sorted)
            job_relevant.sort(key=lambda s: s.lower())
            non_job_relevant.sort(key=lambda s: s.lower())
            categorized[category] = job_relevant + non_job_relevant
    else:
        # Even without job skills, ensure uniqueness and sort
        for category, skills_list in categorized.items():
            seen_in_category = set()
            unique_list = []
            for skill in skills_list:
                skill_key = skill.lower().strip()
                if skill_key not in seen_in_category:
                    seen_in_category.add(skill_key)
                    unique_list.append(skill)
            unique_list.sort(key=lambda s: s.lower())
            categorized[category] = unique_list
    
    # Remove empty categories and maintain order (matching original structure)
    # Remove "Other" category completely
    ordered_categories = ["Languages", "ML/AI", "Mobile/Web", "Backend/DB", 
                          "DevOps", "Operating Systems", "Security", "Tools"]
    result = {}
    for cat in ordered_categories:
        if cat in categorized and categorized[cat]:
            result[cat] = categorized[cat]
    # Add any remaining categories not in the ordered list (except "Other")
    for cat, skills_list in categorized.items():
        if cat not in result and cat != "Other" and skills_list:
            result[cat] = skills_list
    
    return result

