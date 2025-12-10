"""
Request models for API endpoints.
"""

from typing import Optional
from datetime import date

from pydantic import BaseModel, Field, field_validator


class AnalyzeRequest(BaseModel):
    """
    Request model for structured stock analysis.
    
    This endpoint provides a more structured alternative to the free-form chat.
    """
    ticker: str = Field(
        ...,
        description="Stock ticker symbol (e.g., 'AAPL', 'MSFT')",
        min_length=1,
        max_length=10
    )
    start_date: str = Field(
        ...,
        description="Start date in YYYY-MM-DD format",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    end_date: str = Field(
        ...,
        description="End date in YYYY-MM-DD format",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID for conversation continuity"
    )
    expertise_level: Optional[str] = Field(
        None,
        description="User's expertise level: 'beginner', 'intermediate', or 'professional'",
        pattern=r"^(beginner|intermediate|professional)$"
    )
    
    @field_validator('ticker')
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        """Convert ticker to uppercase."""
        return v.upper().strip()
    
    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date format."""
        try:
            # This will raise ValueError if format is wrong
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid date format: {v}. Use YYYY-MM-DD")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "start_date": "2023-01-01",
                "end_date": "2023-02-28",
                "session_id": "session-123",
                "expertise_level": "beginner"
            }
        }

