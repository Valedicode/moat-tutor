"""
In-memory session storage for conversation management.

This is a simple implementation for MVP. In production, you'd want to use
a proper database (Redis, PostgreSQL, etc.) for persistence.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from api.models.chat import ChatMessage, SessionInfo


class SessionStore:
    """
    In-memory storage for chat sessions.
    
    Each session contains:
    - session_id: Unique identifier
    - messages: List of chat messages
    - created_at: When the session was created
    - last_activity: Last message timestamp
    """
    
    def __init__(self):
        """Initialize an empty session store."""
        self._sessions: Dict[str, SessionInfo] = {}
    
    def create_session(self) -> str:
        """
        Create a new session and return its ID.
        
        Returns:
            New session ID
        """
        session_id = f"session-{uuid.uuid4()}"
        now = datetime.utcnow().isoformat()
        
        self._sessions[session_id] = SessionInfo(
            session_id=session_id,
            messages=[],
            created_at=now,
            last_activity=now
        )
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionInfo if found, None otherwise
        """
        return self._sessions.get(session_id)
    
    def add_message(self, session_id: str, message: ChatMessage) -> None:
        """
        Add a message to a session.
        
        Args:
            session_id: Session identifier
            message: Message to add
            
        Raises:
            KeyError: If session doesn't exist
        """
        if session_id not in self._sessions:
            raise KeyError(f"Session {session_id} not found")
        
        self._sessions[session_id].messages.append(message)
        self._sessions[session_id].last_activity = message.timestamp
    
    def get_messages(self, session_id: str) -> List[ChatMessage]:
        """
        Get all messages in a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of messages (empty if session doesn't exist)
        """
        session = self._sessions.get(session_id)
        return session.messages if session else []
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if session didn't exist
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def list_sessions(self) -> List[SessionInfo]:
        """
        List all sessions.
        
        Returns:
            List of all SessionInfo objects
        """
        return list(self._sessions.values())
    
    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session exists
        """
        return session_id in self._sessions
    
    def clear_all(self) -> None:
        """Clear all sessions (useful for testing)."""
        self._sessions.clear()


# Global session store instance
# In production, consider using dependency injection
_session_store = SessionStore()


def get_session_store() -> SessionStore:
    """
    Get the global session store instance.
    
    This can be used as a FastAPI dependency:
    ```python
    @app.get("/sessions")
    def list_sessions(store: SessionStore = Depends(get_session_store)):
        return store.list_sessions()
    ```
    
    Returns:
        SessionStore instance
    """
    return _session_store

