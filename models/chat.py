# models/chat.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# --- API Request/Response Models ---
class ChatRequest(BaseModel):
    query: str = Field(..., description="The user's query for the chatbot.")
    session_id: Optional[str] = Field(None, description="The current conversation session ID.")
    token: Optional[str] = Field(None, description="The user's JWT for context and auth propagation.")
    
class ChatResponse(BaseModel):
    reply: str = Field(..., description="The AI Agent's final response.")
    session_id: str = Field(..., description="The session ID used for context.")
    tool_executed: Optional[str] = Field(None, description="Name of the tool executed, if any.")
    
# --- Microservice Client Models (Context) ---
class VehicleInfo(BaseModel):
    id: str
    make: str
    model: str
    license_plate: str

class UserContext(BaseModel):
    user_id: str = Field(..., description="User ID from JWT sub claim.")
    full_name: str = Field(..., description="User's full name/username.")
    role: str = Field(..., description="User's highest role (CUSTOMER, EMPLOYEE, etc.).")
    vehicles: List[VehicleInfo] = []