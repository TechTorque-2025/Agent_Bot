# Agent_Bot/main.py
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from .models import ChatRequest, ChatResponse
from .service_clients import get_user_context
from .agent_core import run_agent
from .session_manager import load_session, add_message_to_session
import os
import uuid

# 1. Load Environment Variables
load_dotenv() 

# 2. Initialize FastAPI Application
app = FastAPI(
    title="TechTorque AI Agent Bot", 
    version="v1",
    root_path="/api/v1/ai" # Set the root path as per the API design
)

# 3. Health Check endpoint
@app.get("/health")
def health_check():
    return {"status": "Agent Bot is Running", "llm": os.getenv("GEMINI_MODEL", "gemini-2.5-flash")}

# 4. Main Chat Endpoint
@app.post("/chat", response_model=ChatResponse, summary="Send a query to the AI Agent")
async def chat_endpoint(request: ChatRequest):
    
    # 1. Authentication and Context Retrieval
    if not request.token:
        raise HTTPException(status_code=401, detail="Authentication token required.")

    user_context = get_user_context(request.token)
    
    if user_context.user_id == "ERROR":
         raise HTTPException(status_code=401, detail="Invalid or expired token.")

    # 2. Session ID Management
    session_id = request.session_id if request.session_id else str(uuid.uuid4())
    chat_history = load_session(session_id)
    
    # 3. Run the Agent
    try:
        reply = run_agent(
            query=request.query,
            chat_history=chat_history,
            user_context=user_context,
            token=request.token # Pass the token to the agent's core execution
        )
        
        # 4. Save History/State
        add_message_to_session(session_id, request.query, reply)

        return ChatResponse(reply=reply, session_id=session_id)
    
    except Exception as e:
        print(f"Agent Execution Error: {e}")
        # A generic 500 error is fine here for an LLM/Agent failure
        raise HTTPException(status_code=500, detail="The AI Agent encountered an internal error.")

# --- END OF CODE ---

# To run:
# 1. Ensure other services (Auth, Appointment, etc.) are running on port 8080.
# 2. Activate venv: venv\Scripts\activate
# 3. Run: uvicorn main:app --reload --port 8000