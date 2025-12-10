"""
Health check and system status endpoints.
"""

import os
from datetime import datetime

from fastapi import APIRouter

from api.models.responses import HealthResponse
from services.session_store import get_session_store

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Comprehensive health check endpoint.
    
    Returns system status, version, and LLM configuration.
    Useful for monitoring and load balancer health checks.
    
    Returns:
        Health status information
    """
    # Get LLM provider from environment
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    
    return HealthResponse(
        status="ok",
        version="0.1.0",
        timestamp=datetime.utcnow().isoformat(),
        llm_provider=llm_provider
    )


@router.get("/metrics")
async def get_metrics() -> dict:
    """
    Get system metrics.
    
    Returns information about:
    - Active sessions
    - Total messages
    - System uptime
    
    Returns:
        System metrics
    """
    store = get_session_store()
    sessions = store.list_sessions()
    
    total_messages = sum(len(session.messages) for session in sessions)
    
    return {
        "active_sessions": len(sessions),
        "total_messages": total_messages,
        "timestamp": datetime.utcnow().isoformat(),
        "service": "moat-tutor-backend",
        "version": "0.1.0"
    }


@router.get("/ready")
async def readiness_check() -> dict:
    """
    Kubernetes readiness probe endpoint.
    
    Checks if the service is ready to handle requests.
    
    Returns:
        Readiness status
    """
    # In production, you might check:
    # - Database connections
    # - External API availability
    # - LLM availability
    
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/live")
async def liveness_check() -> dict:
    """
    Kubernetes liveness probe endpoint.
    
    Simple check to verify the service is alive.
    
    Returns:
        Liveness status
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat()
    }

