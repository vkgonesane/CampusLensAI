# backend/app/ai/hotspot_detector.py

from typing import List, Dict, Any, Optional


class HotspotDetector:
    """
    Hotspot detector for CampusLensAI.

    This class detects whether a location is becoming a repeated
    issue zone based on recent campus signals.
    """

    def __init__(self):
        self.same_location_weight = 0.15
        self.same_category_weight = 0.10
        self.unresolved_weight = 0.10
        self.critical_category_weight = 0.15

        self.hotspot_threshold = 0.60

        self.critical_categories = {
            "safety",
            "electrical",
            "water"
        }

    def detect_hotspot(
        self,
        new_location: Optional[str],
        new_category: str,
        recent_signals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect hotspot score for a new signal.

        Args:
            new_location:
                Location of the new campus signal.

            new_category:
                AI category of the new campus signal.

            recent_signals:
                Recent campus signals from database.

                Expected format:

                {
                    "id": 1,
                    "category": "sanitation",
                    "location": "Block A",
                    "status": "open"
                }

        Returns:
            Dictionary containing hotspot status, score,
            related issue count, and explanation.
        """

        if not new_location or not new_location.strip():
            return self._empty_result("No location provided.")

        if not recent_signals:
            return self._empty_result("No recent signals available.")

        same_location_count = 0
        same_category_count = 0
        unresolved_count = 0
        related_signal_ids = []

        normalized_new_location = self._normalize_location(new_location)

        for signal in recent_signals:
            old_location = signal.get("location")
            old_category = signal.get("category")
            old_status = str(signal.get("status", "open") or "open")
            old_id = signal.get("id")

            if not old_location:
                continue

            same_location = (
                self._normalize_location(old_location)
                == normalized_new_location
            )

            if not same_location:
                continue

            same_location_count += 1
            related_signal_ids.append(old_id)

            if str(old_category).lower() == str(new_category).lower():
                same_category_count += 1

            if old_status.lower() not in ["resolved", "closed", "rejected"]:
                unresolved_count += 1

        hotspot_score = self._calculate_hotspot_score(
            same_location_count=same_location_count,
            same_category_count=same_category_count,
            unresolved_count=unresolved_count,
            category=new_category
        )

        is_hotspot = hotspot_score >= self.hotspot_threshold

        return {
            "is_hotspot": is_hotspot,
            "hotspot_score": hotspot_score,
            "same_location_count": same_location_count,
            "same_category_count": same_category_count,
            "unresolved_count": unresolved_count,
            "related_signal_ids": related_signal_ids,
            "explanation": self._generate_explanation(
                is_hotspot=is_hotspot,
                hotspot_score=hotspot_score,
                same_location_count=same_location_count,
                same_category_count=same_category_count,
                unresolved_count=unresolved_count
            )
        }

    def _calculate_hotspot_score(
        self,
        same_location_count: int,
        same_category_count: int,
        unresolved_count: int,
        category: str
    ) -> float:
        """
        Convert hotspot factors into a score between 0 and 1.
        """

        score = 0.0

        score += min(same_location_count * self.same_location_weight, 0.45)
        score += min(same_category_count * self.same_category_weight, 0.30)
        score += min(unresolved_count * self.unresolved_weight, 0.25)

        if category in self.critical_categories:
            score += self.critical_category_weight

        return round(min(score, 1.0), 3)

    def _normalize_location(self, location: str) -> str:
        """
        Normalize location text for simple matching.

        Example:
        ' Block A ' -> 'block a'
        """

        return location.lower().strip()

    def _generate_explanation(
        self,
        is_hotspot: bool,
        hotspot_score: float,
        same_location_count: int,
        same_category_count: int,
        unresolved_count: int
    ) -> str:
        """
        Generate explanation for debugging and demo clarity.
        """

        if is_hotspot:
            return (
                f"Hotspot detected with score {hotspot_score}. "
                f"{same_location_count} issue(s) found at the same location, "
                f"{same_category_count} from the same category, "
                f"and {unresolved_count} unresolved."
            )

        return (
            f"No strong hotspot detected. Score {hotspot_score}. "
            f"{same_location_count} issue(s) found at the same location."
        )

    def _empty_result(self, explanation: str) -> Dict[str, Any]:
        """
        Default result when hotspot detection cannot be performed.
        """

        return {
            "is_hotspot": False,
            "hotspot_score": 0.0,
            "same_location_count": 0,
            "same_category_count": 0,
            "unresolved_count": 0,
            "related_signal_ids": [],
            "explanation": explanation
        }


hotspot_detector = HotspotDetector()


def detect_hotspot(
    new_location: Optional[str],
    new_category: str,
    recent_signals: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Public function used by ai_service.py.
    """

    return hotspot_detector.detect_hotspot(
        new_location=new_location,
        new_category=new_category,
        recent_signals=recent_signals
    )