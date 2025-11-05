# Agent_Bot/session_manager.py
from typing import List, Dict, Any
import uuid

# --- Dummy Session/History Storage (REPLACE WITH REDIS LATER) ---
# A simple in-memory dictionary is NOT production ready, but works for local testing.
SESSION_STORE = {}

def load_session(session_id: str) -> List[Dict[str, Any]]:
    """Loads chat history for a session ID."""
    return SESSION_STORE.get(session_id, [])

def save_session(session_id: str, history: List[Dict[str, Any]]):
    """Saves chat history for a session ID."""
    SESSION_STORE[session_id] = history
    
def add_message_to_session(session_id: str, user_message: str, agent_response: str) -> List[Dict[str, Any]]:
    """Adds a human and AI message to the chat history."""
    history = load_session(session_id)
    history.append({"role": "human", "content": user_message})
    history.append({"role": "ai", "content": agent_response})
    save_session(session_id, history)
    return history