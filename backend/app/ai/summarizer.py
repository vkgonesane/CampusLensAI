# backend/app/ai/summarizer.py

from typing import Dict, Any, List
import re


class SignalSummarizer:
    """
    Summarizer for CampusLensAI.

    This class creates short, admin-friendly summaries from
    user-submitted campus signals.
    """

    def __init__(self):
        self.important_words = [
            "not working",
            "broken",
            "damaged",
            "dirty",
            "unsafe",
            "dangerous",
            "urgent",
            "emergency",
            "leaking",
            "overflowing",
            "smell",
            "spark",
            "short circuit",
            "no water",
            "no internet",
            "wifi",
            "projector",
            "washroom",
            "toilet",
            "classroom",
            "lab",
            "hostel",
            "canteen",
            "gate"
        ]

    def summarize(
        self,
        text: str,
        category: str = "general",
        location: str | None = None
    ) -> Dict[str, Any]:
        """
        Generate a short summary for a campus signal.

        Args:
            text: User-submitted complaint text.
            category: AI-predicted category.
            location: Location of the issue, if available.

        Returns:
            Dictionary containing summary and key points.
        """

        if not text or not text.strip():
            return {
                "summary": "No valid complaint text provided.",
                "key_points": [],
                "short_title": "Invalid Signal"
            }

        cleaned_text = self._clean_text(text)
        sentences = self._split_sentences(cleaned_text)

        important_sentence = self._select_important_sentence(sentences)

        summary = self._build_summary(
            sentence=important_sentence,
            category=category,
            location=location
        )

        key_points = self._extract_key_points(
            text=cleaned_text,
            category=category,
            location=location
        )

        short_title = self._generate_short_title(
            category=category,
            location=location,
            key_points=key_points
        )

        return {
            "summary": summary,
            "key_points": key_points,
            "short_title": short_title
        }

    def _clean_text(self, text: str) -> str:
        """
        Clean extra spaces from text.
        """

        text = text.strip()
        text = re.sub(r"\s+", " ", text)

        return text

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split complaint into sentences.
        """

        sentences = re.split(r"[.!?]+", text)
        sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

        if not sentences:
            return [text]

        return sentences

    def _select_important_sentence(self, sentences: List[str]) -> str:
        """
        Pick the most important sentence based on useful issue words.
        """

        best_sentence = sentences[0]
        best_score = 0

        for sentence in sentences:
            sentence_lower = sentence.lower()
            score = 0

            for word in self.important_words:
                if word in sentence_lower:
                    score += 1

            if score > best_score:
                best_score = score
                best_sentence = sentence

        return best_sentence

    def _build_summary(
        self,
        sentence: str,
        category: str,
        location: str | None
    ) -> str:
        """
        Build a short readable summary.
        """

        sentence = sentence.strip()

        if len(sentence) > 160:
            sentence = sentence[:157].strip() + "..."

        if location:
            return f"{category.replace('_', ' ').title()} issue reported at {location}: {sentence}"

        return f"{category.replace('_', ' ').title()} issue reported: {sentence}"

    def _extract_key_points(
        self,
        text: str,
        category: str,
        location: str | None
    ) -> List[str]:
        """
        Extract simple key points from complaint.
        """

        key_points = []

        if location:
            key_points.append(f"Location: {location}")

        key_points.append(f"Category: {category.replace('_', ' ').title()}")

        text_lower = text.lower()

        matched_words = []

        for word in self.important_words:
            if word in text_lower:
                matched_words.append(word)

        for word in matched_words[:3]:
            key_points.append(f"Issue indicator: {word}")

        if not matched_words:
            key_points.append("User reported a campus issue requiring review.")

        return key_points

    def _generate_short_title(
        self,
        category: str,
        location: str | None,
        key_points: List[str]
    ) -> str:
        """
        Generate a short title for dashboard display.
        """

        readable_category = category.replace("_", " ").title()

        if location:
            return f"{readable_category} Issue - {location}"

        return f"{readable_category} Issue"


summarizer = SignalSummarizer()


def summarize_signal(
    text: str,
    category: str = "general",
    location: str | None = None
) -> Dict[str, Any]:
    """
    Public function used by ai_service.py.
    """

    return summarizer.summarize(
        text=text,
        category=category,
        location=location
    )