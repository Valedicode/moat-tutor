from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import chat, companies, analysis, sessions, health
from middleware.logging import LoggingMiddleware


def create_app() -> FastAPI:
    """
    Application factory for the MoatTutor backend.

    This creates a fully configured FastAPI application with:
    - All API routes
    - CORS middleware
    - Request logging
    - Error handling
    """
    app = FastAPI(
        title="MoatTutor Backend",
        description="FastAPI backend for MOAT-style stock explanation agent",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS – allow local frontend during development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",  # Alternative port
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add logging middleware
    app.add_middleware(LoggingMiddleware)

    # Include routers
    app.include_router(health.router)  # /health, /metrics, /ready, /live
    app.include_router(chat.router)  # /api/v1/chat
    app.include_router(companies.router)  # /api/v1/companies
    app.include_router(analysis.router)  # /api/v1/analyze
    app.include_router(sessions.router)  # /api/v1/sessions

    @app.get("/", tags=["root"])
    async def root() -> dict:
        """
        Root endpoint with API information.
        
        Returns:
            API information and available endpoints
        """
        return {
            "name": "MoatTutor Backend API",
            "version": "0.1.0",
            "description": "MOAT framework stock analysis agent",
            "docs": "/docs",
            "endpoints": {
                "health": "/health",
                "metrics": "/metrics",
                "chat": "/api/v1/chat",
                "analyze": "/api/v1/analyze",
                "companies": "/api/v1/companies",
                "sessions": "/api/v1/sessions",
            }
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


