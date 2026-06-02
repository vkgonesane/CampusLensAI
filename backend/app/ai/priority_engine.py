# backend/app/ai/priority_engine.py

from typing import Dict, Any


class PriorityEngine:
    """
    Priority engine for CampusLensAI.

    This class calculates how urgent a campus signal is.
    It combines category, sentiment, duplicate score, hotspot score,
    and reopen history into one final priority.
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
            "safety": 7
        }

    def calculate_priority(
        self,
        category: str,
        sentiment_result: Dict[str, Any],
        duplicate_score: float = 0.0,
        hotspot_score: float = 0.0,
        reopen_count: int = 0,
        repeated_issue_count: int = 0
    ) -> Dict[str, Any]:
        """
        Calculate final priority for a campus signal.

        Args:
            category: AI predicted category.
            sentiment_result: Output from sentiment.py.
            duplicate_score: Similarity score from duplicate detection.
            hotspot_score: Area issue density score.
            reopen_count: Number of times the issue was reopened.
            repeated_issue_count: Number of similar recent issues.

        Returns:
            Dictionary with priority label, priority score, and explanation.
        """

        score = self.category_base_scores.get(category, 2)
        reasons = []

        reasons.append(f"Base score for category '{category}' is {score}.")

        sentiment = sentiment_result.get("sentiment", "neutral")
        is_urgent = sentiment_result.get("is_urgent", False)
        is_frustrated = sentiment_result.get("is_frustrated", False)

        if sentiment == "negative":
            score += 1
            reasons.append("Negative sentiment increased priority.")

        if is_urgent:
            score += 2
            reasons.append("Urgency indicators increased priority.")

        if is_frustrated:
            score += 1
            reasons.append("Frustration or repeated complaint language increased priority.")

        if duplicate_score >= 0.75:
            score += 2
            reasons.append("High duplicate score indicates repeated reports.")

        elif duplicate_score >= 0.50:
            score += 1
            reasons.append("Moderate duplicate score indicates possible repeated issue.")

        if hotspot_score >= 0.75:
            score += 2
            reasons.append("High hotspot score indicates location-level issue cluster.")

        elif hotspot_score >= 0.50:
            score += 1
            reasons.append("Moderate hotspot score increased priority.")

        if reopen_count > 0:
            reopen_boost = min(reopen_count * 2, 4)
            score += reopen_boost
            reasons.append(f"Issue reopened {reopen_count} time(s), increasing accountability priority.")

        if repeated_issue_count > 0:
            repeated_boost = min(repeated_issue_count, 3)
            score += repeated_boost
            reasons.append(f"{repeated_issue_count} repeated issue(s) found, increasing urgency.")

        priority = self._score_to_priority(score)

        return {
            "priority": priority,
            "priority_score": round(score, 2),
            "explanation": " ".join(reasons)
        }

    def _score_to_priority(self, score: float) -> str:
        """
        Convert numeric score into readable priority label.
        """

        if score >= 10:
            return "critical"
        elif score >= 7:
            return "high"
        elif score >= 4:
            return "medium"
        else:
            return "low"


priority_engine = PriorityEngine()


def calculate_priority(
    category: str,
    sentiment_result: Dict[str, Any],
    duplicate_score: float = 0.0,
    hotspot_score: float = 0.0,
    reopen_count: int = 0,
    repeated_issue_count: int = 0
) -> Dict[str, Any]:
    """
    Public function used by ai_service.py.
    """

    return priority_engine.calculate_priority(
        category=category,
        sentiment_result=sentiment_result,
        duplicate_score=duplicate_score,
        hotspot_score=hotspot_score,
        reopen_count=reopen_count,
        repeated_issue_count=repeated_issue_count
    )