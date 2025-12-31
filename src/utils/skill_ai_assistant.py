"""AI assistant for suggesting skills and categories based on text."""

from typing import List, Optional, Dict
import os

from openai import OpenAI


class SkillAIAssistant:
    """Lightweight helper to suggest skills from job descriptions or text snippets.
    
    This never auto-adds skills; it only returns suggestions for the user to confirm.
    """

    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Running in no-AI mode; suggestions will be empty
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)

    def suggest_skills(
        self,
        text: str,
        existing_skills: Optional[List[str]] = None,
    ) -> List[Dict[str, str]]:
        """Suggest skills and categories from raw text.
        
        Returns a list of {name, category} suggestions that are NOT already in existing_skills.
        """
        if not text or not text.strip():
            return []

        existing_set = {s.lower().strip() for s in (existing_skills or [])}

        if self.client is None:
            # No API key – fail safely with no suggestions
            return []

        prompt = f"""You are a precise resume skill extraction assistant.

Given the following text (job description, resume snippet, or project description),
extract ONLY concrete technical skills that would belong on a resume's Technical Skills section.

Rules:
1. Do NOT invent or infer skills that are not clearly supported by the text.
2. Prefer atomic skills (e.g., "Python", "React Native") over vague phrases.
3. Map each skill into one of these categories:
   - Languages
   - ML/AI
   - Mobile/Web
   - Backend/DB
   - DevOps
   - Operating Systems
   - Security
   - Tools
4. Do NOT include soft skills.
5. Do NOT include skills that are already present in this existing skills list:
   {', '.join(sorted(existing_set)) if existing_set else 'None'}

Text:
{text}

Return JSON:
{{
  "skills": [
    {{"name": "Python", "category": "Languages"}},
    {{"name": "React Native", "category": "Mobile/Web"}}
  ]
}}"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You extract resume skills. Be conservative and avoid fabrication.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )

        import json

        try:
            data = json.loads(response.choices[0].message.content)
        except Exception:
            return []

        raw_skills = data.get("skills", [])
        suggestions: List[Dict[str, str]] = []
        for item in raw_skills:
            name = (item.get("name") or "").strip()
            category = (item.get("category") or "").strip() or "Other"
            if not name:
                continue
            if name.lower() in existing_set:
                continue
            suggestions.append({"name": name, "category": category})
        return suggestions


