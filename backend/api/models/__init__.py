"""
Pydantic models for API requests and responses.
"""

from .chat import ChatMessage, ChatRequest, ChatResponse, SessionInfo
from .responses import (
    ErrorResponse,
    HealthResponse,
    ParsedAnalysis,
    LearningOption,
    MoatAnalysis,
)
from .requests import AnalyzeRequest
from .company import Company, CompanyMoat

__all__ = [
    # Chat models
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "SessionInfo",
    # Response models
    "ErrorResponse",
    "HealthResponse",
    "ParsedAnalysis",
    "LearningOption",
    "MoatAnalysis",
    # Request models
    "AnalyzeRequest",
    # Company models
    "Company",
    "CompanyMoat",
]

