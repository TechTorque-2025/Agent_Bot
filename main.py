# main.py
from fastapi import FastAPI
from dotenv import load_dotenv
import os
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# We need to import the router directly
from routes.chatAgent import router as chatbot_router
from config.settings import settings # Use our new settings

app = FastAPI(
    title="TechTorque Unified AI Agent/RAG Service",
    description="Unified AI Agent for Tool Use and RAG for Knowledge Retrieval.",
    version="1.0.0"
)

# CORS is handled by API Gateway - no need for CORS middleware here
# This prevents duplicate Access-Control-Allow-Origin headers

# Include the main router
# NOTE: API Gateway strips /api/v1/ai prefix, so we don't need it here
app.include_router(chatbot_router, prefix="", tags=["ai_agent"])

@app.get("/")
async def root():
    return {
        "service": "TechTorque Unified AI Agent",
        "status": "running",
        "model": settings.GEMINI_MODEL,
        "api_endpoints": "/chat (via Gateway: /api/v1/ai/chat)",
        "rag_endpoints": "/rag/status (via Gateway: /api/v1/ai/rag/status)"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    # Use the port defined in our settings
    # Set reload=False for production stability
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=False)