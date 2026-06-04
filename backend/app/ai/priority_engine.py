# backend/app/ai/priority_engine.py

from typing import Any, Dict, Optional


URGENT_WORDS = [
    "dangerous",
    "unsafe",
    "fire",
    "electric shock",
    "harassment",
    "emergency",
    "critical",
    "risk",
    "threat",
    "accident",
    "injury",
    "spark",
]

HIGH_WORDS = [
    "broken",
    "not working",
    "leak",
    "urgent",
    "blocked",
    "dirty",
    "overflowing",
    "no water",
    "power cut",
]


class PriorityEngine:
    """
    Priority engine for CampusLensAI.

    Supports both:
    1. Vaibhav backend-compatible priority calculation.
    2. Ayush richer AI priority calculation.
    """

    def __init__(self):
        self.category_base_scores = {
            "general": 2,
            "infrastructure": 4,
            "it_issue": 4,
            "sanitation": 4,
            "equipment": 4,
            "water": 5,
            "electrical": 6,
            "safety": 7,
        }

    def calculate_backend_priority(
        self,
        description: str,
        reopen_count: int = 0,
        duplicate_score: float = 0.0,
        hotspot_score: float = 0.0,
    ) -> str:
        """
        Original backend-compatible priority function.

        Returns only:
            "medium" | "high" | "urgent"

        Kept because existing backend services expect a string.
        """
        text = (description or "").lower()

        if reopen_count >= 2:
            return "urgent"

        if reopen_count == 1:
            return "high"

        if duplicate_score > 0.8:
            return "high"

        if hotspot_score > 0.7:
            return "high"

        if any(word in text for word in URGENT_WORDS):
            return "urgent"

        if any(word in text for word in HIGH_WORDS):
            return "high"

        return "medium"

    def calculate_ai_priority(
        self,
        category: str = "general",
        sentiment_result: Optional[Dict[str, Any]] = None,
        duplicate_score: float = 0.0,
        hotspot_score: float = 0.0,
        reopen_count: int = 0,
        repeated_issue_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Ayush-style richer priority function.

        Returns:
            {
                "priority": str,
                "priority_score": float,
                "explanation": str
            }
        """
        sentiment_result = sentiment_result or {}

        score = self.category_base_scores.get(category or "general", 2)
        reasons = [f"Base score for category '{category}' is {score}."]

        sentiment = sentiment_result.get("sentiment", "neutral")
        is_urgent = bool(sentiment_result.get("is_urgent", False))
        is_frustrated = bool(sentiment_result.get("is_frustrated", False))

        if sentiment == "negative":
            score += 1
            reasons.append("Negative sentiment increased priority.")

        if is_urgent:
            score += 2
            reasons.append("Urgency indicators increased priority.")

        if is_frustrated:
            score += 1
            reasons.append("Frustration or repeated complaint language increased priority.")

        if duplicate_score >= 0.85:
            score += 2
            reasons.append("Very high duplicate score indicates repeated reports.")
        elif duplicate_score >= 0.65:
            score += 1
            reasons.append("Moderate duplicate score indicates possible repeated issue.")

        if hotspot_score >= 0.85:
            score += 2
            reasons.append("Strong hotspot detected at this location.")
        elif hotspot_score >= 0.60:
            score += 1
            reasons.append("Possible hotspot detected at this location.")

        if reopen_count > 0:
            reopen_boost = min(reopen_count * 2, 4)
            score += reopen_boost
            reasons.append(
                f"Issue reopened {reopen_count} time(s), increasing accountability priority."
            )

        if repeated_issue_count > 0:
            repeated_boost = min(repeated_issue_count, 3)
            score += repeated_boost
            reasons.append(
                f"{repeated_issue_count} repeated issue(s) found, increasing urgency."
            )

        priority = self._score_to_priority(score)

        return {
            "priority": priority,
            "priority_score": round(float(score), 2),
            "explanation": " ".join(reasons),
        }

    def _score_to_priority(self, score: float) -> str:
        if score >= 12:
            return "critical"

        if score >= 8:
            return "high"

        if score >= 4:
            return "medium"

        return "low"


_priority_engine_instance: Optional[PriorityEngine] = None


def _get_priority_engine() -> PriorityEngine:
    global _priority_engine_instance

    if _priority_engine_instance is None:
        _priority_engine_instance = PriorityEngine()

    return _priority_engine_instance


def calculate_priority(*args, **kwargs):
    """
    Public priority function.

    Supports old backend style:
        calculate_priority(
            description="...",
            reopen_count=0,
            duplicate_score=0.0,
            hotspot_score=0.0
        ) -> str

    Supports Ayush AI style:
        calculate_priority(
            category="safety",
            sentiment_result={...},
            duplicate_score=0.0,
            hotspot_score=0.0,
            reopen_count=0,
            repeated_issue_count=0
        ) -> dict
    """
    engine = _get_priority_engine()

    # Old positional backend style:
    # calculate_priority(description, reopen_count, duplicate_score, hotspot_score)
    if args and isinstance(args[0], str) and "category" not in kwargs:
        return engine.calculate_backend_priority(
            description=args[0],
            reopen_count=args[1] if len(args) > 1 else kwargs.get("reopen_count", 0),
            duplicate_score=args[2] if len(args) > 2 else kwargs.get("duplicate_score", 0.0),
            hotspot_score=args[3] if len(args) > 3 else kwargs.get("hotspot_score", 0.0),
        )

    # Old keyword backend style used by merged ai_service.py.
    if "description" in kwargs and "category" not in kwargs:
        return engine.calculate_backend_priority(
            description=kwargs.get("description", ""),
            reopen_count=kwargs.get("reopen_count", 0),
            duplicate_score=kwargs.get("duplicate_score", 0.0),
            hotspot_score=kwargs.get("hotspot_score", 0.0),
        )

    # New Ayush AI style.
    return engine.calculate_ai_priority(
        category=kwargs.get("category", "general"),
        sentiment_result=kwargs.get("sentiment_result", {}),
        duplicate_score=kwargs.get("duplicate_score", 0.0),
        hotspot_score=kwargs.get("hotspot_score", 0.0),
        reopen_count=kwargs.get("reopen_count", 0),
        repeated_issue_count=kwargs.get("repeated_issue_count", 0),
    )