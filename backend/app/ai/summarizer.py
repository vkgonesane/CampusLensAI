# backend/app/ai/summarizer.py

import re
from typing import Any, Dict, List, Optional


IMPORTANT_WORDS = [
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
    "gate",
]


def generate_summary(
    title: str,
    description: str,
    location_name: Optional[str] = None,
) -> str:
    """
    Backend-compatible summary function.

    Existing backend ai_service.py depends on this returning a plain string.
    """
    safe_title = (title or "Signal").strip()
    safe_description = (description or "").strip()
    location = location_name if location_name else "unknown location"

    if not safe_description:
        return f"{safe_title} reported at {location}."

    short_description = safe_description[:120]

    suffix = "..." if len(safe_description) > 120 else ""

    return (
        f"{safe_title} reported at {location}. "
        f"Details: {short_description}{suffix}"
    )


class SignalSummarizer:
    """
    Enhanced summarizer for CampusLensAI.

    Keeps Ayush's richer dashboard-friendly summary logic while preserving
    generate_summary() above for backend compatibility.
    """

    def __init__(self):
        self.important_words = IMPORTANT_WORDS

    def summarize(
        self,
        text: str,
        category: str = "general",
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                "summary": "No valid complaint text provided.",
                "key_points": [],
                "short_title": "Invalid Signal",
            }

        cleaned_text = self._clean_text(text)
        sentences = self._split_sentences(cleaned_text)

        important_sentence = self._select_important_sentence(sentences)

        summary = self._build_summary(
            sentence=important_sentence,
            category=category,
            location=location,
        )

        key_points = self._extract_key_points(
            text=cleaned_text,
            category=category,
            location=location,
        )

        short_title = self._generate_short_title(
            category=category,
            location=location,
        )

        return {
            "summary": summary,
            "key_points": key_points,
            "short_title": short_title,
        }

    def _clean_text(self, text: str) -> str:
        text = text.strip()
        return re.sub(r"\s+", " ", text)

    def _split_sentences(self, text: str) -> List[str]:
        sentences = re.split(r"[.!?]+", text)
        sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
        return sentences or [text]

    def _select_important_sentence(self, sentences: List[str]) -> str:
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
        location: Optional[str],
    ) -> str:
        sentence = sentence.strip()

        if len(sentence) > 160:
            sentence = sentence[:157].strip() + "..."

        readable_category = (category or "general").replace("_", " ").title()

        if location:
            return f"{readable_category} issue reported at {location}: {sentence}"

        return f"{readable_category} issue reported: {sentence}"

    def _extract_key_points(
        self,
        text: str,
        category: str,
        location: Optional[str],
    ) -> List[str]:
        key_points = []

        if location:
            key_points.append(f"Location: {location}")

        readable_category = (category or "general").replace("_", " ").title()
        key_points.append(f"Category: {readable_category}")

        text_lower = text.lower()

        matched_words = [
            word
            for word in self.important_words
            if word in text_lower
        ]

        for word in matched_words[:3]:
            key_points.append(f"Issue indicator: {word}")

        if not matched_words:
            key_points.append("User reported a campus issue requiring review.")

        return key_points

    def _generate_short_title(
        self,
        category: str,
        location: Optional[str],
    ) -> str:
        readable_category = (category or "general").replace("_", " ").title()

        if location:
            return f"{readable_category} Issue - {location}"

        return f"{readable_category} Issue"


_summarizer_instance: Optional[SignalSummarizer] = None


def _get_summarizer() -> SignalSummarizer:
    global _summarizer_instance

    if _summarizer_instance is None:
        _summarizer_instance = SignalSummarizer()

    return _summarizer_instance


def summarize_signal(
    text: str,
    category: str = "general",
    location: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Enhanced public function used by Ayush-style AI service code.
    """
    return _get_summarizer().summarize(
        text=text,
        category=category,
        location=location,
    )