
from functools import lru_cache
from typing import List, Union

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingService:
    """
    Shared embedding service for CampusLensAI.

    This service converts text into numerical vectors called embeddings.
    These embeddings help the AI understand meaning, not just keywords.

    Used by:
    - classifier.py
    - duplicate_detector.py
    - hotspot_detector.py
    - priority_engine.py
    """

    def __init__(self, model_name: str = MODEL_NAME):
        """
        Initialize the embedding model.

        The model is loaded once when the service object is created.
        """

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def get_embedding(self, text: str) -> np.ndarray:
        """
        Convert a single text into an embedding vector.

        Args:
            text: A campus signal text.

        Returns:
            NumPy array representing the meaning of the text.
        """

        if not text or not text.strip():
            raise ValueError("Text cannot be empty for embedding generation.")

        prepared_text = f"Campus complaint: {text.strip()}"

        return self.model.encode(
            prepared_text,
            normalize_embeddings=True
        )

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Convert multiple texts into embedding vectors.

        Args:
            texts: List of campus signal texts.

        Returns:
            NumPy array of embeddings.
        """

        if not texts:
            raise ValueError("Text list cannot be empty.")

        cleaned_texts = []

        for text in texts:
            if text and text.strip():
                cleaned_texts.append(text.strip())

        if not cleaned_texts:
            raise ValueError("Text list contains no valid text.")

        prepared_texts = [
            f"Campus complaint: {text}"
            for text in cleaned_texts
        ]

        return self.model.encode(
            prepared_texts,
            normalize_embeddings=True
        )

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two text inputs.

        Args:
            text1: First campus signal.
            text2: Second campus signal.

        Returns:
            Similarity score between 0 and 1 approximately.
        """

        embedding1 = self.get_embedding(text1)
        embedding2 = self.get_embedding(text2)

        return self.calculate_embedding_similarity(embedding1, embedding2)

    def calculate_embedding_similarity(
        self,
        embedding1: Union[np.ndarray, List[float]],
        embedding2: Union[np.ndarray, List[float]]
    ) -> float:
        """
        Calculate similarity between two existing embeddings.

        Useful when embeddings are already stored in the database.

        Args:
            embedding1: First embedding vector.
            embedding2: Second embedding vector.

        Returns:
            Cosine similarity score.
        """

        embedding1 = np.array(embedding1).reshape(1, -1)
        embedding2 = np.array(embedding2).reshape(1, -1)

        score = cosine_similarity(embedding1, embedding2)[0][0]

        return round(float(score), 3)


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """
    Returns a cached instance of EmbeddingService.

    This prevents the AI model from loading again and again.
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
    """

    service = get_embedding_service()
    return service.calculate_similarity(text1, text2)


def calculate_embedding_similarity(
    embedding1: Union[np.ndarray, List[float]],
    embedding2: Union[np.ndarray, List[float]]
) -> float:
    """
    Helper function to calculate similarity between two embeddings.
    """

    service = get_embedding_service()
    return service.calculate_embedding_similarity(embedding1, embedding2)