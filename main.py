# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the main router
# NOTE: We use the prefix /api/v1/ai as per our original design
app.include_router(chatbot_router, prefix="/api/v1/ai", tags=["ai_agent"])

@app.get("/")
async def root():
    return {
        "service": "TechTorque Unified AI Agent",
        "status": "running",
        "model": settings.GEMINI_MODEL,
        "api_endpoints": "/api/v1/ai/chat",
        "rag_endpoints": "/api/v1/ai/rag/status"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    # Use the port defined in our settings
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)