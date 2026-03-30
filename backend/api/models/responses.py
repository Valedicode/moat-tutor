"""
Response models for API endpoints.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal

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


class MoatDimensionScore(BaseModel):
    """Score for a single moat dimension."""
    score: float = Field(..., ge=0, le=5, description="Strength score (0-5)")
    direction: str = Field(..., description="Strengthening, Stable, or Weakening")
    confidence: str = Field(..., description="Low, Medium, or High")
    rationale: str = Field(..., description="One causal chain: Signal → Mechanism → Moat Impact")
    
    class Config:
        json_schema_extra = {
            "example": {
                "score": 4.5,
                "direction": "Strengthening",
                "confidence": "High",
                "rationale": "Enterprise AI adoption (signal) increases switching costs (mechanism) as customers build infrastructure on CUDA platform (moat impact)."
            }
        }


class MoatAssessment(BaseModel):
    """
    Complete moat assessment from agent analysis.
    
    Based on analysis of price development and financial news, this provides
    quantified moat scores across five dimensions plus an overall rating.
    """
    # Dimension scores
    switching_costs: MoatDimensionScore = Field(..., description="Cost/difficulty for customers to switch to competitors")
    network_effects: MoatDimensionScore = Field(..., description="Value increases as more users join the platform")
    intangible_assets: MoatDimensionScore = Field(..., description="Brand, patents, proprietary data, regulatory advantages")
    cost_advantages: MoatDimensionScore = Field(..., description="Ability to produce goods/services cheaper due to scale or unique resources")
    efficient_scale: MoatDimensionScore = Field(..., description="Market only supports limited competitors profitably due to natural size constraints")
    
    # Overall assessment
    overall_score: float = Field(..., ge=0, le=5, description="Average of dimension scores")
    overall_rating: str = Field(..., description="Wide, Narrow, or None")
    overall_confidence: str = Field(..., description="Low, Medium, or High")
    assessment_period: str = Field(..., description="Date range analyzed (e.g., '2024-01-01 to 2024-12-31')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "switching_costs": {
                    "score": 4.5,
                    "direction": "Strengthening",
                    "confidence": "High",
                    "rationale": "Enterprise AI adoption increases switching costs as customers build on CUDA."
                },
                "network_effects": {
                    "score": 3.8,
                    "direction": "Stable",
                    "confidence": "Medium",
                    "rationale": "Developer ecosystem remains strong but not expanding materially."
                },
                "intangible_assets": {
                    "score": 4.7,
                    "direction": "Strengthening",
                    "confidence": "High",
                    "rationale": "Patent portfolio and CUDA platform strengthen brand in AI computing."
                },
                "cost_advantages": {
                    "score": 4.0,
                    "direction": "Stable",
                    "confidence": "Medium",
                    "rationale": "Scale advantages in R&D maintained but competition increasing."
                },
                "efficient_scale": {
                    "score": 2.5,
                    "direction": "Stable",
                    "confidence": "Medium",
                    "rationale": "Market size limits the number of viable competitors in high-end GPU design, but efficient scale is not the primary moat driver."
                },
                "overall_score": 4.0,
                "overall_rating": "Wide",
                "overall_confidence": "High",
                "assessment_period": "2024-01-01 to 2024-12-31"
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


class ChartDataResponse(BaseModel):
    """
    Chart-ready OHLCV data with adaptive interval resampling.
    
    This response is optimized for frontend charting libraries like Recharts, D3, or Chart.js.
    The interval is automatically determined based on the date range to balance detail and performance.
    """
    ticker: str = Field(..., description="Stock ticker symbol")
    interval: str = Field(..., description="Time interval used ('D', 'W', or 'M')")
    interval_display: str = Field(..., description="Human-readable interval (Daily, Weekly, Monthly)")
    start_date: str = Field(..., description="Actual start date of returned data (YYYY-MM-DD)")
    end_date: str = Field(..., description="Actual end date of returned data (YYYY-MM-DD)")
    data_points: int = Field(..., description="Number of data points returned")
    dates: List[str] = Field(..., description="ISO format dates for each data point")
    open: List[float] = Field(..., description="Opening prices")
    high: List[float] = Field(..., description="High prices")
    low: List[float] = Field(..., description="Low prices")
    close: List[float] = Field(..., description="Closing prices")
    volume: List[int] = Field(..., description="Trading volumes")
    adj_close: Optional[List[float]] = Field(None, description="Adjusted closing prices (if available)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "interval": "W",
                "interval_display": "Weekly",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "data_points": 52,
                "dates": ["2023-01-02T00:00:00", "2023-01-09T00:00:00"],
                "open": [130.28, 132.04],
                "high": [133.41, 135.92],
                "low": [129.89, 131.66],
                "close": [132.31, 135.45],
                "volume": [654321000, 712345000],
                "adj_close": [132.31, 135.45]
            }
        }


class ParsedAnalysis(BaseModel):
    """
    Structured analysis parsed from the agent's response.
    
    This represents the 5-section structure defined in the agent's system prompt:
    1. Executive Takeaway
    2. Price Signal → Market Interpretation
    3. News Signals → Moat-Relevant Themes
    4. Moat Reasoning (Causal Analysis)
    5. Uncertainty & What Would Change the View
    
    Plus the structured moat assessment with dimension scores.
    """
    ticker: Optional[str] = Field(None, description="Stock ticker symbol")
    start_date: Optional[str] = Field(None, description="Analysis start date")
    end_date: Optional[str] = Field(None, description="Analysis end date")
    
    # Core Analysis Sections (1-5)
    summary: Optional[str] = Field(None, description="Executive takeaway (max 4 sentences)")
    key_events: List[str] = Field(default_factory=list, description="Major news or developments")
    price_behavior: Optional[str] = Field(None, description="Price signal and market interpretation")
    moat_analysis: Optional[MoatAnalysis] = Field(None, description="MOAT characteristics analysis (legacy)")
    plain_explanation: Optional[str] = Field(None, description="Moat reasoning with causal chains")
    
    # Structured Moat Assessment (new)
    moat_assessment: Optional[MoatAssessment] = Field(None, description="Quantified moat scores and rating")
    
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


class WindowedMoatReport(BaseModel):
    """
    Windowed moat analysis report with time-window-specific context.
    
    Includes the window metadata, policy constraints, and the analysis result.
    """
    # Window metadata
    window_label: str = Field(..., description="Window identifier (e.g., 'structural', 'phase_foundation')")
    window_type: Literal["structural", "phase", "signal"] = Field(..., description="Window type")
    start_date: str = Field(..., description="Analysis start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Analysis end date (YYYY-MM-DD)")
    duration_years: float = Field(..., description="Window duration in years")
    
    # Policy constraints
    output_mode: Literal["rating", "direction", "signals"] = Field(..., description="Output type allowed for this window")
    allows_rating: bool = Field(..., description="Whether Wide/Narrow/None rating is included")
    requires_disclaimer: bool = Field(..., description="Whether uncertainty disclaimer is required")
    guidance: str = Field(..., description="User-facing guidance for this window")
    
    # Analysis result
    parsed_analysis: ParsedAnalysis = Field(..., description="Structured analysis for this window")
    
    class Config:
        json_schema_extra = {
            "example": {
                "window_label": "phase_acceleration",
                "window_type": "phase",
                "start_date": "2019-01-01",
                "end_date": "2021-12-31",
                "duration_years": 3.0,
                "output_mode": "direction",
                "allows_rating": False,
                "requires_disclaimer": True,
                "guidance": "📊 Medium window (3.0 years): Direction only. Sufficient for moat evolution trends but not full structural rating.",
                "parsed_analysis": {
                    "ticker": "NVDA",
                    "summary": "Moat strengthening during stress test phase...",
                    "raw_response": "..."
                }
            }
        }


class MultiWindowReport(BaseModel):
    """
    Combined report from multiple time windows (e.g., structural + all phases).
    
    Provides a comprehensive view of moat evolution over time.
    """
    ticker: str = Field(..., description="Stock ticker symbol")
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Report generation timestamp")
    
    # Primary window (structural)
    structural: WindowedMoatReport = Field(..., description="Structural moat assessment (10+ years)")
    
    # Phase windows (contextual layers)
    phases: List[WindowedMoatReport] = Field(default_factory=list, description="Phase analysis windows (foundation, acceleration, monetization)")
    
    # Synthesis
    synthesis: Optional[str] = Field(None, description="Cross-window synthesis and key insights")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "NVDA",
                "generated_at": "2026-01-23T12:00:00Z",
                "structural": {
                    "window_label": "structural",
                    "window_type": "structural",
                    "start_date": "2015-01-01",
                    "end_date": "2025-12-31",
                    "duration_years": 11.0,
                    "output_mode": "rating",
                    "allows_rating": True,
                    "requires_disclaimer": False,
                    "guidance": "✓ Structural window (11.0 years): Full rating enabled.",
                    "parsed_analysis": {}
                },
                "phases": [],
                "synthesis": "The moat strengthened across all phases, with acceleration during 2019-2021 being particularly notable..."
            }
        }

