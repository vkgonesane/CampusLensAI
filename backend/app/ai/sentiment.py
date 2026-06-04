# backend/app/ai/sentiment.py

from typing import Any, Dict, Optional


URGENT_WORDS = [
    "urgent",
    "emergency",
    "danger",
    "dangerous",
    "unsafe",
    "immediately",
    "serious",
    "critical",
    "risk",
    "threat",
    "harassment",
    "fight",
    "fire",
    "spark",
    "accident",
    "injury",
    "theft",
]

FRUSTRATION_WORDS = [
    "again",
    "still",
    "not fixed",
    "no one",
    "ignored",
    "complained",
    "many times",
    "repeatedly",
    "every day",
    "for days",
    "for weeks",
    "same issue",
]


class SentimentAnalyzer:
    """
    Sentiment analyzer for CampusLensAI.

    VADER is initialized lazily so importing this module does not make
    FastAPI startup fragile.
    """

    def __init__(self):
        self.analyzer = None
        self.urgent_words = URGENT_WORDS
        self.frustration_words = FRUSTRATION_WORDS

    def _get_analyzer(self):
        if self.analyzer is None:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

            self.analyzer = SentimentIntensityAnalyzer()

        return self.analyzer

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of a campus signal.

        Returns richer Ayush-style metadata:
            {
                "sentiment": str,
                "sentiment_score": float,
                "is_urgent": bool,
                "is_frustrated": bool,
                ...
            }

        The backend-facing ai_service.py normalizes this to the old string value.
        """
        if not text or not text.strip():
            return {
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "is_urgent": False,
                "is_frustrated": False,
                "raw_scores": {},
                "explanation": "No valid text provided.",
            }

        cleaned_text = text.lower().strip()

        try:
            scores = self._get_analyzer().polarity_scores(cleaned_text)
            compound_score = float(scores.get("compound", 0.0))
        except Exception:
            scores = {}
            compound_score = self._fallback_sentiment_score(cleaned_text)

        sentiment = self._get_sentiment_label(compound_score)

        is_urgent = self._contains_keywords(cleaned_text, self.urgent_words)
        is_frustrated = self._contains_keywords(cleaned_text, self.frustration_words)

        explanation = self._generate_explanation(
            sentiment=sentiment,
            compound_score=compound_score,
            is_urgent=is_urgent,
            is_frustrated=is_frustrated,
        )

        return {
            "sentiment": sentiment,
            "sentiment_score": round(float(compound_score), 3),
            "is_urgent": is_urgent,
            "is_frustrated": is_frustrated,
            "raw_scores": scores,
            "explanation": explanation,
        }

    def _fallback_sentiment_score(self, text: str) -> float:
        """
        Very small dependency-free fallback.

        This is not meant to be perfect. It only prevents AI failure from
        breaking signal creation.
        """
        negative_words = [
            "bad",
            "broken",
            "dirty",
            "unsafe",
            "danger",
            "urgent",
            "not working",
            "failed",
            "issue",
            "problem",
            "complaint",
            "harassment",
            "fight",
            "theft",
            "fire",
        ]

        positive_words = [
            "good",
            "fixed",
            "resolved",
            "clean",
            "safe",
            "working",
            "better",
        ]

        negative_hits = sum(1 for word in negative_words if word in text)
        positive_hits = sum(1 for word in positive_words if word in text)

        if negative_hits > positive_hits:
            return -0.5

        if positive_hits > negative_hits:
            return 0.5

        return 0.0

    def _get_sentiment_label(self, compound_score: float) -> str:
        """
        Convert sentiment score into a readable label.

        We keep Ayush's thresholds here.
        """
        if compound_score <= -0.45:
            return "negative"

        if compound_score >= 0.45:
            return "positive"

        return "neutral"

    def _contains_keywords(self, text: str, keywords: list[str]) -> bool:
        return any(keyword in text for keyword in keywords)

    def _generate_explanation(
        self,
        sentiment: str,
        compound_score: float,
        is_urgent: bool,
        is_frustrated: bool,
    ) -> str:
        reasons = [
            f"Detected {sentiment} sentiment with score {round(float(compound_score), 3)}."
        ]

        if is_urgent:
            reasons.append("Urgency-related words were found.")

        if is_frustrated:
            reasons.append("Repeated issue or frustration indicators were found.")

        return " ".join(reasons)


_sentiment_analyzer_instance: Optional[SentimentAnalyzer] = None


def _get_sentiment_analyzer() -> SentimentAnalyzer:
    global _sentiment_analyzer_instance

    if _sentiment_analyzer_instance is None:
        _sentiment_analyzer_instance = SentimentAnalyzer()

    return _sentiment_analyzer_instance


def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Public function used by ai_service.py and priority_engine.py.

    Returns Ayush-style dict. Existing backend output compatibility is handled
    inside ai_service.py.
    """
    return _get_sentiment_analyzer().analyze(text)