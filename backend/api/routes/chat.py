"""
Chat endpoints for MoatTutor agent interaction.
"""

import uuid
import os
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
import json

from api.models.chat import ChatRequest, ChatResponse, ChatMessage, SessionInfo
from api.models.responses import ErrorResponse
from agent.moat_tutor import invoke_agent, stream_agent_messages
from services.parser import AgentResponseParser
from services.session_store import SessionStore, get_session_store

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# Maximum number of messages to include in conversation history
# Prevents unbounded context growth; keeps most recent exchanges
# TODO: For future implementation, consider using LangGraph's MemorySaver
# with summarization middleware for smarter context management
# See: https://docs.langchain.com/oss/langchain/short-term-memory
MAX_HISTORY_MESSAGES = 50

# Optional tiny delay between SSE delta chunks (ms) to give UI a perceivable stream.
# Default 10ms. Set to 0 to push every token immediately.
STREAM_TOKEN_DELAY_MS = int(os.getenv("STREAM_TOKEN_DELAY_MS", "0"))
STREAM_TOKEN_DELAY_SEC = max(0.0, STREAM_TOKEN_DELAY_MS / 1000.0)


def _build_enhanced_query(query: str, ticker: Optional[str], start_date: Optional[str], end_date: Optional[str]) -> str:
    """
    Enhance the user query with context from selected company and date range.
    
    If ticker and dates are provided, they are prepended to give the agent
    explicit context about what to analyze.
    """
    if not ticker:
        return query
    
    context_parts = [f"[Context: Analyzing {ticker}"]
    if start_date and end_date:
        context_parts.append(f" from {start_date} to {end_date}")
    context_parts.append("]")
    
    context = "".join(context_parts)
    return f"{context}\n\n{query}"


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    store: SessionStore = Depends(get_session_store)
) -> ChatResponse:
    """
    Chat with the MoatTutor agent using natural language.
    
    The agent will automatically determine which tools to use based on your query.
    You can ask about stock movements, moat characteristics, news, or prices.
    
    The response includes:
    - The agent's message
    - Session ID for conversation continuity
    - Parsed structured data (if available)
    
    Examples:
    ```json
    {
        "query": "Explain why AAPL stock moved from 2023-01-01 to 2023-02-28",
        "session_id": "session-123"
    }
    ```
    
    Args:
        request: ChatRequest with query and optional session_id
        store: Session store dependency
        
    Returns:
        ChatResponse with agent's message and parsed analysis
        
    Raises:
        HTTPException: If there's an error invoking the agent
    """
    try:
        # Get or create session
        session_id = request.session_id
        if session_id and not store.session_exists(session_id):
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        elif not session_id:
            session_id = store.create_session()
        
        # Create user message
        user_message = ChatMessage(
            id=f"msg-{uuid.uuid4()}",
            role="user",
            content=request.query,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Store user message
        store.add_message(session_id, user_message)
        
        # Get conversation history (exclude the message we just added)
        previous_messages = store.get_messages(session_id)[:-1]
        # Trim to last N messages to prevent unbounded context growth
        if len(previous_messages) > MAX_HISTORY_MESSAGES:
            previous_messages = previous_messages[-MAX_HISTORY_MESSAGES:]
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in previous_messages
        ]
        
        # Build enhanced query with context
        enhanced_query = _build_enhanced_query(
            request.query, request.ticker, request.start_date, request.end_date
        )
        
        # Invoke agent with conversation history
        agent_response = invoke_agent(enhanced_query, conversation_history)
        
        # Create assistant message
        assistant_message = ChatMessage(
            id=f"msg-{uuid.uuid4()}",
            role="assistant",
            content=agent_response,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Store assistant message
        store.add_message(session_id, assistant_message)
        
        # Try to parse the response into structured data
        parsed = None
        try:
            parsed = AgentResponseParser.parse(agent_response)
        except Exception as parse_error:
            # If parsing fails, we still return the raw response
            # Log the error but don't fail the request
            print(f"Warning: Failed to parse agent response: {parse_error}")
        
        return ChatResponse(
            message=assistant_message,
            session_id=session_id,
            parsed=parsed
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    store: SessionStore = Depends(get_session_store)
):
    """
    Stream chat responses from the MoatTutor agent using Server-Sent Events (SSE).

    Emits events:
    - event: meta   data: {"session_id": "...", "message_id": "..."}
    - event: delta  data: {"delta": "..."}
    - event: done   data: {"message": {...}, "session_id": "...", "parsed": ...}
    - event: error  data: {"error": "..."}  (best-effort)
    """
    # Get or create session
    session_id = request.session_id
    if session_id and not store.session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    elif not session_id:
        session_id = store.create_session()

    # Create/store user message immediately
    user_message = ChatMessage(
        id=f"msg-{uuid.uuid4()}",
        role="user",
        content=request.query,
        timestamp=datetime.utcnow().isoformat()
    )
    store.add_message(session_id, user_message)

    assistant_message_id = f"msg-{uuid.uuid4()}"

    def _sse(event: str, data_obj) -> str:
        return f"event: {event}\ndata: {json.dumps(data_obj, ensure_ascii=False)}\n\n"

    async def event_generator():
        full_text_parts: list[str] = []
        try:
            # Send meta first so client can persist session immediately
            yield _sse("meta", {"session_id": session_id, "message_id": assistant_message_id})

            # Get conversation history (exclude the user message we just added)
            previous_messages = store.get_messages(session_id)[:-1]
            # Trim to last N messages to prevent unbounded context growth
            if len(previous_messages) > MAX_HISTORY_MESSAGES:
                previous_messages = previous_messages[-MAX_HISTORY_MESSAGES:]
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in previous_messages
            ]
            
            # Build enhanced query with context
            enhanced_query = _build_enhanced_query(
                request.query, request.ticker, request.start_date, request.end_date
            )
            stream_iter = stream_agent_messages(enhanced_query, conversation_history)

            # stream_agent_messages may return an async generator or a sync generator
            if hasattr(stream_iter, "__aiter__"):
                async for token, metadata in stream_iter:
                    delta = _extract_text_delta(token)
                    if not delta:
                        continue
                    full_text_parts.append(delta)
                    yield _sse("delta", {"delta": delta})
                    if STREAM_TOKEN_DELAY_SEC > 0:
                        await asyncio.sleep(STREAM_TOKEN_DELAY_SEC)
            else:
                for token, metadata in stream_iter:
                    delta = _extract_text_delta(token)
                    if not delta:
                        continue
                    full_text_parts.append(delta)
                    yield _sse("delta", {"delta": delta})
                    if STREAM_TOKEN_DELAY_SEC > 0:
                        await asyncio.sleep(STREAM_TOKEN_DELAY_SEC)

            full_text = "".join(full_text_parts).strip()

            assistant_message = ChatMessage(
                id=assistant_message_id,
                role="assistant",
                content=full_text,
                timestamp=datetime.utcnow().isoformat()
            )
            store.add_message(session_id, assistant_message)

            parsed = None
            try:
                parsed = AgentResponseParser.parse(full_text)
            except Exception as parse_error:
                print(f"Warning: Failed to parse agent response: {parse_error}")

            yield _sse("done", {"message": assistant_message.model_dump(), "session_id": session_id, "parsed": parsed.model_dump() if parsed else None})
        except Exception as e:
            yield _sse("error", {"error": str(e)})

    def _extract_text_delta(token) -> str:
        """
        Extract only user-visible text from LangChain streamed message chunks.

        We intentionally ignore tool_call chunks and other non-text blocks.
        """
        try:
            blocks = getattr(token, "content_blocks", None)
            if not blocks:
                # Some integrations stream plain content
                content = getattr(token, "content", None)
                if isinstance(content, str) and content:
                    return content
                return ""

            parts = []
            for block in blocks:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text") or ""
                    if text:
                        parts.append(text)
            return "".join(parts)
        except Exception:
            return ""

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/stream-test")
async def stream_test():
    """
    Diagnostic endpoint to test SSE streaming without LLM.
    
    Visit /api/v1/chat/stream-test in the browser or curl to verify
    that chunked streaming actually works from the backend.
    """
    import time
    
    async def test_generator():
        for i in range(10):
            yield f"data: chunk {i + 1} of 10\n\n"
            await asyncio.sleep(0.3)  # 300ms delay between chunks
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        test_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history/{session_id}", response_model=SessionInfo)
async def get_chat_history(
    session_id: str,
    store: SessionStore = Depends(get_session_store)
) -> SessionInfo:
    """
    Get the chat history for a session.
    
    Args:
        session_id: Session identifier
        store: Session store dependency
        
    Returns:
        SessionInfo with all messages
        
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


@router.delete("/{session_id}")
async def clear_session(
    session_id: str,
    store: SessionStore = Depends(get_session_store)
) -> dict:
    """
    Clear a chat session (delete all messages).
    
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
        "message": f"Session {session_id} deleted"
    }

