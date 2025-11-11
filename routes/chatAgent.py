# routes/chatAgent.py
from fastapi import APIRouter, HTTPException, Header, status
from models.chat import ChatRequest, ChatResponse
from services.agent_core import get_agent_service
from services.rag import get_rag_service # For RAG utility endpoints
from services.document import get_document_service # For document ingestion
from services.conversation import get_conversation_service # For session creation
from datetime import datetime

router = APIRouter()

# Instantiate services
agent_service = get_agent_service()
conv_service = get_conversation_service()
doc_service = get_document_service()
rag_service = get_rag_service()

@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_with_agent(
    request: ChatRequest,
    # The JWT is passed in the body for the Python Agent's internal use.
    # The API Gateway validates the token first.
):
    """
    Main chat endpoint. Receives user message, manages session, and invokes the AI Agent.
    """
    try:
        # 1. Session Management
        session_id = request.session_id if request.session_id else conv_service.create_session(user_id="anonymous" if not request.token else "authenticated_user")
        
        # 2. Get history for LangChain prompt
        chat_history = conv_service.get_history(session_id, limit=5)
        
        # 3. Invoke the Agent
        agent_result = await agent_service.invoke_agent(
            user_query=request.query,
            session_id=session_id,
            user_token=request.token,
            chat_history=chat_history
        )
        
        # 4. Update conversation history (crucial for context)
        conv_service.add_message(session_id, "user", request.query)
        conv_service.add_message(session_id, "assistant", agent_result.get("output", "Error processing request."))

        return ChatResponse(
            reply=agent_result.get("output", "I'm having trouble connecting to my brain right now. Please try again."),
            session_id=session_id,
            tool_executed=agent_result.get("tool_executed")
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Agent Error: {str(e)}")

# --- RAG Utility Endpoints (For Management Scripts) ---

@router.get("/rag/status")
async def get_rag_system_status():
    """Get the current status of the RAG system (Embedding, Vector Store)."""
    return rag_service.get_service_status()

@router.post("/documents/ingest")
async def ingest_document_route(title: str, content: str, doc_type: str = "general", source: str = "manual"):
    """Ingest a single document into the Vector Knowledge Base."""
    return doc_service.ingest_document(
        content=content,
        title=title,
        doc_type=doc_type,
        source=source
    )

@router.post("/documents/batch-ingest")
async def batch_ingest_documents_route(documents: List[Dict[str, Any]]):
    """Ingest multiple documents into the Vector Knowledge Base."""
    return doc_service.ingest_multiple_documents(documents)

@router.get("/health")
async def health():
    """Service health check with RAG status."""
    return {
        "status": "healthy",
        "rag_enabled": rag_service.is_available(),
        "vector_store": rag_service.get_service_status().get("vector_store")
    }