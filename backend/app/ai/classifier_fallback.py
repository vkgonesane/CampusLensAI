from typing import Dict, Any


CATEGORY_KEYWORDS = {
    "infrastructure": [
        "desk",
        "wall",
        "ceiling",
        "staircase",
        "door",
        "window",
        "road",
        "building"
    ],

    "it_issue": [
        "wifi",
        "internet",
        "portal",
        "login",
        "computer",
        "network",
        "server",
        "biometric"
    ],

    "sanitation": [
        "dirty",
        "garbage",
        "smell",
        "toilet",
        "dustbin",
        "waste",
        "unhygienic",
        "clean"
    ],

    "safety": [
        "fight",
        "harassment",
        "unsafe",
        "security",
        "theft",
        "suspicious",
        "emergency"
    ],

    "equipment": [
        "projector",
        "screen",
        "smart board",
        "microphone",
        "speaker",
        "fan",
        "air conditioner",
        "equipment"
    ],

    "electrical": [
        "power",
        "spark",
        "short circuit",
        "voltage",
        "wire",
        "switch",
        "lights",
        "electrical"
    ],

    "water": [
        "water",
        "leakage",
        "tap",
        "drainage",
        "pipe",
        "cooler"
    ]
}


DEPARTMENT_MAPPING = {
    "infrastructure": "Campus Maintenance",
    "it_issue": "IT Support",
    "sanitation": "Housekeeping",
    "safety": "Security Department",
    "equipment": "Technical Support",
    "electrical": "Electrical Department",
    "water": "Plumbing Department",
    "general": "General Administration"
}


def classify_signal(text: str) -> Dict[str, Any]:
    """
    Safe fallback classifier.

    Keeps backend operational even if
    advanced AI dependencies fail.
    """

    if not text:
        return {
            "category": "general",
            "department": DEPARTMENT_MAPPING["general"],
            "confidence": 0.0
        }

    text_lower = text.lower()

    category_scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0

        for keyword in keywords:
            if keyword in text_lower:
                score += 1

        category_scores[category] = score

    best_category = max(category_scores, key=category_scores.get)

    if category_scores[best_category] == 0:
        best_category = "general"

    confidence = round(
        category_scores[best_category] / 10,
        2
    )

    return {
        "category": best_category,
        "department": DEPARTMENT_MAPPING[best_category],
        "confidence": confidence,
        "all_scores": category_scores
    }