"""
Time window models for windowed moat analysis.

Defines different types of analysis windows and their associated policies.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


WindowType = Literal["structural", "phase", "signal"]
WindowLabel = Literal[
    "structural",  # 2000-2025 (20+ years)
    "phase_foundation",  # 2000-2010
    "phase_acceleration",  # 2011-2015
    "phase_monetization",  # 2016-2025
    "medium_term",  # 3-7 years
    "short_term",  # <3 years
    "custom"
]


class WindowPolicy(BaseModel):
    """
    Policy defining what outputs are allowed for a given time window.
    
    Shorter windows can only provide directional signals, not structural ratings.
    """
    allow_rating: bool = Field(..., description="Whether Wide/Narrow/None rating is allowed")
    allow_scores: bool = Field(..., description="Whether numeric dimension scores are allowed")
    require_disclaimer: bool = Field(..., description="Whether uncertainty disclaimer is required")
    output_mode: Literal["rating", "direction", "signals"] = Field(
        ..., 
        description="Expected output type: rating (full), direction (partial), or signals (tactical only)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "allow_rating": True,
                "allow_scores": True,
                "require_disclaimer": False,
                "output_mode": "rating"
            }
        }


class TimeWindow(BaseModel):
    """
    Represents a time window for moat analysis with associated metadata.
    """
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    label: WindowLabel = Field(..., description="Window label/identifier")
    window_type: WindowType = Field(..., description="Type of window: structural, phase, or signal")
    duration_years: float = Field(..., description="Window duration in years")
    policy: WindowPolicy = Field(..., description="Analysis policy for this window")
    description: Optional[str] = Field(None, description="Human-readable description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2000-01-01",
                "end_date": "2025-12-31",
                "label": "structural",
                "window_type": "structural",
                "duration_years": 26.0,
                "policy": {
                    "allow_rating": True,
                    "allow_scores": True,
                    "require_disclaimer": False,
                    "output_mode": "rating"
                },
                "description": "Structural moat assessment (2000-2025)"
            }
        }


# Default window presets
STRUCTURAL_WINDOW = TimeWindow(
    start_date="2000-01-01",
    end_date="2025-12-31",
    label="structural",
    window_type="structural",
    duration_years=26.0,
    policy=WindowPolicy(
        allow_rating=True,
        allow_scores=True,
        require_disclaimer=False,
        output_mode="rating"
    ),
    description="Structural moat assessment over 20+ years (captures multiple cycles)"
)

PHASE_FOUNDATION = TimeWindow(
    start_date="2000-01-01",
    end_date="2010-12-31",
    label="phase_foundation",
    window_type="phase",
    duration_years=11.0,
    policy=WindowPolicy(
        allow_rating=True,
        allow_scores=True,
        require_disclaimer=False,
        output_mode="rating"
    ),
    description="Foundation Phase (2000-2010): Early moat formation and differentiation"
)

PHASE_ACCELERATION = TimeWindow(
    start_date="2011-01-01",
    end_date="2015-12-31",
    label="phase_acceleration",
    window_type="phase",
    duration_years=5.0,
    policy=WindowPolicy(
        allow_rating=True,
        allow_scores=True,
        require_disclaimer=False,
        output_mode="rating"
    ),
    description="Acceleration & Growth (2011-2015): Competitive response and platform scaling"
)

PHASE_MONETIZATION = TimeWindow(
    start_date="2016-01-01",
    end_date="2025-12-31",
    label="phase_monetization",
    window_type="phase",
    duration_years=10.0,
    policy=WindowPolicy(
        allow_rating=True,
        allow_scores=True,
        require_disclaimer=False,
        output_mode="rating"
    ),
    description="Monetization & Power (2016-2025): Pricing power and ecosystem monetization"
)

DEFAULT_WINDOWS = {
    "structural": STRUCTURAL_WINDOW,
    "phase_foundation": PHASE_FOUNDATION,
    "phase_acceleration": PHASE_ACCELERATION,
    "phase_monetization": PHASE_MONETIZATION,
}


def get_default_windows() -> dict[str, TimeWindow]:
    """Get all default window presets."""
    return DEFAULT_WINDOWS.copy()


def get_structural_window() -> TimeWindow:
    """Get the default structural window (2000-2025)."""
    return STRUCTURAL_WINDOW


def get_phase_windows() -> list[TimeWindow]:
    """Get all phase windows in chronological order."""
    return [PHASE_FOUNDATION, PHASE_ACCELERATION, PHASE_MONETIZATION]
