# backend/app/ai/hotspot_detector.py

from typing import Any, Dict, List, Optional


def calculate_hotspot_score(location_signal_count: int) -> float:
    """
    Backend-compatible hotspot score function.

    Existing backend ai_service.py depends on this simple count-based function.
    """
    try:
        count = int(location_signal_count or 0)
    except Exception:
        count = 0

    if count >= 10:
        return 1.0

    if count >= 7:
        return 0.8

    if count >= 5:
        return 0.6

    if count >= 3:
        return 0.4

    return 0.1


def _get_value(item: Any, key: str, default: Any = None) -> Any:
    if item is None:
        return default

    if isinstance(item, dict):
        return item.get(key, default)

    return getattr(item, key, default)


class HotspotDetector:
    """
    Enhanced hotspot detector for CampusLensAI.

    Keeps Ayush's richer hotspot logic while preserving the old backend
    calculate_hotspot_score() helper above.
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
            "water",
        }

    def detect_hotspot(
        self,
        new_location: Optional[str],
        new_category: str = "general",
        recent_signals: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        if not new_location or not str(new_location).strip():
            return self._empty_result("No location provided.")

        recent_signals = recent_signals or []

        if not recent_signals:
            return self._empty_result("No recent signals available.")

        same_location_count = 0
        same_category_count = 0
        unresolved_count = 0
        related_signal_ids = []

        normalized_new_location = self._normalize_location(str(new_location))

        for signal in recent_signals:
            old_location = _get_value(signal, "location")
            old_category = _get_value(signal, "category")
            old_status = str(_get_value(signal, "status", "open") or "open")
            old_id = _get_value(signal, "id")

            if not old_location:
                continue

            same_location = (
                self._normalize_location(str(old_location))
                == normalized_new_location
            )

            if not same_location:
                continue

            same_location_count += 1
            related_signal_ids.append(old_id)

            if str(old_category).lower().strip() == str(new_category).lower().strip():
                same_category_count += 1

            if old_status.lower() not in ["resolved", "closed", "rejected"]:
                unresolved_count += 1

        hotspot_score = self._calculate_hotspot_score(
            same_location_count=same_location_count,
            same_category_count=same_category_count,
            unresolved_count=unresolved_count,
            category=new_category,
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
                unresolved_count=unresolved_count,
            ),
        }

    def _calculate_hotspot_score(
        self,
        same_location_count: int,
        same_category_count: int,
        unresolved_count: int,
        category: str,
    ) -> float:
        score = 0.0

        score += min(same_location_count * self.same_location_weight, 0.45)
        score += min(same_category_count * self.same_category_weight, 0.30)
        score += min(unresolved_count * self.unresolved_weight, 0.25)

        if str(category).lower().strip() in self.critical_categories:
            score += self.critical_category_weight

        return round(min(float(score), 1.0), 3)

    def _normalize_location(self, location: str) -> str:
        return location.lower().strip()

    def _generate_explanation(
        self,
        is_hotspot: bool,
        hotspot_score: float,
        same_location_count: int,
        same_category_count: int,
        unresolved_count: int,
    ) -> str:
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
        return {
            "is_hotspot": False,
            "hotspot_score": 0.0,
            "same_location_count": 0,
            "same_category_count": 0,
            "unresolved_count": 0,
            "related_signal_ids": [],
            "explanation": explanation,
        }


_hotspot_detector_instance: Optional[HotspotDetector] = None


def _get_hotspot_detector() -> HotspotDetector:
    global _hotspot_detector_instance

    if _hotspot_detector_instance is None:
        _hotspot_detector_instance = HotspotDetector()

    return _hotspot_detector_instance


def detect_hotspot(
    new_location: Optional[str],
    new_category: str = "general",
    recent_signals: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """
    Enhanced public function used by Ayush-style AI service code.
    """
    return _get_hotspot_detector().detect_hotspot(
        new_location=new_location,
        new_category=new_category,
        recent_signals=recent_signals or [],
    )