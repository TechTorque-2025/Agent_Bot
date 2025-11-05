# Agent_Bot/models.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# --- API Communication Models (main.py) ---
class ChatRequest(BaseModel):
    query: str = Field(..., description="The user's query for the chatbot.")
    session_id: Optional[str] = Field(None, description="The current conversation session ID.")
    token: str = Field(..., description="The user's JWT for authentication and context retrieval.")

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    
# --- Service Client Models (Context) ---
class Vehicle(BaseModel):
    id: str
    make: str
    model: str
    license_plate: str

class UserContext(BaseModel):
    user_id: str
    full_name: str
    vehicles: List[Vehicle]