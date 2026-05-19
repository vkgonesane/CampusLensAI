# backend/app/ai/classifier.py

from typing import Dict, List, Any
import numpy as np

from app.ai.embedding_service import (
    get_embedding,
    get_embeddings,
    calculate_embedding_similarity
)


class CampusSignalClassifier:
    """
    AI-based classifier for CampusLensAI.

    This classifier uses sentence embeddings to understand the meaning
    of a campus signal and classify it into the most suitable category.
    """

    def __init__(self):
        self.category_examples = {
            "infrastructure": [
                "broken classroom desk",
                "damaged wall in building",
                "cracked ceiling",
                "broken staircase",
                "damaged classroom door",
                "broken window",
                "campus road is damaged",
                "building structure needs repair"
            ],

            "it_issue": [
                "wifi is not working",
                "internet is down",
                "student portal is not opening",
                "unable to login to college website",
                "computer system is not working",
                "network issue in lab",
                "server is not responding",
                "biometric machine is not working"
            ],

            "sanitation": [
                "dirty washroom",
                "garbage is overflowing",
                "bad smell from toilet",
                "classroom is not clean",
                "dustbin is full",
                "campus area is unhygienic",
                "waste lying near canteen",
                "corridor is dirty"
            ],

            "safety": [
                "students are fighting",
                "harassment incident reported",
                "area feels unsafe",
                "security guard is not present",
                "theft happened on campus",
                "suspicious activity near gate",
                "emergency help needed",
                "safety concern near hostel"
            ],

            "equipment": [
                "projector is not working",
                "classroom screen is blank",
                "smart board is not working",
                "microphone is damaged",
                "speaker is not working",
                "fan is not working",
                "air conditioner is not cooling",
                "lab equipment is broken"
            ],

            "electrical": [
                "power cut in classroom",
                "electric spark from switch",
                "short circuit happened",
                "voltage fluctuation",
                "exposed electric wire",
                "switch board is damaged",
                "lights are not working",
                "electrical issue in building"
            ],

            "water": [
                "water leakage from pipe",
                "tap is not working",
                "no drinking water available",
                "water cooler is not working",
                "drainage is blocked",
                "water is overflowing",
                "broken water pipe",
                "washroom has no water"
            ],

            "general": [
                "general campus issue",
                "campus service problem",
                "complaint needs attention",
                "facility needs improvement",
                "student reported a problem"
            ]
        }

        self.department_mapping = {
            "infrastructure": "Campus Maintenance",
            "it_issue": "IT Support",
            "sanitation": "Housekeeping",
            "safety": "Security Department",
            "equipment": "Technical Support",
            "electrical": "Electrical Department",
            "water": "Plumbing Department",
            "general": "General Administration"
        }

        self.category_embeddings = self._prepare_category_embeddings()

    def _prepare_category_embeddings(self) -> Dict[str, np.ndarray]:
        """
        Convert example complaints of each category into average embeddings.
        """

        category_embeddings = {}

        for category, examples in self.category_examples.items():
            embeddings = get_embeddings(examples)
            average_embedding = np.mean(embeddings, axis=0)
            category_embeddings[category] = average_embedding

        return category_embeddings

    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify a campus signal into a category.

        Args:
            text: User-submitted campus signal.

        Returns:
            Dictionary containing category, suggested department,
            confidence score, and all category scores.
        """

        if not text or not text.strip():
            return {
                "category": "general",
                "department": self.department_mapping["general"],
                "confidence": 0.0,
                "all_scores": {}
            }

        signal_embedding = get_embedding(text)

        scores = {}

        for category, category_embedding in self.category_embeddings.items():
            score = calculate_embedding_similarity(
                signal_embedding,
                category_embedding
            )

            scores[category] = score

        best_category = max(scores, key=scores.get)
        confidence = scores[best_category]

        # Safety fallback for unclear complaints
        if confidence < 0.30:
            best_category = "general"

        return {
            "category": best_category,
            "department": self.department_mapping[best_category],
            "confidence": confidence,
            "all_scores": scores
        }


classifier = CampusSignalClassifier()


def classify_signal(text: str) -> Dict[str, Any]:
    """
    Public function used by ai_service.py.

    Example:
        result = classify_signal("Projector is not working in room 204")
    """

    return classifier.classify(text)