# backend/app/ai/ai_service.py

from typing import Dict, Any, List, Optional

from app.ai.classifier import classify_signal
from app.ai.sentiment import analyze_sentiment
from app.ai.duplicate_detector import detect_duplicate
from app.ai.hotspot_detector import detect_hotspot
from app.ai.priority_engine import calculate_priority
from app.ai.summarizer import summarize_signal


def analyze_signal(
    text: str,
    location: Optional[str] = None,
    reopen_count: int = 0,
    existing_signals: Optional[List[Dict[str, Any]]] = None,
    recent_signals: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Main AI function for CampusLensAI.

    This function is called by the backend whenever a user submits
    a new Campus Signal.

    Args:
        text:
            User-submitted complaint text.

        location:
            Location of the issue, for example:
            "Block A", "Room 204", "Canteen Washroom".

        reopen_count:
            Number of times this issue has been reopened.

        existing_signals:
            Previous signals used for duplicate detection.

            Expected format:
            [
                {
                    "id": 1,
                    "text": "WiFi is not working in Block A",
                    "category": "it_issue",
                    "location": "Block A",
                    "status": "open"
                }
            ]

        recent_signals:
            Recent signals used for hotspot detection.

            Expected format:
            [
                {
                    "id": 1,
                    "category": "sanitation",
                    "location": "Block A Washroom",
                    "status": "open"
                }
            ]

    Returns:
        Final AI analysis dictionary.
    """

    if not text or not text.strip():
        return _empty_ai_response("No valid signal text provided.")

    existing_signals = existing_signals or []
    recent_signals = recent_signals or []

    # 1. Classification
    classification_result = classify_signal(text)

    ai_category = classification_result.get("category", "general")
    suggested_department = classification_result.get(
        "department",
        "General Administration"
    )

    # 2. Sentiment Analysis
    sentiment_result = analyze_sentiment(text)

    ai_sentiment = sentiment_result.get("sentiment", "neutral")

    # 3. Duplicate Detection
    duplicate_result = detect_duplicate(
        new_signal_text=text,
        new_category=ai_category,
        new_location=location,
        existing_signals=existing_signals
    )

    duplicate_score = duplicate_result.get("duplicate_score", 0.0)
    repeated_issue_count = duplicate_result.get("repeated_issue_count", 0)

    # 4. Hotspot Detection
    hotspot_result = detect_hotspot(
        new_location=location,
        new_category=ai_category,
        recent_signals=recent_signals
    )

    hotspot_score = hotspot_result.get("hotspot_score", 0.0)

    # 5. Priority Scoring
    priority_result = calculate_priority(
        category=ai_category,
        sentiment_result=sentiment_result,
        duplicate_score=duplicate_score,
        hotspot_score=hotspot_score,
        reopen_count=reopen_count,
        repeated_issue_count=repeated_issue_count
    )

    ai_priority = priority_result.get("priority", "low")

    # 6. AI Summary
    summary_result = summarize_signal(
        text=text,
        category=ai_category,
        location=location
    )

    ai_summary = summary_result.get("summary", text[:150])

    return {
        "ai_category": ai_category,
        "ai_sentiment": ai_sentiment,
        "ai_priority": ai_priority,
        "ai_summary": ai_summary,
        "suggested_department": suggested_department,
        "duplicate_score": duplicate_score,
        "hotspot_score": hotspot_score,

        # Extra useful details for backend/admin dashboard
        "classification_confidence": classification_result.get("confidence", 0.0),
        "priority_score": priority_result.get("priority_score", 0.0),
        "is_duplicate": duplicate_result.get("is_duplicate", False),
        "matched_signal_id": duplicate_result.get("matched_signal_id"),
        "repeated_issue_count": repeated_issue_count,
        "is_hotspot": hotspot_result.get("is_hotspot", False),
        "short_title": summary_result.get("short_title"),
        "key_points": summary_result.get("key_points", []),

        # Debug/explainability fields
        "explanations": {
            "sentiment": sentiment_result.get("explanation"),
            "duplicate": duplicate_result.get("explanation"),
            "hotspot": hotspot_result.get("explanation"),
            "priority": priority_result.get("explanation")
        },

        # Optional detailed scores
        "raw": {
            "classification": classification_result,
            "sentiment": sentiment_result,
            "duplicate": duplicate_result,
            "hotspot": hotspot_result,
            "priority": priority_result,
            "summary": summary_result
        }
    }


def _empty_ai_response(reason: str) -> Dict[str, Any]:
    """
    Default response when AI analysis cannot be performed.
    """

    return {
        "ai_category": "general",
        "ai_sentiment": "neutral",
        "ai_priority": "low",
        "ai_summary": reason,
        "suggested_department": "General Administration",
        "duplicate_score": 0.0,
        "hotspot_score": 0.0,
        "classification_confidence": 0.0,
        "priority_score": 0.0,
        "is_duplicate": False,
        "matched_signal_id": None,
        "repeated_issue_count": 0,
        "is_hotspot": False,
        "short_title": "Invalid Signal",
        "key_points": [],
        "explanations": {
            "sentiment": reason,
            "duplicate": reason,
            "hotspot": reason,
            "priority": reason
        },
        "raw": {}
    }