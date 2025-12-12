"""
Structured analysis endpoints.

These endpoints provide more structured alternatives to free-form chat.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends

from api.models.requests import AnalyzeRequest
from api.models.responses import ParsedAnalysis
from api.models.chat import ChatMessage
from agent.moat_tutor import invoke_agent
from services.parser import AgentResponseParser
from services.session_store import SessionStore, get_session_store

router = APIRouter(prefix="/api/v1/analyze", tags=["analysis"])


@router.post("", response_model=ParsedAnalysis)
async def analyze_stock(
    request: AnalyzeRequest,
    store: SessionStore = Depends(get_session_store)
) -> ParsedAnalysis:
    """
    Perform a structured stock analysis using the MOAT framework.
    
    This endpoint provides a more predictable response format compared to free-form chat.
    It constructs a specific query for the agent based on the parameters and returns
    structured analysis results.
    
    The analysis includes:
    - Summary of stock movement
    - Key events during the period
    - Price behavior metrics
    - MOAT characteristics analysis
    - Plain-language explanation
    - Concept definitions
    - Learning options
    
    Example request:
    ```json
    {
        "ticker": "AAPL",
        "start_date": "2023-01-01",
        "end_date": "2023-02-28",
        "expertise_level": "beginner"
    }
    ```
    
    Args:
        request: Analysis request with ticker and date range
        store: Session store dependency
        
    Returns:
        Structured analysis with all sections parsed
        
    Raises:
        HTTPException: If there's an error performing the analysis
    """
    try:
        # Construct query based on expertise level
        expertise_prefix = ""
        if request.expertise_level == "beginner":
            expertise_prefix = "Explain like I'm new to investing: "
        elif request.expertise_level == "professional":
            expertise_prefix = "Provide a professional analyst view: "
        
        query = (
            f"{expertise_prefix}Explain why {request.ticker} stock moved "
            f"from {request.start_date} to {request.end_date} using the MOAT framework."
        )
        
        # Get or create session if provided
        session_id = request.session_id
        if session_id and not store.session_exists(session_id):
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        elif not session_id:
            session_id = store.create_session()
        
        # Get conversation history before adding new message
        previous_messages = store.get_messages(session_id)
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in previous_messages
        ]
        
        # Create user message
        user_message = ChatMessage(
            id=f"msg-{uuid.uuid4()}",
            role="user",
            content=query,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Store user message
        store.add_message(session_id, user_message)
        
        # Invoke agent with conversation history
        agent_response = invoke_agent(query, conversation_history)
        
        # Create assistant message
        assistant_message = ChatMessage(
            id=f"msg-{uuid.uuid4()}",
            role="assistant",
            content=agent_response,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Store assistant message
        store.add_message(session_id, assistant_message)
        
        # Parse the response into structured format
        parsed = AgentResponseParser.parse(
            agent_response,
            ticker=request.ticker,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        return parsed
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error performing analysis: {str(e)}"
        )


@router.get("/{ticker}/quick-summary")
async def get_quick_summary(ticker: str) -> dict:
    """
    Get a quick summary of a company's moat characteristics.
    
    This is a lightweight endpoint that returns basic moat information without
    invoking the full agent.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Quick moat summary
        
    Raises:
        HTTPException: If ticker not found
    """
    try:
        # Use the same moat data as the companies endpoint
        from api.routes.companies import MOAT_DB
        
        ticker_upper = ticker.upper()
        
        if ticker_upper not in MOAT_DB:
            raise HTTPException(
                status_code=404,
                detail=f"Moat data not available for ticker '{ticker}'"
            )
        
        moat_data = MOAT_DB[ticker_upper]
        
        # Create a summary string from the moat characteristics
        characteristics_summary = ", ".join([
            f"{char.name} ({char.strength})"
            for char in moat_data.characteristics
        ])
        
        return {
            "ticker": ticker_upper,
            "moat_summary": f"{moat_data.overall_moat_rating} moat: {characteristics_summary}",
            "overall_rating": moat_data.overall_moat_rating,
            "characteristics_count": len(moat_data.characteristics),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching moat summary: {str(e)}"
        )

