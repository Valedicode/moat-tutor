from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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

    @app.get("/explain", tags=["explanations"])
    async def explain(
        ticker: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """
        Placeholder explanation endpoint.

        Later this will call into LangChain / LangGraph with real data.
        """
        return {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "explanation": "This is a placeholder explanation. Backend wiring is working.",
        }

    return app


app = create_app()


