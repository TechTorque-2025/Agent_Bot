#!/usr/bin/env python3
"""
Script to upload knowledge base documents to Pinecone vector database
Run this after creating/updating knowledge base documents
"""
import os
import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import document service
from services.document import get_document_service

def load_knowledge_documents():
    """Load all knowledge documents from the knowledge_base directory"""
    knowledge_dir = Path(__file__).parent / "knowledge_base"

    if not knowledge_dir.exists():
        logger.error(f"Knowledge base directory not found: {knowledge_dir}")
        return []

    documents = []
    for file_path in sorted(knowledge_dir.glob("*.txt")):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract title from first line or filename
            title = content.split('\n')[0].strip() if content else file_path.stem

            # Determine document type from filename
            filename_lower = file_path.stem.lower()
            if 'service' in filename_lower:
                doc_type = 'services'
            elif 'appointment' in filename_lower or 'booking' in filename_lower:
                doc_type = 'appointments'
            elif 'pricing' in filename_lower or 'payment' in filename_lower:
                doc_type = 'pricing'
            elif 'warranty' in filename_lower or 'policy' in filename_lower:
                doc_type = 'warranty'
            elif 'company' in filename_lower or 'hours' in filename_lower:
                doc_type = 'company_info'
            else:
                doc_type = 'general'

            documents.append({
                'content': content,
                'title': title,
                'doc_type': doc_type,
                'source': file_path.name,
                'metadata': {
                    'filename': file_path.name,
                    'file_path': str(file_path)
                }
            })

            logger.info(f"Loaded document: {file_path.name} ({len(content)} chars)")

        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")

    return documents

def main():
    """Main function to upload knowledge base"""
    print("=" * 70)
    print("TechTorque Knowledge Base Upload Script")
    print("=" * 70)
    print()

    # Load documents
    print("[*] Loading knowledge documents...")
    documents = load_knowledge_documents()

    if not documents:
        print("[ERROR] No documents found to upload!")
        sys.exit(1)

    print(f"[OK] Loaded {len(documents)} documents")
    print()

    # Get document service
    print("[*] Initializing document service...")
    try:
        doc_service = get_document_service()
        print("[OK] Document service ready")
    except Exception as e:
        print(f"[ERROR] Failed to initialize document service: {e}")
        sys.exit(1)

    print()

    # Upload documents
    print("[*] Uploading documents to Pinecone...")
    print()

    result = doc_service.ingest_multiple_documents(documents)

    # Display results
    print("=" * 70)
    print("UPLOAD RESULTS")
    print("=" * 70)
    print(f"Total Documents: {result['total']}")
    print(f"[OK] Successful: {result['successful']}")
    print(f"[ERROR] Failed: {result['failed']}")
    print()

    # Show detailed results
    for i, doc_result in enumerate(result['results'], 1):
        if doc_result.get('success'):
            print(f"{i}. [OK] {doc_result['title']}")
            print(f"   Doc ID: {doc_result['doc_id']}")
            print(f"   Chunks: {doc_result['chunks_created']}")
        else:
            print(f"{i}. [ERROR] Failed")
            print(f"   Error: {doc_result.get('error', 'Unknown error')}")
        print()

    print("=" * 70)
    if result['successful'] == result['total']:
        print("[SUCCESS] All documents uploaded successfully!")
        print("Your chatbot is now ready with comprehensive knowledge!")
    else:
        print(f"[WARNING] Some documents failed to upload. Check the logs above.")
    print("=" * 70)

if __name__ == "__main__":
    main()
