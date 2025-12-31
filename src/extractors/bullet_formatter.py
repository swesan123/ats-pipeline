"""AI-powered bullet formatter for resume bullets."""

import json
import os
from typing import List, Optional
from openai import OpenAI


class BulletFormatter:
    """Format raw project bullets into professional resume bullets using AI."""
    
    # Example bullets from user's resume template
    EXAMPLE_BULLETS = [
        "Built a convolutional neural network classifier in Python using TensorFlow.",
        "Applied preprocessing, augmentation, and splitting using NumPy and pandas.",
        "Evaluated accuracy, precision, recall, and confusion matrices using scikit-learn and Matplotlib.",
        "Trained SVM models in Python using scikit-learn to classify flare intensity.",
        "Improved accuracy through feature scaling and hyperparameter tuning using NumPy and pandas.",
        "Visualized ROC/PR curves and confusion matrices with Matplotlib.",
        "Implemented a feedforward neural network in PyTorch with two hidden layers.",
        "Applied early stopping, mini-batch SGD, dropout, and L1/L2 regularization using NumPy and scikit-learn.",
        "Plotted training/validation loss trends using Matplotlib.",
        "Developing a mobile ride-share application using React Native and TypeScript.",
        "Built backend APIs using Node.js, tRPC, and PostgreSQL.",
        "Implemented user authentication with JWT and styled UI using Tailwind.",
    ]
    
    BULLET_STRUCTURE = """
Resume bullets must follow this structure:
1. Start with a strong action verb (Built, Developed, Implemented, Trained, Applied, Evaluated, Created, Designed, etc.)
2. Be a complete sentence (subject + verb + object)
3. Include specific technologies/tools used (naturally integrated, not listed)
4. Show what was accomplished (what was built/created/improved)
5. Optionally include impact/metrics if relevant
6. Be concise (one sentence, typically 15-25 words)
7. Use past tense for completed projects, present tense for ongoing projects
8. Be professional and technical

Examples of GOOD bullets:
- "Built a convolutional neural network classifier in Python using TensorFlow."
- "Applied preprocessing, augmentation, and splitting using NumPy and pandas."
- "Evaluated accuracy, precision, recall, and confusion matrices using scikit-learn and Matplotlib."
- "Trained SVM models in Python using scikit-learn to classify flare intensity."
- "Built backend APIs using Node.js, tRPC, and PostgreSQL."

Examples of BAD bullets (to avoid):
- "CNN training on two datasets" (not a sentence, no action verb)
- "Behavior of training vs validation loss curves" (not a sentence, descriptive not action-oriented)
- "Conv1: 1 → 10 filters (3×3)" (too technical, not a sentence)
- "Overfitting and underfitting patterns" (not a sentence, no action)
"""
    
    def __init__(self):
        """Initialize bullet formatter."""
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
    
    def format_bullets(
        self,
        raw_bullets: List[str],
        project_name: str,
        tech_stack: List[str],
        description: Optional[str] = None,
    ) -> List[str]:
        """Format raw bullets into professional resume bullets.
        
        Args:
            raw_bullets: Raw bullet points from README or project description
            project_name: Name of the project
            tech_stack: List of technologies used
            description: Optional project description for context
            
        Returns:
            List of formatted resume bullets
        """
        if not raw_bullets:
            return []
        
        if not self.client:
            # Fallback: basic formatting without AI
            return self._format_bullets_fallback(raw_bullets, tech_stack)
        
        try:
            return self._format_bullets_ai(raw_bullets, project_name, tech_stack, description)
        except Exception:
            # Fallback on error
            return self._format_bullets_fallback(raw_bullets, tech_stack)
    
    def _format_bullets_ai(
        self,
        raw_bullets: List[str],
        project_name: str,
        tech_stack: List[str],
        description: Optional[str] = None,
    ) -> List[str]:
        """Format bullets using AI."""
        
        tech_stack_str = ", ".join(tech_stack) if tech_stack else "various technologies"
        description_text = f"\nProject Description: {description}" if description else ""
        
        prompt = f"""You are formatting project bullets for a professional resume. Convert the raw bullet points below into well-formatted resume bullets.

{self.BULLET_STRUCTURE}

Project Name: {project_name}
Technologies Used: {tech_stack_str}
{description_text}

Raw Bullets to Format:
{chr(10).join(f"- {bullet}" for bullet in raw_bullets[:15])}

Format each bullet point following the structure above. Convert technical details, feature lists, and descriptions into action-oriented resume bullets.

Return a JSON object with a "bullets" array containing the formatted bullets:
{{"bullets": ["bullet 1", "bullet 2", "bullet 3", ...]}}

Requirements:
- Each bullet must be a complete sentence starting with an action verb
- Include relevant technologies naturally in the sentence
- Maximum 5-6 bullets (prioritize the most impactful ones)
- Each bullet should be 15-25 words
- Use past tense for completed projects
"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional resume writer specializing in technical resumes. Format bullets to be concise, action-oriented, and professional.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            
            # Extract bullets from response - try different possible keys
            bullets = None
            if isinstance(result, dict):
                for key in ["bullets", "formatted_bullets", "resume_bullets", "output", "formatted"]:
                    if key in result:
                        value = result[key]
                        if isinstance(value, list):
                            bullets = value
                            break
            
            if bullets and isinstance(bullets, list):
                # Filter out empty strings and ensure all are strings, remove markdown
                formatted = []
                for b in bullets[:6]:  # Limit to 6
                    if b:
                        bullet_text = str(b).strip()
                        # Remove markdown formatting if present
                        bullet_text = bullet_text.replace('**', '').replace('*', '').replace('`', '')
                        if bullet_text and len(bullet_text) > 10:  # Minimum meaningful length
                            # Ensure it ends with period
                            if not bullet_text.endswith('.'):
                                bullet_text += '.'
                            formatted.append(bullet_text)
                
                if formatted:
                    return formatted
        except Exception:
            pass
        
        # Fallback if parsing fails
        return self._format_bullets_fallback(raw_bullets, tech_stack)
    
    def _format_bullets_fallback(
        self,
        raw_bullets: List[str],
        tech_stack: List[str],
    ) -> List[str]:
        """Fallback formatting without AI - basic improvements."""
        formatted = []
        action_verbs = [
            "Built", "Developed", "Implemented", "Created", "Designed", "Trained",
            "Applied", "Evaluated", "Improved", "Optimized", "Integrated", "Deployed"
        ]
        
        tech_stack_lower = [t.lower() for t in tech_stack]
        
        for bullet in raw_bullets[:6]:
            bullet = bullet.strip()
            if not bullet:
                continue
            
            # Skip if it's too short or looks like a configuration
            if len(bullet) < 15 or "→" in bullet or ":" in bullet and len(bullet.split(":")) == 2:
                continue
            
            # Check if it already starts with an action verb
            starts_with_verb = any(bullet.startswith(verb) for verb in action_verbs)
            
            if not starts_with_verb:
                # Try to add an action verb
                bullet_lower = bullet.lower()
                if "train" in bullet_lower or "model" in bullet_lower:
                    bullet = f"Trained {bullet.lower()}"
                elif "build" in bullet_lower or "create" in bullet_lower:
                    bullet = f"Built {bullet.lower()}"
                elif "implement" in bullet_lower:
                    bullet = f"Implemented {bullet.lower()}"
                elif "evaluat" in bullet_lower or "test" in bullet_lower:
                    bullet = f"Evaluated {bullet.lower()}"
                elif "visualiz" in bullet_lower or "plot" in bullet_lower:
                    bullet = f"Visualized {bullet.lower()}"
                else:
                    bullet = f"Developed {bullet.lower()}"
            
            # Ensure it's a sentence (ends with period)
            if not bullet.endswith('.'):
                bullet += '.'
            
            # Capitalize first letter
            bullet = bullet[0].upper() + bullet[1:] if len(bullet) > 1 else bullet.upper()
            
            formatted.append(bullet)
        
        return formatted[:6]
