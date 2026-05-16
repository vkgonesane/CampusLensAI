from typing import Optional
from pydantic import BaseModel


class SignalAIInput(BaseModel):
    title: str
    description: str
    category: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    reopen_count: int = 0


class SignalAIOutput(BaseModel):
    ai_category: str
    ai_sentiment: str
    ai_priority: str
    ai_summary: str
    suggested_department: str
    duplicate_score: float
    hotspot_score: float


def analyze_signal(signal: SignalAIInput) -> SignalAIOutput:
    text = f"{signal.title} {signal.description}".lower()

    if any(word in text for word in ["wifi", "internet", "network"]):
        category = "IT"
        department = "IT Department"
    elif any(word in text for word in ["water", "leak", "washroom", "tap"]):
        category = "Infrastructure"
        department = "Infrastructure Department"
    elif any(word in text for word in ["dirty", "garbage", "clean"]):
        category = "Sanitation"
        department = "Sanitation Department"
    elif any(word in text for word in ["unsafe", "security", "fight"]):
        category = "Security"
        department = "Security Department"
    else:
        category = signal.category or "General"
        department = "Admin Department"

    if signal.reopen_count >= 2:
        priority = "urgent"
    elif signal.reopen_count == 1:
        priority = "high"
    elif any(word in text for word in ["unsafe", "dangerous", "fire", "emergency"]):
        priority = "urgent"
    elif any(word in text for word in ["broken", "not working", "leak", "urgent"]):
        priority = "high"
    else:
        priority = "medium"

    if any(word in text for word in ["bad", "angry", "unsafe", "dirty", "dangerous", "broken"]):
        sentiment = "negative"
    else:
        sentiment = "neutral"

    summary = (
        f"{signal.title} reported at "
        f"{signal.location_name or 'unknown location'}. "
        f"AI classified it as {category} with {priority} priority."
    )

    return SignalAIOutput(
        ai_category=category,
        ai_sentiment=sentiment,
        ai_priority=priority,
        ai_summary=summary,
        suggested_department=department,
        duplicate_score=0.0,
        hotspot_score=0.0
    )