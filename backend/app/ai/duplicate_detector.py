# backend/app/ai/duplicate_detector.py

from typing import List, Dict, Any, Optional

from app.ai.embedding_service import calculate_similarity


class DuplicateDetector:
    """
    Duplicate detector for CampusLensAI.

    This class checks whether a new campus signal is similar to
    previously submitted signals.
    """

    def __init__(self):
        self.high_similarity_threshold = 0.65
        self.moderate_similarity_threshold = 0.40

    def detect_duplicate(
        self,
        new_signal_text: str,
        new_category: str,
        new_location: Optional[str],
        existing_signals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect duplicate or repeated campus signals.

        Args:
            new_signal_text:
                Text of the newly submitted signal.

            new_category:
                AI category of the new signal.

            new_location:
                Location of the new signal.

            existing_signals:
                List of previous signals.
                Each signal should look like:

                {
                    "id": 1,
                    "text": "WiFi is not working in Block A",
                    "category": "it_issue",
                    "location": "Block A",
                    "status": "open"
                }

        Returns:
            Dictionary containing duplicate status, score,
            matched signal, and repeated issue count.
        """

        if not new_signal_text or not new_signal_text.strip():
            return self._empty_result()

        if not existing_signals:
            return self._empty_result()

        best_match = None
        best_score = 0.0
        repeated_issue_count = 0
        possible_matches = []

        for signal in existing_signals:
            old_text = signal.get("text", "")
            old_category = signal.get("category", "")
            old_location = signal.get("location", "")
            old_status = str(signal.get("status", "open") or "open")

            if not old_text:
                continue

            similarity = calculate_similarity(new_signal_text, old_text)

            same_category = self._is_same_category(
                new_category,
                old_category
            )

            same_location = self._is_same_location(
                new_location,
                old_location
            )

            is_unresolved = old_status.lower() not in [
                "resolved",
                "closed",
                "rejected"
            ]

            duplicate_likelihood = self._calculate_duplicate_likelihood(
                similarity=similarity,
                same_category=same_category,
                same_location=same_location,
                is_unresolved=is_unresolved
            )

            if duplicate_likelihood >= self.moderate_similarity_threshold:
                repeated_issue_count += 1

                possible_matches.append({
                    "signal_id": signal.get("id"),
                    "text": old_text,
                    "similarity": similarity,
                    "duplicate_likelihood": duplicate_likelihood,
                    "same_category": same_category,
                    "same_location": same_location,
                    "status": old_status
                })

            if duplicate_likelihood > best_score:
                best_score = duplicate_likelihood
                best_match = signal

        is_duplicate = best_score >= self.high_similarity_threshold

        return {
            "is_duplicate": is_duplicate,
            "duplicate_score": round(best_score, 3),
            "matched_signal_id": best_match.get("id") if best_match else None,
            "matched_signal": best_match,
            "repeated_issue_count": repeated_issue_count,
            "possible_matches": possible_matches,
            "explanation": self._generate_explanation(
                is_duplicate=is_duplicate,
                duplicate_score=best_score,
                repeated_issue_count=repeated_issue_count
            )
        }

    def _calculate_duplicate_likelihood(
        self,
        similarity: float,
        same_category: bool,
        same_location: bool,
        is_unresolved: bool
    ) -> float:
        """
        Combine semantic similarity with category, location,
        and unresolved status.
        """

        score = similarity

        if same_category:
            score += 0.15

        if same_location:
            score += 0.20

        if is_unresolved:
            score += 0.10

        return min(score, 1.0)

    def _is_same_category(
        self,
        new_category: str,
        old_category: str
    ) -> bool:
        """
        Check if two signals belong to the same category.
        """

        if not new_category or not old_category:
            return False

        return new_category.lower() == old_category.lower()

    def _is_same_location(
        self,
        new_location: Optional[str],
        old_location: Optional[str]
    ) -> bool:
        """
        Simple MVP location matching.

        Later this can be improved using geolocation distance,
        building IDs, room numbers, or map coordinates.
        """

        if not new_location or not old_location:
            return False

        return new_location.lower().strip() == old_location.lower().strip()

    def _generate_explanation(
        self,
        is_duplicate: bool,
        duplicate_score: float,
        repeated_issue_count: int
    ) -> str:
        """
        Generate explanation for debugging and demo clarity.
        """

        if is_duplicate:
            return (
                f"Likely duplicate detected with score "
                f"{round(duplicate_score, 3)}. "
                f"{repeated_issue_count} similar unresolved/recent issue(s) found."
            )

        if repeated_issue_count > 0:
            return (
                f"No strong duplicate found, but "
                f"{repeated_issue_count} related issue(s) were detected."
            )

        return "No duplicate or repeated issue detected."

    def _empty_result(self) -> Dict[str, Any]:
        """
        Default result when no comparison can be made.
        """

        return {
            "is_duplicate": False,
            "duplicate_score": 0.0,
            "matched_signal_id": None,
            "matched_signal": None,
            "repeated_issue_count": 0,
            "possible_matches": [],
            "explanation": "No existing signals available for duplicate comparison."
        }


duplicate_detector = DuplicateDetector()


def detect_duplicate(
    new_signal_text: str,
    new_category: str,
    new_location: Optional[str],
    existing_signals: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Public function used by ai_service.py.
    """

    return duplicate_detector.detect_duplicate(
        new_signal_text=new_signal_text,
        new_category=new_category,
        new_location=new_location,
        existing_signals=existing_signals
    )