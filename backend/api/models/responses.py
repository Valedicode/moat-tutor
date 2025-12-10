"""
Response models for API endpoints.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid ticker symbol",
                "detail": "Ticker 'XYZ' not found in database",
                "timestamp": "2025-12-10T15:30:00Z"
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(default="0.1.0", description="API version")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    llm_provider: Optional[str] = Field(None, description="LLM provider being used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "version": "0.1.0",
                "timestamp": "2025-12-10T15:30:00Z",
                "llm_provider": "openai"
            }
        }


class MoatAnalysis(BaseModel):
    """Moat characteristics analysis."""
    strengthened: List[str] = Field(
        default_factory=list,
        description="Moat characteristics that were strengthened"
    )
    weakened: List[str] = Field(
        default_factory=list,
        description="Moat characteristics that were weakened"
    )
    relevant: List[str] = Field(
        default_factory=list,
        description="Relevant moat characteristics"
    )
    explanation: Optional[str] = Field(
        None,
        description="Detailed moat analysis explanation"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "strengthened": ["Network Effects", "Intangible Assets"],
                "weakened": [],
                "relevant": ["Switching Costs"],
                "explanation": "Apple's ecosystem continued to expand..."
            }
        }


class LearningOption(BaseModel):
    """A learning path option for the user."""
    id: str = Field(..., description="Unique option identifier")
    label: str = Field(..., description="Display label for the option")
    description: str = Field(..., description="What this option provides")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "beginner-friendly",
                "label": "Beginner-Friendly",
                "description": "Explain this using everyday examples and simple analogies"
            }
        }


class ParsedAnalysis(BaseModel):
    """
    Structured analysis parsed from the agent's response.
    
    This represents the 9-section structure defined in the agent's system prompt:
    1. Summary
    2. Key Events
    3. Price Behavior
    4. MOAT Analysis
    5. Plain-Language Explanation
    6. Concept Definitions
    7. Learning Options
    8. Comprehension Check
    9. Next Steps
    """
    ticker: Optional[str] = Field(None, description="Stock ticker symbol")
    start_date: Optional[str] = Field(None, description="Analysis start date")
    end_date: Optional[str] = Field(None, description="Analysis end date")
    
    # Core Analysis Sections (1-5)
    summary: Optional[str] = Field(None, description="2-3 sentence overview")
    key_events: List[str] = Field(default_factory=list, description="Major news or developments")
    price_behavior: Optional[str] = Field(None, description="How the stock moved")
    moat_analysis: Optional[MoatAnalysis] = Field(None, description="MOAT characteristics analysis")
    plain_explanation: Optional[str] = Field(None, description="Simple terms explanation")
    
    # Teaching Layer (6)
    concept_definitions: Dict[str, str] = Field(
        default_factory=dict,
        description="Financial concepts with their definitions"
    )
    
    # Interactive Learning (7-9)
    learning_options: List[LearningOption] = Field(
        default_factory=list,
        description="Available learning paths"
    )
    comprehension_questions: List[str] = Field(
        default_factory=list,
        description="Questions to verify understanding"
    )
    next_steps: List[str] = Field(
        default_factory=list,
        description="Suggested next actions"
    )
    
    # Raw response for fallback
    raw_response: Optional[str] = Field(None, description="Full unstructured agent response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "start_date": "2023-01-01",
                "end_date": "2023-02-28",
                "summary": "Apple's stock gained 8.35% during Q1 2023...",
                "key_events": [
                    "Strong quarterly earnings beat expectations",
                    "New product launch received positive reviews"
                ],
                "price_behavior": "Period Return: +8.35%, High: $165.40",
                "moat_analysis": {
                    "strengthened": ["Network Effects"],
                    "weakened": [],
                    "relevant": ["Intangible Assets", "Switching Costs"],
                    "explanation": "Apple's ecosystem lock-in strengthened..."
                },
                "plain_explanation": "Apple did well because...",
                "concept_definitions": {
                    "Network Effects": "A product becomes more valuable as more people use it",
                    "Rally": "A sustained increase in stock price over a period"
                },
                "learning_options": [],
                "comprehension_questions": [
                    "Which event had the biggest impact on the stock?"
                ],
                "next_steps": [
                    "Would you like a quiz on today's concepts?"
                ]
            }
        }

