"""
Company-related Pydantic models.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class Company(BaseModel):
    """
    Company metadata model.
    Aligns with frontend Company type.
    """
    id: str = Field(..., description="Unique company identifier")
    name: str = Field(..., description="Full company name")
    ticker: str = Field(..., description="Stock ticker symbol")
    sector: str = Field(..., description="Industry sector")
    market_cap: str = Field(..., description="Market capitalization (formatted)")
    logo: Optional[str] = Field(None, description="Logo URL or identifier")
    description: Optional[str] = Field(None, description="Company description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "aapl",
                "name": "Apple Inc.",
                "ticker": "AAPL",
                "sector": "Technology",
                "market_cap": "$2.8T",
                "logo": None,
                "description": "Apple Inc. designs, manufactures, and markets smartphones..."
            }
        }


class MoatCharacteristic(BaseModel):
    """A single moat characteristic."""
    name: str = Field(..., description="Moat characteristic name")
    strength: str = Field(..., description="Strength level: 'Strong', 'Moderate', 'Weak', or 'None'")
    description: str = Field(..., description="Description of how this applies to the company")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Network Effects",
                "strength": "Strong",
                "description": "Apple's ecosystem creates powerful network effects through device integration"
            }
        }


class CompanyMoat(BaseModel):
    """
    Detailed moat analysis for a company.
    """
    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: str = Field(..., description="Full company name")
    overall_moat_rating: str = Field(
        ...,
        description="Overall moat strength: 'Wide', 'Narrow', or 'None'"
    )
    characteristics: List[MoatCharacteristic] = Field(
        ...,
        description="List of moat characteristics with analysis"
    )
    summary: str = Field(..., description="Summary of competitive advantages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "overall_moat_rating": "Wide",
                "characteristics": [
                    {
                        "name": "Network Effects",
                        "strength": "Strong",
                        "description": "Ecosystem lock-in through device integration"
                    },
                    {
                        "name": "Intangible Assets",
                        "strength": "Strong",
                        "description": "Powerful brand and proprietary technology"
                    },
                    {
                        "name": "Switching Costs",
                        "strength": "Strong",
                        "description": "High cost of leaving the Apple ecosystem"
                    }
                ],
                "summary": "Apple has a wide moat driven by strong network effects..."
            }
        }


class CompaniesListResponse(BaseModel):
    """Response model for listing companies."""
    companies: List[Company] = Field(..., description="List of available companies")
    total: int = Field(..., description="Total number of companies")
    
    class Config:
        json_schema_extra = {
            "example": {
                "companies": [
                    {
                        "id": "aapl",
                        "name": "Apple Inc.",
                        "ticker": "AAPL",
                        "sector": "Technology",
                        "market_cap": "$2.8T"
                    }
                ],
                "total": 1
            }
        }

