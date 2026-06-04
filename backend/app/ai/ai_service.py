# backend/app/ai/ai_service.py

from typing import Any, Dict, Optional


def _safe_call(func, default, *args, **kwargs):
    """
    Runs an AI helper safely.

    AI dependencies should never crash backend startup or signal creation.
    If an AI module fails because of missing models/dependencies, we return
    a safe default instead of breaking the API.
    """
    try:
        return func(*args, **kwargs)
    except Exception:
        return default


def _normalize_classification(result: Any) -> Dict[str, Any]:
    """
    Supports both old and new classifier return formats.
    Expected old format:
        {"category": "...", "department": "..."}

    Possible newer format:
        {"category": "...", "department": "...", "confidence": 0.91}
    """
    if not isinstance(result, dict):
        return {
            "category": "general",
            "department": "General Administration",
            "confidence": 0.0,
        }

    return {
        "category": result.get("category") or "general",
        "department": result.get("department") or "General Administration",
        "confidence": float(result.get("confidence") or 0.0),
    }


def _normalize_sentiment(result: Any) -> str:
    """
    Supports both old and new sentiment return formats.

    Old backend-compatible format:
        "positive" / "neutral" / "negative"

    Newer AI format:
        {"sentiment": "negative", ...}
    """
    if isinstance(result, dict):
        return result.get("sentiment") or "neutral"

    if isinstance(result, str):
        return result

    return "neutral"


def _normalize_priority(result: Any) -> str:
    """
    Supports both old and new priority return formats.

    Old backend-compatible format:
        "low" / "medium" / "high"

    Newer AI format:
        {"priority": "high", "priority_score": 0.85}
    """
    if isinstance(result, dict):
        return result.get("priority") or "low"

    if isinstance(result, str):
        return result

    return "low"


def _normalize_summary(result: Any, fallback: str) -> str:
    """
    Supports both old and new summarizer return formats.

    Old backend-compatible format:
        "summary text"

    Newer AI format:
        {"summary": "summary text", ...}
    """
    if isinstance(result, dict):
        return result.get("summary") or fallback

    if isinstance(result, str):
        return result

    return fallback


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def analyze_signal(
    title: str,
    description: str,
    location_name: Optional[str] = None,
    reopen_count: int = 0,
    previous_descriptions: list[str] = [],
    location_signal_count: int = 0,
) -> Dict[str, Any]:
    """
    Backend-compatible CampusLensAI analysis entrypoint.

    IMPORTANT:
    This function's signature and return keys must not change because
    existing backend services depend on them.

    Required return keys:
        ai_category
        ai_sentiment
        ai_priority
        ai_summary
        suggested_department
        duplicate_score
        hotspot_score
    """

    safe_description = (description or "").strip()
    safe_title = (title or "").strip()

    if not safe_description and not safe_title:
        return {
            "ai_category": "general",
            "ai_sentiment": "neutral",
            "ai_priority": "low",
            "ai_summary": "No valid signal text provided.",
            "suggested_department": "General Administration",
            "duplicate_score": 0.0,
            "hotspot_score": 0.0,
        }

    text_for_ai = safe_description or safe_title

    # Imports stay inside the function so FastAPI startup remains safer.
    # If heavy AI dependencies fail, only this request falls back safely.
    try:
        from app.ai.classifier import classify_signal
    except Exception:
        try:
            from app.ai.classifier_fallback import classify_signal
        except Exception:
            classify_signal = None

    try:
        from app.ai.sentiment import analyze_sentiment
    except Exception:
        analyze_sentiment = None

    try:
        from app.ai.priority_engine import calculate_priority
    except Exception:
        calculate_priority = None

    try:
        from app.ai.summarizer import generate_summary
    except Exception:
        try:
            from app.ai.summarizer import summarize_signal
        except Exception:
            generate_summary = None
            summarize_signal = None
        else:
            generate_summary = None
    else:
        summarize_signal = None

    try:
        from app.ai.duplicate_detector import detect_duplicate_score
    except Exception:
        detect_duplicate_score = None

    try:
        from app.ai.hotspot_detector import calculate_hotspot_score
    except Exception:
        calculate_hotspot_score = None

    # 1. Classification
    if classify_signal:
        classification_raw = _safe_call(
            classify_signal,
            {
                "category": "general",
                "department": "General Administration",
                "confidence": 0.0,
            },
            text_for_ai,
        )
    else:
        classification_raw = {
            "category": "general",
            "department": "General Administration",
            "confidence": 0.0,
        }

    classification = _normalize_classification(classification_raw)

    # 2. Sentiment
    if analyze_sentiment:
        sentiment_raw = _safe_call(
            analyze_sentiment,
            "neutral",
            text_for_ai,
        )
    else:
        sentiment_raw = "neutral"

    sentiment = _normalize_sentiment(sentiment_raw)

    # 3. Duplicate score
    if detect_duplicate_score:
        duplicate_score = _safe_call(
            detect_duplicate_score,
            0.0,
            text_for_ai,
            previous_descriptions or [],
        )
    else:
        duplicate_score = 0.0

    duplicate_score = _as_float(duplicate_score)

    # 4. Hotspot score
    if calculate_hotspot_score:
        hotspot_score = _safe_call(
            calculate_hotspot_score,
            0.0,
            location_signal_count or 0,
        )
    else:
        hotspot_score = 0.0

    hotspot_score = _as_float(hotspot_score)

    # 5. Priority
    if calculate_priority:
        priority_raw = _safe_call(
            calculate_priority,
            "low",
            description=text_for_ai,
            reopen_count=reopen_count or 0,
            duplicate_score=duplicate_score,
            hotspot_score=hotspot_score,
        )
    else:
        priority_raw = "low"

    priority = _normalize_priority(priority_raw)

    # 6. Summary
    fallback_summary = text_for_ai[:150]

    if generate_summary:
        summary_raw = _safe_call(
            generate_summary,
            fallback_summary,
            title=safe_title,
            description=text_for_ai,
            location_name=location_name,
        )
    elif summarize_signal:
        summary_raw = _safe_call(
            summarize_signal,
            {"summary": fallback_summary},
            text=text_for_ai,
            category=classification["category"],
            location=location_name,
        )
    else:
        summary_raw = fallback_summary

    summary = _normalize_summary(summary_raw, fallback_summary)

    return {
        "ai_category": classification["category"],
        "ai_sentiment": sentiment,
        "ai_priority": priority,
        "ai_summary": summary,
        "suggested_department": classification["department"],
        "duplicate_score": duplicate_score,
        "hotspot_score": hotspot_score,
    }