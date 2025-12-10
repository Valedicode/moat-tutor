"""
Chat-related Pydantic models.
"""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """
    Represents a single chat message.
    Aligns with frontend Message type.
    """
    id: str = Field(..., description="Unique message identifier")
    role: Literal["user", "assistant"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "role": "user",
                "content": "Explain why AAPL moved in Q1 2023",
                "timestamp": "2025-12-10T15:30:00Z"
            }
        }


class ChatRequest(BaseModel):
    """Request model for chatting with the MoatTutor agent."""
    query: str = Field(..., description="User's natural language query", min_length=1)
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation continuity")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Explain why Apple stock moved from 2023-01-01 to 2023-02-28",
                "session_id": "session-123"
            }
        }


class ChatResponse(BaseModel):
    """
    Response model for chat endpoint.
    Includes both the raw agent response and parsed structured data.
    """
    message: ChatMessage = Field(..., description="The assistant's message")
    session_id: str = Field(..., description="Session identifier")
    parsed: Optional["ParsedAnalysis"] = Field(
        None,
        description="Structured analysis if available"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": {
                    "id": "msg-456",
                    "role": "assistant",
                    "content": "Summary: Apple's stock gained 8.35%...",
                    "timestamp": "2025-12-10T15:30:05Z"
                },
                "session_id": "session-123",
                "parsed": None
            }
        }


class SessionInfo(BaseModel):
    """Information about a chat session."""
    session_id: str = Field(..., description="Session identifier")
    messages: List[ChatMessage] = Field(default_factory=list, description="Messages in this session")
    created_at: str = Field(..., description="Session creation timestamp")
    last_activity: str = Field(..., description="Last activity timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session-123",
                "messages": [],
                "created_at": "2025-12-10T15:00:00Z",
                "last_activity": "2025-12-10T15:30:00Z"
            }
        }


# Forward reference resolution
from .responses import ParsedAnalysis
ChatResponse.model_rebuild()

