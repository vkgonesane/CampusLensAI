# backend/app/ai/duplicate_detector.py

from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional


def calculate_text_similarity(text_one: str, text_two: str) -> float:
    """
    Lightweight fallback text similarity.

    This must remain dependency-free so duplicate detection works even if
    sentence-transformers/torch are unavailable.
    """
    text_one = (text_one or "").lower().strip()
    text_two = (text_two or "").lower().strip()

    if not text_one or not text_two:
        return 0.0

    similarity = SequenceMatcher(None, text_one, text_two).ratio()
    return round(float(similarity), 2)


def _safe_semantic_similarity(text_one: str, text_two: str) -> float:
    """
    Try Ayush's embedding similarity first.
    Fall back to difflib if heavy AI dependencies/models fail.
    """
    try:
        from app.ai.embedding_service import calculate_similarity

        score = calculate_similarity(text_one, text_two)
        return round(float(score), 3)
    except Exception:
        return calculate_text_similarity(text_one, text_two)


def _get_value(item: Any, key: str, default: Any = None) -> Any:
    """
    Read values from either dicts or SQLAlchemy/Pydantic-style objects.
    """
    if item is None:
        return default

    if isinstance(item, dict):
        return item.get(key, default)

    return getattr(item, key, default)


def _get_signal_text(signal: Any) -> str:
    """
    Supports multiple possible signal shapes.
    Backend SQLAlchemy object usually has .description.
    Ayush's AI dictionaries usually use "text".
    """
    return (
        _get_value(signal, "description")
        or _get_value(signal, "text")
        or _get_value(signal, "title")
        or ""
    )


def detect_duplicate_score(
    current_description: str,
    previous_descriptions: list[str],
) -> float:
    """
    Backend-compatible duplicate score function.

    Required by existing ai_service.py contract.
    """
    highest_score = 0.0

    for old_description in previous_descriptions or []:
        similarity = _safe_semantic_similarity(
            current_description,
            old_description,
        )

        if similarity > highest_score:
            highest_score = similarity

    return round(float(highest_score), 2)


def find_best_duplicate_match(
    current_description: str,
    previous_signals: list,
):
    """
    Backend-compatible duplicate match function.

    IMPORTANT:
    Existing signal creation code may call this and expect:
        {
            "score": float,
            "matched_signal": signal_object_or_none
        }

    So we preserve that exact return shape.
    """
    best_score = 0.0
    best_signal = None

    for signal in previous_signals or []:
        old_description = _get_signal_text(signal)

        if not old_description:
            continue

        similarity = _safe_semantic_similarity(
            current_description,
            old_description,
        )

        if similarity > best_score:
            best_score = similarity
            best_signal = signal

    return {
        "score": round(float(best_score), 2),
        "matched_signal": best_signal,
    }


