# services/document.py
"""
Document Ingestion Service
Handles document processing, chunking, and indexing for RAG system
"""
import uuid
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import re

# FIX: Update imports to reflect the new structure: 'services' directory
from services.embedding import get_embedding_service
from services.vector import get_vector_store
from config.settings import settings # Include settings for chunk size/overlap

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for processing and indexing documents"""

    def __init__(self, chunk_size: int = settings.RAG_CHUNK_SIZE, chunk_overlap: int = settings.RAG_CHUNK_OVERLAP):
        """
        Initialize document service

        Args:
            chunk_size: Maximum number of characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()

    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Split text into chunks with overlap

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of chunk dictionaries with text and metadata
        """
        # Clean text
        text = text.strip()
        if not text:
            return []

        # Split by paragraphs first
        paragraphs = re.split(r'\n\s*\n', text)

        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # If paragraph fits in current chunk, add it
            if len(current_chunk) + len(paragraph) + 2 <= self.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # Save current chunk if not empty
                if current_chunk:
                    chunks.append(current_chunk)

                # Start new chunk with paragraph
                if len(paragraph) <= self.chunk_size:
                    current_chunk = paragraph
                else:
                    # Split long paragraph into sentences
                    sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                    current_chunk = ""

                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) + 1 <= self.chunk_size:
                            if current_chunk:
                                current_chunk += " " + sentence
                            else:
                                current_chunk = sentence
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = sentence

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk)

        # Create chunk objects with metadata
        chunk_objects = []
        for i, chunk_text in enumerate(chunks):
            chunk_obj = {
                "text": chunk_text,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "metadata": metadata or {}
            }
            chunk_objects.append(chunk_obj)

        logger.info(f"Created {len(chunk_objects)} chunks from text")
        return chunk_objects

    def ingest_document(
        self,
        content: str,
        title: str,
        doc_type: str = "general",
        source: str = "manual",
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ingest a document into the vector database

        Args:
            content: Document content
            title: Document title
            doc_type: Type of document (e.g., 'faq', 'manual', 'policy')
            source: Source of the document
            additional_metadata: Additional metadata to attach

        Returns:
            Dictionary with ingestion result
        """
        if not self.embedding_service.is_available():
            return {
                "success": False,
                "error": "Embedding service not available"
            }

        if not self.vector_store.is_available():
            return {
                "success": False,
                "error": "Vector store not available"
            }

        try:
            # Generate document ID
            doc_id = str(uuid.uuid4())
            content_hash = hashlib.md5(content.encode()).hexdigest()

            # Prepare base metadata
            base_metadata = {
                "doc_id": doc_id,
                "title": title,
                "doc_type": doc_type,
                "source": source,
                "content_hash": content_hash,
                "ingested_at": datetime.utcnow().isoformat(),
                **(additional_metadata or {})
            }

            # Chunk the document
            chunks = self.chunk_text(content, base_metadata)

            if not chunks:
                return {
                    "success": False,
                    "error": "No chunks created from content"
                }

            # Extract texts for embedding
            texts = [chunk["text"] for chunk in chunks]

            # Generate embeddings
            logger.info(f"Generating embeddings for {len(texts)} chunks")
            embeddings = self.embedding_service.embed_texts(texts)

            if not embeddings or len(embeddings) != len(texts):
                return {
                    "success": False,
                    "error": "Failed to generate embeddings"
                }

            # Prepare vector IDs and metadata for Pinecone
            vector_ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
            
            # Combine chunk-specific metadata (index, total_chunks) 
            # with base document metadata, and add the chunk text.
            vectors_and_metadata = []
            for i, chunk in enumerate(chunks):
                # Ensure each chunk's text is saved in the metadata
                meta = {**base_metadata, "chunk_index": i, "total_chunks": len(chunks), "text": chunk["text"]}
                vectors_and_metadata.append(meta)

            self.vector_store.upsert_vectors(
                vectors=embeddings,
                ids=vector_ids,
                metadata=vectors_and_metadata
            )

            logger.info(f"Successfully ingested document '{title}' (ID: {doc_id}) with {len(chunks)} chunks.")
            return {
                "success": True,
                "doc_id": doc_id,
                "title": title,
                "chunks_created": len(chunks),
                "content_hash": content_hash
            }

        except Exception as e:
            logger.exception("Failed to ingest document")
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
_document_service_instance = None


def get_document_service() -> DocumentService:
    """Get or create the document service singleton instance"""
    global _document_service_instance
    if _document_service_instance is None:
        _document_service_instance = DocumentService()
    return _document_service_instance