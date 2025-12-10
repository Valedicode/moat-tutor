from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.moat_tutor import invoke_agent


class ChatRequest(BaseModel):
    """Request model for chatting with the MoatTutor agent."""
    query: str


def create_app() -> FastAPI:
    """
    Application factory for the MoatTutor backend.

    This keeps things flexible if we later add settings, routers, or lifespan events.
    """
    app = FastAPI(
        title="MoatTutor Backend",
        description="FastAPI backend for MOAT-style stock explanation agent",
        version="0.1.0",
    )

    # CORS – allow local frontend during development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["system"])
    async def health() -> dict:
        """Simple health check endpoint."""
        return {"status": "ok"}

    @app.post("/chat", tags=["agent"])
    async def chat(request: ChatRequest) -> dict:
        """
        Chat with the MoatTutor agent using natural language.
        
        The agent will automatically determine which tools to use based on your query.
        You can ask about stock movements, moat characteristics, news, or prices.
        
        Examples:
        - "Explain why AAPL stock moved from 2023-01-01 to 2023-02-28"
        - "What are Microsoft's competitive advantages?"
        - "Get news for GOOGL in March 2023"
        - "Show me price data for AMZN from Jan to Feb 2023"
        
        Args:
            request: ChatRequest with the user's natural language query
        
        Returns:
            Agent's response with explanation and analysis
        """
        try:
            response = invoke_agent(request.query)
            return {
                "query": request.query,
                "response": response,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app


app = create_app()


