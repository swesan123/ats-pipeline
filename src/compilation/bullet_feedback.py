"""Store and surface user feedback about bullet candidates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from src.models.resume import BulletCandidate


FEEDBACK_PATH = Path("data/bullet_feedback.json")


@dataclass
class BulletFeedbackEntry:
    action: str  # "accepted" or "rejected"
    rewrite_intent: Optional[str]
    length: int
    rating: Optional[int] = None  # 1-5 stars, None if not provided
    comment: Optional[str] = None  # user's written feedback
    rejection_reason: Optional[str] = None  # explanation when rejecting


class BulletFeedbackStore:
    """Persist simple feedback statistics for bullet generation."""

    def __init__(self, path: Path = FEEDBACK_PATH):
        self.path = path
        self._data: Dict[str, Any] = {"entries": []}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            with self.path.open("r", encoding="utf-8") as f:
                self._data = json.load(f)
        except Exception:
            self._data = {"entries": []}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def record_feedback(
        self,
        action: str,
        candidate: BulletCandidate,
        rewrite_intent: Optional[str],
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        rejection_reason: Optional[str] = None,
    ) -> None:
        """Record a single feedback event.
        
        Args:
            action: "accepted" or "rejected"
            candidate: The bullet candidate being evaluated
            rewrite_intent: The rewrite intent used (e.g., "emphasize_skills")
            rating: Optional 1-5 star rating
            comment: Optional written feedback comment
            rejection_reason: Optional reason for rejection
        """
        entry = {
            "action": action,
            "rewrite_intent": rewrite_intent,
            "length": len(candidate.text or ""),
        }
        # Add optional fields if provided
        if rating is not None:
            entry["rating"] = rating
        if comment:
            entry["comment"] = comment.strip()
        if rejection_reason:
            entry["rejection_reason"] = rejection_reason.strip()
        
        self._data.setdefault("entries", []).append(entry)
        # Keep only the last 200 entries to avoid unbounded growth
        self._data["entries"] = self._data["entries"][-200:]
        self._save()

    def preference_note(self) -> str:
        """Summarize simple preferences for use in prompts."""
        entries: List[Dict[str, Any]] = self._data.get("entries", [])
        if not entries:
            return ""

        accepted = [e for e in entries if e.get("action") == "accepted"]
        if not accepted:
            return ""

        avg_len = sum(e.get("length", 0) for e in accepted) / max(len(accepted), 1)
        intents: Dict[str, int] = {}
        for e in accepted:
            intent = e.get("rewrite_intent") or "emphasize_skills"
            intents[intent] = intents.get(intent, 0) + 1

        # Pick top intent
        top_intent = max(intents.items(), key=lambda kv: kv[1])[0] if intents else None

        note_bits = []
        note_bits.append(
            f"User tends to accept bullets around {int(avg_len)} characters long."
        )
        if top_intent:
            label_map = {
                "emphasize_skills": "emphasizing skills",
                "more_technical": "more technical detail",
                "more_concise": "being concise",
                "conservative": "minimal, conservative edits",
            }
            note_bits.append(
                f"User often prefers bullets focused on {label_map.get(top_intent, top_intent)}."
            )
        
        # Add average rating if available
        ratings = [e.get("rating") for e in accepted if e.get("rating") is not None]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            note_bits.append(
                f"User typically rates accepted bullets {avg_rating:.1f} out of 5 stars."
            )
        
        # Extract common themes from comments (simple keyword extraction)
        comments = [e.get("comment", "") for e in accepted if e.get("comment")]
        if comments:
            # Simple keyword extraction - look for common patterns
            common_words = {}
            for comment in comments:
                words = comment.lower().split()
                for word in words:
                    if len(word) > 4:  # Only meaningful words
                        common_words[word] = common_words.get(word, 0) + 1
            
            # Get top 2-3 most common meaningful words
            if common_words:
                top_words = sorted(common_words.items(), key=lambda kv: kv[1], reverse=True)[:3]
                if top_words and top_words[0][1] >= 2:  # At least mentioned twice
                    themes = [word for word, count in top_words if count >= 2]
                    if themes:
                        note_bits.append(
                            f"User feedback often mentions: {', '.join(themes[:2])}."
                        )

        return " ".join(note_bits)