class DuplicateDetector:
    """
    Enhanced duplicate detector for AI-internal use.

    This keeps Ayush's richer duplicate logic while preserving the backend's
    old public helper functions above.
    """

    def __init__(self):
        self.high_similarity_threshold = 0.65
        self.moderate_similarity_threshold = 0.40

    def detect_duplicate(
        self,
        new_signal_text: str,
        new_category: str = "general",
        new_location: Optional[str] = None,
        existing_signals: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        if not new_signal_text or not new_signal_text.strip():
            return self._empty_result("No valid signal text provided.")

        existing_signals = existing_signals or []

        if not existing_signals:
            return self._empty_result(
                "No existing signals available for duplicate comparison."
            )

        best_match = None
        best_score = 0.0
        repeated_issue_count = 0
        possible_matches = []

        for signal in existing_signals:
            old_text = _get_signal_text(signal)
            old_category = _get_value(signal, "category", "")
            old_location = _get_value(signal, "location", None)
            old_status = str(_get_value(signal, "status", "open") or "open")

            if not old_text:
                continue

            similarity = _safe_semantic_similarity(new_signal_text, old_text)

            same_category = self._is_same_category(
                new_category,
                old_category,
            )

            same_location = self._is_same_location(
                new_location,
                old_location,
            )

            is_unresolved = old_status.lower() not in [
                "resolved",
                "closed",
                "rejected",
            ]

            duplicate_likelihood = self._calculate_duplicate_likelihood(
                similarity=similarity,
                same_category=same_category,
                same_location=same_location,
                is_unresolved=is_unresolved,
            )

            if duplicate_likelihood >= self.moderate_similarity_threshold:
                repeated_issue_count += 1

                possible_matches.append(
                    {
                        "signal_id": _get_value(signal, "id"),
                        "text": old_text,
                        "similarity": round(float(similarity), 3),
                        "duplicate_likelihood": round(
                            float(duplicate_likelihood),
                            3,
                        ),
                        "same_category": same_category,
                        "same_location": same_location,
                        "status": old_status,
                    }
                )

            if duplicate_likelihood > best_score:
                best_score = duplicate_likelihood
                best_match = signal

        is_duplicate = best_score >= self.high_similarity_threshold

        return {
            "is_duplicate": is_duplicate,
            "duplicate_score": round(float(best_score), 3),
            "matched_signal_id": _get_value(best_match, "id"),
            "matched_signal": best_match,
            "repeated_issue_count": repeated_issue_count,
            "possible_matches": possible_matches,
            "explanation": self._generate_explanation(
                is_duplicate=is_duplicate,
                duplicate_score=best_score,
                repeated_issue_count=repeated_issue_count,
            ),
        }

    def _calculate_duplicate_likelihood(
        self,
        similarity: float,
        same_category: bool,
        same_location: bool,
        is_unresolved: bool,
    ) -> float:
        score = float(similarity or 0.0)

        if same_category:
            score += 0.15

        if same_location:
            score += 0.20

        if is_unresolved:
            score += 0.10

        return min(score, 1.0)

    def _is_same_category(
        self,
        new_category: Optional[str],
        old_category: Optional[str],
    ) -> bool:
        if not new_category or not old_category:
            return False

        return str(new_category).lower().strip() == str(old_category).lower().strip()

    def _is_same_location(
        self,
        new_location: Optional[str],
        old_location: Optional[str],
    ) -> bool:
        if not new_location or not old_location:
            return False

        return str(new_location).lower().strip() == str(old_location).lower().strip()

    def _generate_explanation(
        self,
        is_duplicate: bool,
        duplicate_score: float,
        repeated_issue_count: int,
    ) -> str:
        if is_duplicate:
            return (
                f"Likely duplicate detected with score "
                f"{round(float(duplicate_score), 3)}. "
                f"{repeated_issue_count} similar unresolved/recent issue(s) found."
            )

        if repeated_issue_count > 0:
            return (
                f"No strong duplicate found, but "
                f"{repeated_issue_count} related issue(s) were detected."
            )

        return "No duplicate or repeated issue detected."

    def _empty_result(self, explanation: str) -> Dict[str, Any]:
        return {
            "is_duplicate": False,
            "duplicate_score": 0.0,
            "matched_signal_id": None,
            "matched_signal": None,
            "repeated_issue_count": 0,
            "possible_matches": [],
            "explanation": explanation,
        }


_duplicate_detector_instance: Optional[DuplicateDetector] = None


def _get_duplicate_detector() -> DuplicateDetector:
    """
    Lazy singleton.

    Keeps imports/startup safer and avoids doing unnecessary AI setup at module import.
    """
    global _duplicate_detector_instance

    if _duplicate_detector_instance is None:
        _duplicate_detector_instance = DuplicateDetector()

    return _duplicate_detector_instance


def detect_duplicate(
    new_signal_text: str,
    new_category: str = "general",
    new_location: Optional[str] = None,
    existing_signals: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """
    Enhanced public function used by Ayush-style AI service code.

    Safe to keep, but existing backend does not have to depend on it.
    """
    return _get_duplicate_detector().detect_duplicate(
        new_signal_text=new_signal_text,
        new_category=new_category,
        new_location=new_location,
        existing_signals=existing_signals or [],
    )