# backend/app/ai/sentiment.py

from typing import Dict, Any
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class SentimentAnalyzer:
    """
    Sentiment analyzer for CampusLensAI.

    This class analyzes the emotional tone of a campus complaint.
    It helps the priority engine understand whether the user is calm,
    dissatisfied, frustrated, or reporting something urgent.
    """

    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

        self.urgent_words = [
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
            "theft"
        ]

        self.frustration_words = [
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
            "same issue"
        ]

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of a campus signal.

        Args:
            text: User-submitted campus complaint.

        Returns:
            Dictionary containing sentiment label, score, urgency flag,
            frustration flag, and explanation.
        """

        if not text or not text.strip():
            return {
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "is_urgent": False,
                "is_frustrated": False,
                "explanation": "No valid text provided."
            }

        cleaned_text = text.lower().strip()

        scores = self.analyzer.polarity_scores(cleaned_text)
        compound_score = scores["compound"]

        sentiment = self._get_sentiment_label(compound_score)

        is_urgent = self._contains_keywords(cleaned_text, self.urgent_words)
        is_frustrated = self._contains_keywords(cleaned_text, self.frustration_words)

        explanation = self._generate_explanation(
            sentiment=sentiment,
            compound_score=compound_score,
            is_urgent=is_urgent,
            is_frustrated=is_frustrated
        )

        return {
            "sentiment": sentiment,
            "sentiment_score": round(compound_score, 3),
            "is_urgent": is_urgent,
            "is_frustrated": is_frustrated,
            "raw_scores": scores,
            "explanation": explanation
        }

    def _get_sentiment_label(self, compound_score: float) -> str:
        """
        Convert VADER compound score into a readable label.
        """

        if compound_score <= -0.45:
            return "negative"
        elif compound_score >= 0.45:
            return "positive"
        else:
            return "neutral"

    def _contains_keywords(self, text: str, keywords: list) -> bool:
        """
        Check if complaint contains urgency/frustration indicators.
        """

        return any(keyword in text for keyword in keywords)

    def _generate_explanation(
        self,
        sentiment: str,
        compound_score: float,
        is_urgent: bool,
        is_frustrated: bool
    ) -> str:
        """
        Generate simple explanation for debugging and demo clarity.
        """

        reasons = []

        reasons.append(f"Detected {sentiment} sentiment with score {round(compound_score, 3)}.")

        if is_urgent:
            reasons.append("Urgency-related words were found.")

        if is_frustrated:
            reasons.append("Repeated issue or frustration indicators were found.")

        return " ".join(reasons)


sentiment_analyzer = SentimentAnalyzer()


def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Public function used by ai_service.py and priority_engine.py.
    """

    return sentiment_analyzer.analyze(text)