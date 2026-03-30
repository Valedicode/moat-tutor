"""
Company-related Pydantic models.
"""

from typing import Optional

from pydantic import BaseModel, Field


class Company(BaseModel):
    """Company metadata model."""
    id: str = Field(..., description="Unique company identifier")
    name: str = Field(..., description="Full company name")
    ticker: str = Field(..., description="Stock ticker symbol")
    sector: str = Field(..., description="Industry sector")
    market_cap: str = Field(..., description="Market capitalization (formatted)")
    logo: Optional[str] = Field(None, description="Logo URL or identifier")
    description: Optional[str] = Field(None, description="Company description")
