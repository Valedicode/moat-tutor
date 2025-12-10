"""
Session management endpoints.
"""

from typing import List

from fastapi import APIRouter, HTTPException, Depends

from api.models.chat import SessionInfo
from services.session_store import SessionStore, get_session_store

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.post("", response_model=dict)
async def create_session(
    store: SessionStore = Depends(get_session_store)
) -> dict:
    """
    Create a new chat session.
    
    Sessions are used to maintain conversation context across multiple
    chat interactions.
    
    Returns:
        New session ID
        
    Example response:
    ```json
    {
        "session_id": "session-123e4567-e89b-12d3-a456-426614174000"
    }
    ```
    """
    session_id = store.create_session()
    
    return {
        "session_id": session_id,
        "message": "Session created successfully"
    }


@router.get("/{session_id}", response_model=SessionInfo)
async def get_session(
    session_id: str,
    store: SessionStore = Depends(get_session_store)
) -> SessionInfo:
    """
    Get information about a specific session.
    
    Returns the session metadata and all messages in the conversation.
    
    Args:
        session_id: Session identifier
        store: Session store dependency
        
    Returns:
        Session information with message history
        
    Raises:
        HTTPException: If session not found
    """
    session = store.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    
    return session


@router.get("", response_model=List[SessionInfo])
async def list_sessions(
    store: SessionStore = Depends(get_session_store)
) -> List[SessionInfo]:
    """
    List all active sessions.
    
    Returns:
        List of all sessions with their metadata
    """
    return store.list_sessions()


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    store: SessionStore = Depends(get_session_store)
) -> dict:
    """
    Delete a session and all its messages.
    
    Args:
        session_id: Session identifier
        store: Session store dependency
        
    Returns:
        Success confirmation
        
    Raises:
        HTTPException: If session not found
    """
    success = store.delete_session(session_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    
    return {
        "success": True,
        "message": f"Session {session_id} deleted successfully"
    }


@router.delete("")
async def clear_all_sessions(
    store: SessionStore = Depends(get_session_store)
) -> dict:
    """
    Clear all sessions.
    
    WARNING: This will delete all conversation history.
    Useful for development/testing.
    
    Returns:
        Success confirmation
    """
    store.clear_all()
    
    return {
        "success": True,
        "message": "All sessions cleared"
    }

