# backend/app/ai/embedding_service.py

from functools import lru_cache
from typing import List, Union
from difflib import SequenceMatcher

import numpy as np


MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingService:
    """
    Shared embedding service for CampusLensAI.

    Heavy AI dependencies are imported and loaded lazily so FastAPI startup
    stays safe even if sentence-transformers/torch/model loading has issues.
    """

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self.model = None

    def _get_model(self):
        """
        Lazily load SentenceTransformer only when embeddings are actually needed.
        """
        if self.model is None:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(self.model_name)

        return self.model

    def get_embedding(self, text: str) -> np.ndarray:
        """
        Convert a single text into an embedding vector.
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty for embedding generation.")

        prepared_text = f"Campus complaint: {text.strip()}"

        model = self._get_model()

        return model.encode(
            prepared_text,
            normalize_embeddings=True,
        )

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Convert multiple texts into embedding vectors.
        """
        if not texts:
            raise ValueError("Text list cannot be empty.")

        cleaned_texts = [
            text.strip()
            for text in texts
            if text and text.strip()
        ]

        if not cleaned_texts:
            raise ValueError("Text list contains no valid text.")

        prepared_texts = [
            f"Campus complaint: {text}"
            for text in cleaned_texts
        ]

        model = self._get_model()

        return model.encode(
            prepared_texts,
            normalize_embeddings=True,
        )

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two text inputs.
        """
        embedding1 = self.get_embedding(text1)
        embedding2 = self.get_embedding(text2)

        return self.calculate_embedding_similarity(embedding1, embedding2)

    def calculate_embedding_similarity(
        self,
        embedding1: Union[np.ndarray, List[float]],
        embedding2: Union[np.ndarray, List[float]],
    ) -> float:
        """
        Calculate similarity between two existing embeddings.
        """
        embedding1 = np.array(embedding1).reshape(1, -1)
        embedding2 = np.array(embedding2).reshape(1, -1)

        denominator = np.linalg.norm(embedding1) * np.linalg.norm(embedding2)

        if denominator == 0:
            return 0.0

        score = np.dot(embedding1, embedding2.T)[0][0] / denominator

        return round(float(score), 3)


def fallback_text_similarity(text1: str, text2: str) -> float:
    """
    Dependency-free fallback similarity.
    """
    text1 = (text1 or "").lower().strip()
    text2 = (text2 or "").lower().strip()

    if not text1 or not text2:
        return 0.0

    return round(float(SequenceMatcher(None, text1, text2).ratio()), 3)


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """
    Returns a cached instance of EmbeddingService.

    The model itself is still loaded lazily when first used.
    """
    return EmbeddingService()


def get_embedding(text: str) -> np.ndarray:
    """
    Helper function to get embedding for one text.
    """
    service = get_embedding_service()
    return service.get_embedding(text)


def get_embeddings(texts: List[str]) -> np.ndarray:
    """
    Helper function to get embeddings for multiple texts.
    """
    service = get_embedding_service()
    return service.get_embeddings(texts)


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Helper function to calculate similarity between two texts.

    Falls back to lightweight text similarity if embedding dependencies fail.
    """
    try:
        service = get_embedding_service()
        return service.calculate_similarity(text1, text2)
    except Exception:
        return fallback_text_similarity(text1, text2)


def calculate_embedding_similarity(
    embedding1: Union[np.ndarray, List[float]],
    embedding2: Union[np.ndarray, List[float]],
) -> float:
    """
    Helper function to calculate similarity between two embeddings.
    """
    service = get_embedding_service()
    return service.calculate_embedding_similarity(embedding1, embedding2)