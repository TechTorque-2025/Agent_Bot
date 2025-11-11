# services/embedding.py
"""
Embedding Service for Text Vectorization
Uses sentence-transformers for generating embeddings
"""
from typing import List, Union
from sentence_transformers import SentenceTransformer
import logging
import numpy as np
import os # Keep os import for getenv inside the class method

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings"""

    def __init__(self, model_name: str = None):
        """
        Initialize the embedding model

        Args:
            model_name: Name of the sentence-transformers model to use
                       If None, will be determined from PINECONE_DIMENSION env var
        """
        # Determine model based on required dimension (using os.getenv as in original)
        required_dim = int(os.getenv("PINECONE_DIMENSION", "384"))

        if model_name is None:
            # Select model based on dimension
            if required_dim == 1024:
                # Use 768-dim model and pad to 1024
                model_name = "sentence-transformers/all-mpnet-base-v2"  # 768 dimensions
            else:
                model_name = "all-MiniLM-L6-v2"  # 384 dimensions

        self.model_name = model_name
        self.dimension = required_dim

        try:
            logger.info(f"Loading embedding model: {model_name} (target dimension: {required_dim})")
            # NOTE: sentence-transformers can take time, ensure this is a single instance
            self.model = SentenceTransformer(model_name)
            actual_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Embedding model loaded. Actual dimension: {actual_dim}, Target: {required_dim}")

            # Store actual dimension for potential padding/truncation
            self.actual_dimension = actual_dim
            self.dimension = required_dim

        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            self.model = None

    def is_available(self) -> bool:
        """Check if embedding service is available"""
        return self.model is not None

    def _adjust_dimension(self, embedding: np.ndarray) -> np.ndarray:
        """
        Adjust embedding dimension to match target dimension

        Args:
            embedding: Input embedding array

        Returns:
            Adjusted embedding array
        """
        if self.actual_dimension == self.dimension:
            return embedding

        if self.actual_dimension < self.dimension:
            # Pad with zeros
            padding = np.zeros(self.dimension - self.actual_dimension)
            return np.concatenate([embedding, padding])
        else:
            # Truncate
            return embedding[:self.dimension]

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not self.is_available():
            logger.error("Embedding model not available")
            return []

        try:
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)

            # Adjust dimension if needed
            embedding = self._adjust_dimension(embedding)

            # Convert to list
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()

            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return []

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of input texts to embed
            batch_size: Batch size for processing

        Returns:
            List of embedding vectors
        """
        if not self.is_available():
            logger.error("Embedding model not available")
            return []

        try:
            # Generate embeddings in batches
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 100
            )

            # Adjust dimensions for each embedding
            adjusted_embeddings = []
            for emb in embeddings:
                adjusted_emb = self._adjust_dimension(emb)
                adjusted_embeddings.append(adjusted_emb.tolist())

            logger.info(f"Generated {len(adjusted_embeddings)} embeddings (dimension: {self.dimension})")
            return adjusted_embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return []

    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score between -1 and 1
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            # Compute cosine similarity
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

            return float(similarity)

        except Exception as e:
            logger.error(f"Error computing similarity: {str(e)}")
            return 0.0

    def get_model_info(self) -> dict:
        """Get information about the embedding model"""
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "available": self.is_available()
        }


# Singleton instance
_embedding_service_instance = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service singleton instance"""
    global _embedding_service_instance
    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()
    return _embedding_service_instance