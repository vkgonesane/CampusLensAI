from app.ai.classifier_fallback import classify_signal
from app.ai.sentiment import analyze_sentiment
from app.ai.priority_engine import calculate_priority
from app.ai.summarizer import generate_summary
from app.ai.duplicate_detector import detect_duplicate_score
from app.ai.hotspot_detector import calculate_hotspot_score


def analyze_signal(
    title: str,
    description: str,
    location_name: str | None = None,
    reopen_count: int = 0,
    previous_descriptions: list[str] = [],
    location_signal_count: int = 0
):

    classification = classify_signal(description)

    sentiment = analyze_sentiment(description)

    duplicate_score = detect_duplicate_score(
        description,
        previous_descriptions
    )

    hotspot_score = calculate_hotspot_score(
        location_signal_count
    )

    priority = calculate_priority(
        description=description,
        reopen_count=reopen_count,
        duplicate_score=duplicate_score,
        hotspot_score=hotspot_score
    )

    summary = generate_summary(
        title=title,
        description=description,
        location_name=location_name
    )

    return {
        "ai_category": classification['category'],
        "ai_sentiment": sentiment,
        "ai_priority": priority,
        "ai_summary": summary,
        "suggested_department": classification['department'],
        "duplicate_score": duplicate_score,
        "hotspot_score": hotspot_score
    }