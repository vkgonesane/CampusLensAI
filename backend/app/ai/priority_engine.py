def calculate_priority(
    description: str,
    reopen_count: int = 0,
    duplicate_score: float = 0.0,
    hotspot_score: float = 0.0
) -> str:

    text = description.lower()

    urgent_words = [
        "dangerous",
        "unsafe",
        "fire",
        "electric shock",
        "harassment",
        "emergency"
    ]

    high_words = [
        "broken",
        "not working",
        "leak",
        "urgent",
        "blocked"
    ]

    # Reopen escalation
    if reopen_count >= 2:
        return "urgent"

    if reopen_count == 1:
        return "high"

    # Duplicate escalation
    if duplicate_score > 0.8:
        return "high"

    # Hotspot escalation
    if hotspot_score > 0.7:
        return "high"

    if any(word in text for word in urgent_words):
        return "urgent"

    if any(word in text for word in high_words):
        return "high"

    return "medium"