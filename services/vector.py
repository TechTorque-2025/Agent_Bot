# services/vector.py
"""
Vector Store Service for Pinecone Integration
Handles vector database operations for RAG system
"""
import os
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
import logging

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing vector database operations with Pinecone"""

    def __init__(self):
        """Initialize Pinecone client and index"""
        # Relying on os.getenv which gets values loaded by dotenv in main.py
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1-aws")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "techtorque-kb")

        # Check if dimension is specified in env, otherwise use default
        self.dimension = int(os.getenv("PINECONE_DIMENSION", "384"))

        if not self.api_key:
            logger.warning("PINECONE_API_KEY not set. Vector store will not be available.")
            self.pc = None
            self.index = None
            return

        try:
            # Initialize Pinecone client
            logger.info(f"Initializing Pinecone client for index: {self.index_name}")
            self.pc = Pinecone(api_key=self.api_key)

            # Check if index exists, create if not (with timeout protection)
            try:
                self._ensure_index_exists()
            except Exception as idx_err:
                logger.warning(f"Could not verify/create Pinecone index (may be network issue): {idx_err}")
                logger.warning("Vector store will continue but may not function properly")
                self.pc = None
                self.index = None
                return

            # Connect to index
            self.index = self.pc.Index(self.index_name)

            # Get actual dimension from existing index
            try:
                stats = self.index.describe_index_stats()
                # Check for stats and dimension availability
                if stats and hasattr(stats, 'dimension') and stats.dimension: 
                    # If index exists and dimension is available, use it
                    self.dimension = stats.dimension 
                    logger.info(f"Using existing index dimension: {self.dimension}")
                elif stats and hasattr(stats, 'total_vector_count') and stats.total_vector_count > 0:
                    # If index has vectors but no dimension set (unlikely for Pinecone), log a warning
                    logger.warning("Index exists but dimension is unknown. Using default/env dimension.")
            except Exception as inner_e:
                logger.warning(f"Could not describe index stats, proceeding with ENV dimension: {inner_e}")
                pass

            logger.info(f"Connected to Pinecone index: {self.index_name} (dimension: {self.dimension})")

        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {str(e)}")
            self.pc = None
            self.index = None

    def _ensure_index_exists(self):
        """Create index if it doesn't exist"""
        if not self.pc:
            raise Exception("Pinecone client is not initialized.")

        try:
            # Get list of index names - .names() is a method, not a property
            index_list = self.pc.list_indexes()
            existing_indexes = [idx.name for idx in index_list] if hasattr(index_list, '__iter__') else index_list.names()

            if self.index_name not in existing_indexes:
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                logger.info(f"Index {self.index_name} created successfully")
            else:
                logger.info(f"Index {self.index_name} already exists")

        except Exception as e:
            logger.error(f"Error checking/creating index: {str(e)}")
            raise

    def is_available(self) -> bool:
        """Check if vector store is available"""
        return self.index is not None

    def upsert_vectors(
        self,
        vectors: List[List[float]],
        ids: List[str],
        metadata: List[Dict[str, Any]]
    ) -> bool:
        """
        Insert or update vectors in the index

        Args:
            vectors: List of embedding vectors
            ids: List of unique IDs for each vector
            metadata: List of metadata dicts for each vector

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available():
            logger.error("Vector store not available")
            return False

        try:
            # Prepare data for upsert
            vectors_data = [
                {
                    "id": vid,
                    "values": vector,
                    "metadata": meta
                }
                for vid, vector, meta in zip(ids, vectors, metadata)
            ]

            # Upsert in batches of 100
            batch_size = 100
            for i in range(0, len(vectors_data), batch_size):
                batch = vectors_data[i:i + batch_size]
                self.index.upsert(vectors=batch)

            logger.info(f"Upserted {len(vectors_data)} vectors to index")
            return True

        except Exception as e:
            logger.error(f"Error upserting vectors: {str(e)}")
            return False

    def query_similar(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query for similar vectors

        Args:
            query_vector: The query embedding vector
            top_k: Number of results to return
            filter_dict: Optional metadata filter
            include_metadata: Whether to include metadata in results

        Returns:
            List of matched documents with scores and metadata
        """
        if not self.is_available():
            logger.error("Vector store not available")
            return []

        try:
            # Query the index
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                filter=filter_dict,
                include_metadata=include_metadata
            )

            # Format results
            matches = []
            for match in results.matches:
                match_dict = {
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata if include_metadata else {}
                }
                matches.append(match_dict)

            logger.info(f"Found {len(matches)} similar documents")
            return matches

        except Exception as e:
            logger.error(f"Error querying vectors: {str(e)}")
            return []

    def delete_vectors(self, ids: List[str]) -> bool:
        """
        Delete vectors by IDs

        Args:
            ids: List of vector IDs to delete

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_available():
            logger.error("Vector store not available")
            return False

        try:
            self.index.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} vectors from index")
            return True

        except Exception as e:
            logger.error(f"Error deleting vectors: {str(e)}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics

        Returns:
            Dictionary with index stats
        """
        if not self.is_available():
            return {"available": False}

        try:
            stats = self.index.describe_index_stats()
            return {
                "available": True,
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_name": self.index_name
            }
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {"available": True, "error": str(e)}


# Singleton instance
_vector_store_instance = None


def get_vector_store() -> VectorStoreService:
    """Get or create the vector store singleton instance"""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStoreService()
    return _vector_store_instance