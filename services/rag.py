# services/rag.py
"""
RAG (Retrieval-Augmented Generation) Service
Combines vector search with LLM generation for context-aware responses
"""
from typing import List, Dict, Any, Optional
import logging

# FIX: Update imports to reflect the new structure: 'services' directory
from services.embedding import get_embedding_service
from services.vector import get_vector_store

logger = logging.getLogger(__name__)


class RAGService:
    """Service for retrieval-augmented generation"""

    def __init__(self):
        """Initialize RAG service"""
        # Initialize services using the corrected getter functions
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()

    def is_available(self) -> bool:
        """Check if RAG service is fully available"""
        return (
            self.embedding_service.is_available() and
            self.vector_store.is_available()
        )

    def retrieve_relevant_context(
        self,
        query: str,
        top_k: int = 5,
        doc_type_filter: Optional[str] = None,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for a query

        Args:
            query: User query text
            top_k: Number of results to retrieve
            doc_type_filter: Optional filter by document type
            min_score: Minimum similarity score threshold (0-1)

        Returns:
            List of relevant documents with text and metadata
        """
        if not self.is_available():
            logger.warning("RAG service not available, returning empty context")
            return []

        try:
            # Generate query embedding
            logger.info(f"Generating embedding for query: {query[:100]}...")
            query_embedding = self.embedding_service.embed_text(query)

            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []

            # Prepare filter if needed
            filter_dict = None
            if doc_type_filter:
                filter_dict = {"doc_type": doc_type_filter}

            # Query vector store
            logger.info(f"Querying vector store for top {top_k} results")
            results = self.vector_store.query_similar(
                query_vector=query_embedding,
                top_k=top_k,
                filter_dict=filter_dict,
                include_metadata=True
            )

            # Filter by minimum score and format results
            relevant_docs = []
            for result in results:
                if result["score"] >= min_score:
                    doc = {
                        "text": result["metadata"].get("text", ""),
                        "score": result["score"],
                        "title": result["metadata"].get("title", "Unknown"),
                        "doc_type": result["metadata"].get("doc_type", "general"),
                        "source": result["metadata"].get("source", "unknown"),
                        "chunk_index": result["metadata"].get("chunk_index", 0),
                        "doc_id": result["metadata"].get("doc_id", ""),
                    }
                    relevant_docs.append(doc)

            logger.info(f"Retrieved {len(relevant_docs)} relevant documents above threshold")
            return relevant_docs

        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return []

    def format_context_for_prompt(
        self,
        relevant_docs: List[Dict[str, Any]],
        max_context_length: int = 2000
    ) -> str:
        """
        Format retrieved documents into a context string for LLM

        Args:
            relevant_docs: List of relevant documents
            max_context_length: Maximum characters for context

        Returns:
            Formatted context string
        """
        if not relevant_docs:
            return ""

        context_parts = []
        total_length = 0

        for i, doc in enumerate(relevant_docs, 1):
            # Format document
            doc_text = f"[Source {i}: {doc['title']}]\n{doc['text']}\n"

            # Check if adding this would exceed limit
            if total_length + len(doc_text) > max_context_length:
                break

            context_parts.append(doc_text)
            total_length += len(doc_text)

        if not context_parts:
            return ""

        # Combine into final context
        context = "Relevant Information:\n\n" + "\n".join(context_parts)
        return context

    def retrieve_and_format(
        self,
        query: str,
        top_k: int = 5,
        doc_type_filter: Optional[str] = None,
        min_score: float = 0.3,
        max_context_length: int = 2000
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context and format for use in LLM prompt

        Args:
            query: User query
            top_k: Number of results to retrieve
            doc_type_filter: Optional filter by document type
            min_score: Minimum similarity score
            max_context_length: Maximum context length

        Returns:
            Dictionary with formatted context and metadata
        """
        # Retrieve documents
        relevant_docs = self.retrieve_relevant_context(
            query=query,
            top_k=top_k,
            doc_type_filter=doc_type_filter,
            min_score=min_score
        )

        # Format context
        formatted_context = self.format_context_for_prompt(
            relevant_docs=relevant_docs,
            max_context_length=max_context_length
        )

        return {
            "context": formatted_context,
            "num_sources": len(relevant_docs),
            "sources": [
                {
                    "title": doc["title"],
                    "score": doc["score"],
                    "doc_type": doc["doc_type"]
                }
                for doc in relevant_docs
            ],
            "has_context": len(relevant_docs) > 0
        }

    def get_service_status(self) -> Dict[str, Any]:
        """Get RAG service status"""
        embedding_info = self.embedding_service.get_model_info()
        vector_stats = self.vector_store.get_stats()

        return {
            "rag_available": self.is_available(),
            "embedding_service": embedding_info,
            "vector_store": vector_stats
        }


# Singleton instance
_rag_service_instance = None


def get_rag_service() -> RAGService:
    """Get or create the RAG service singleton instance"""
    global _rag_service_instance
    if _rag_service_instance is None:
        _rag_service_instance = RAGService()
    return _rag_service_instance