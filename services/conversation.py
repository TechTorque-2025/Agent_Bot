# services/conversation.py


from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import uuid
import json

logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self, max_history_length: int = 10, ttl_minutes: int = 60):
        self.conversations = {}
        self.max_history_length = max_history_length
        self.ttl_minutes = ttl_minutes

    def create_session(self, user_id: Optional[str] = None) -> str:
        session_id = str(uuid.uuid4())
        self.conversations[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [],
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "metadata": {}
        }
        logger.info(f"Created new conversation session: {session_id}")
        return session_id

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        if session_id not in self.conversations:
            logger.warning(f"Session {session_id} not found")
            return False

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }

        conversation = self.conversations[session_id]
        conversation["messages"].append(message)
        conversation["last_activity"] = datetime.utcnow()

        if len(conversation["messages"]) > self.max_history_length:
            conversation["messages"] = conversation["messages"][-self.max_history_length:]

        return True

    def get_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if session_id not in self.conversations:
            return []

        messages = self.conversations[session_id]["messages"]
        if limit:
            messages = messages[-limit:]
        return messages
    
    # ... (Other methods omitted for brevity but should be in the file)

_conversation_service_instance = None
def get_conversation_service() -> ConversationService:
    global _conversation_service_instance
    if _conversation_service_instance is None:
        _conversation_service_instance = ConversationService()
    return _conversation_service_instance

