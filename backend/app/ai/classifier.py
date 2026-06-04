# backend/app/ai/classifier.py

from difflib import SequenceMatcher
from typing import Any, Dict, Optional

import numpy as np


CATEGORY_EXAMPLES = {
    "infrastructure": [
        "broken classroom desk",
        "damaged wall in building",
        "cracked ceiling",
        "broken staircase",
        "damaged classroom door",
        "broken window",
        "campus road is damaged",
        "building structure needs repair",
    ],
    "it_issue": [
        "wifi is not working",
        "internet is down",
        "student portal is not opening",
        "unable to login to college website",
        "computer system is not working",
        "network issue in lab",
        "server is not responding",
        "biometric machine is not working",
    ],
    "sanitation": [
        "dirty washroom",
        "garbage is overflowing",
        "bad smell from toilet",
        "classroom is not clean",
        "dustbin is full",
        "campus area is unhygienic",
        "waste lying near canteen",
        "corridor is dirty",
    ],
    "safety": [
        "students are fighting",
        "harassment incident reported",
        "area feels unsafe",
        "security guard is not present",
        "theft happened on campus",
        "suspicious activity near gate",
        "emergency help needed",
        "safety concern near hostel",
    ],
    "equipment": [
        "projector is not working",
        "classroom screen is blank",
        "smart board is not working",
        "microphone is damaged",
        "speaker is not working",
        "fan is not working",
        "air conditioner is not cooling",
        "lab equipment is broken",
    ],
    "electrical": [
        "power cut in classroom",
        "electric spark from switch",
        "short circuit happened",
        "voltage fluctuation",
        "exposed electric wire",
        "switch board is damaged",
        "lights are not working",
        "electrical issue in building",
    ],
    "water": [
        "water leakage from pipe",
        "tap is not working",
        "no drinking water available",
        "water cooler is not working",
        "drainage is blocked",
        "water is overflowing",
        "broken water pipe",
        "washroom has no water",
    ],
    "general": [
        "general campus issue",
        "campus service problem",
        "complaint needs attention",
        "facility needs improvement",
        "student reported a problem",
    ],
}


DEPARTMENT_MAPPING = {
    "infrastructure": "Campus Maintenance",
    "it_issue": "IT Support",
    "sanitation": "Housekeeping",
    "safety": "Security Department",
    "equipment": "Technical Support",
    "electrical": "Electrical Department",
    "water": "Plumbing Department",
    "general": "General Administration",
}


KEYWORD_RULES = {
    "it_issue": [
        "wifi",
        "internet",
        "network",
        "server",
        "portal",
        "login",
        "website",
        "computer",
        "biometric",
    ],
    "sanitation": [
        "dirty",
        "garbage",
        "dustbin",
        "toilet",
        "washroom",
        "smell",
        "hygiene",
        "waste",
        "clean",
    ],
    "safety": [
        "fight",
        "harassment",
        "unsafe",
        "security",
        "theft",
        "suspicious",
        "emergency",
        "danger",
    ],
    "equipment": [
        "projector",
        "screen",
        "smart board",
        "microphone",
        "speaker",
        "fan",
        "ac",
        "air conditioner",
        "lab equipment",
    ],
    "electrical": [
        "power",
        "electric",
        "spark",
        "short circuit",
        "voltage",
        "wire",
        "switch",
        "light",
    ],
    "water": [
        "water",
        "tap",
        "cooler",
        "drainage",
        "pipe",
        "leakage",
        "overflowing",
    ],
    "infrastructure": [
        "broken desk",
        "wall",
        "ceiling",
        "staircase",
        "door",
        "window",
        "road",
        "building",
        "repair",
    ],
}


def _default_result(
    category: str = "general",
    confidence: float = 0.0,
    all_scores: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    return {
        "category": category,
        "department": DEPARTMENT_MAPPING.get(category, "General Administration"),
        "confidence": round(float(confidence), 3),
        "all_scores": all_scores or {},
    }


def _fallback_keyword_classify(text: str) -> Dict[str, Any]:
    """
    Dependency-free classifier fallback.

    Used when embedding models are unavailable.
    """
    clean_text = (text or "").lower().strip()

    if not clean_text:
        return _default_result()

    scores: Dict[str, float] = {}

    for category, keywords in KEYWORD_RULES.items():
        score = 0.0

        for keyword in keywords:
            keyword = keyword.lower()

            if keyword in clean_text:
                score += 1.0
            else:
                score += SequenceMatcher(None, clean_text, keyword).ratio() * 0.15

        scores[category] = score / max(len(keywords), 1)

    if not scores:
        return _default_result()

    best_category = max(scores, key=scores.get)
    confidence = float(scores.get(best_category, 0.0))

    if confidence < 0.12:
        best_category = "general"
        confidence = 0.0

    return _default_result(
        category=best_category,
        confidence=confidence,
        all_scores=scores,
    )


class CampusSignalClassifier:
    """
    AI-based classifier for CampusLensAI.

    Heavy embedding work is initialized only when this class is first used,
    not during FastAPI startup.
    """

    def __init__(self):
        self.category_examples = CATEGORY_EXAMPLES
        self.department_mapping = DEPARTMENT_MAPPING
        self.category_embeddings: Optional[Dict[str, np.ndarray]] = None
        self.embedding_ready = False

    def _prepare_category_embeddings(self) -> Dict[str, np.ndarray]:
        from app.ai.embedding_service import get_embeddings

        category_embeddings = {}

        for category, examples in self.category_examples.items():
            embeddings = get_embeddings(examples)
            average_embedding = np.mean(embeddings, axis=0)
            category_embeddings[category] = average_embedding

        return category_embeddings

    def _ensure_embeddings_ready(self) -> bool:
        if self.embedding_ready and self.category_embeddings is not None:
            return True

        try:
            self.category_embeddings = self._prepare_category_embeddings()
            self.embedding_ready = True
            return True
        except Exception:
            self.category_embeddings = None
            self.embedding_ready = False
            return False

    def classify(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return _default_result()

        if not self._ensure_embeddings_ready():
            return _fallback_keyword_classify(text)

        try:
            from app.ai.embedding_service import (
                calculate_embedding_similarity,
                get_embedding,
            )

            signal_embedding = get_embedding(text)

            scores = {}

            for category, category_embedding in self.category_embeddings.items():
                score = calculate_embedding_similarity(
                    signal_embedding,
                    category_embedding,
                )
                scores[category] = float(score)

            best_category = max(scores, key=scores.get)
            confidence = float(scores[best_category])

            # Safety fallback for unclear complaints
            if confidence < 0.35:
                best_category = "general"

            return {
                "category": best_category,
                "department": self.department_mapping[best_category],
                "confidence": round(confidence, 3),
                "all_scores": scores,
            }

        except Exception:
            return _fallback_keyword_classify(text)


_classifier_instance: Optional[CampusSignalClassifier] = None


def _get_classifier() -> CampusSignalClassifier:
    """
    Lazy singleton.

    Do not instantiate CampusSignalClassifier at import time.
    """
    global _classifier_instance

    if _classifier_instance is None:
        _classifier_instance = CampusSignalClassifier()

    return _classifier_instance


def classify_signal(text: str) -> Dict[str, Any]:
    """
    Public function used by ai_service.py.

    Example:
        classify_signal("Projector is not working in room 204")
    """
    return _get_classifier().classify(text)