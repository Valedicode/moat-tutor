"""
Overall moat score endpoint for full 2015-2025 analysis.
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Optional
import hashlib
import json

router = APIRouter(prefix="/api/v1/moat", tags=["moat"])

# In-memory cache for computed scores (in production, use Redis or similar)
_moat_cache: dict = {}


def generate_cache_key(ticker: str, start_date: str, end_date: str) -> str:
    """Generate a cache key for moat score lookup."""
    key_str = f"{ticker}_{start_date}_{end_date}"
    return hashlib.md5(key_str.encode()).hexdigest()


@router.get("/overall")
async def get_overall_moat_score(
    ticker: str = Query(..., description="Stock ticker symbol"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """
    Get overall moat score for a ticker across specified date range.
    
    If dates match 2015-01-01 to 2025-12-31, returns cached full analysis.
    Otherwise, computes analysis on-demand.
    
    Returns:
        OverallMoatScore with comprehensive moat analysis
    """
    try:
        # Default to full range if not specified
        start = start_date or "2015-01-01"
        end = end_date or "2025-12-31"
        
        # Check if this is the full range (can use cached data)
        is_full_range = start == "2015-01-01" and end == "2025-12-31"
        
        # Generate cache key
        cache_key = generate_cache_key(ticker.upper(), start, end)
        
        # Check cache first
        if cache_key in _moat_cache:
            cached_result = _moat_cache[cache_key]
            # Add metadata about cache hit
            cached_result["from_cache"] = True
            return cached_result
        
        # Mock computation (in production, this would call actual analysis)
        # For now, return mock data based on ticker
        moat_score = _compute_moat_score(ticker.upper(), start, end, is_full_range)
        
        # Cache the result
        _moat_cache[cache_key] = moat_score
        
        return moat_score
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute moat score: {str(e)}"
        )


def _compute_moat_score(ticker: str, start_date: str, end_date: str, is_full_range: bool) -> dict:
    """
    Compute overall moat score for a ticker.
    
    This is a mock implementation. In production, this would:
    1. Analyze historical data
    2. Process news events
    3. Evaluate competitive dynamics
    4. Score each moat factor
    """
    
    # Mock scores based on ticker (replace with real analysis)
    mock_scores = {
        "NVDA": {
            "overall_score": 4.5,
            "rating": "Wide",
            "confidence": "High",
            "factors": {
                "network_effects": 4.2,
                "switching_costs": 4.5,
                "intangible_assets": 4.8,
                "cost_advantages": 4.3,
                "regulatory_barriers": 4.6,
            },
            "trend": "strengthening",
            "summary": "NVIDIA demonstrates a wide moat driven by strong intangible assets (CUDA ecosystem, brand), high switching costs (software lock-in), and significant network effects. The company's position in AI accelerators has strengthened substantially from 2015-2025."
        },
        "AAPL": {
            "overall_score": 4.8,
            "rating": "Wide",
            "confidence": "High",
            "factors": {
                "network_effects": 4.9,
                "switching_costs": 4.8,
                "intangible_assets": 4.9,
                "cost_advantages": 4.5,
                "regulatory_barriers": 4.3,
            },
            "trend": "stable",
            "summary": "Apple exhibits an exceptionally wide moat characterized by powerful network effects (ecosystem), extremely high switching costs, and strong brand intangibles. The ecosystem moat has remained consistently strong throughout 2015-2025."
        },
        "MSFT": {
            "overall_score": 4.6,
            "rating": "Wide",
            "confidence": "High",
            "factors": {
                "network_effects": 4.7,
                "switching_costs": 4.8,
                "intangible_assets": 4.5,
                "cost_advantages": 4.4,
                "regulatory_barriers": 4.4,
            },
            "trend": "strengthening",
            "summary": "Microsoft's moat has strengthened significantly through its cloud transition. Extremely high switching costs in enterprise software, growing network effects in Teams/Azure, and strong recurring revenue models create a formidable competitive advantage."
        },
        "AMD": {
            "overall_score": 3.4,
            "rating": "Narrow",
            "confidence": "Medium",
            "factors": {
                "network_effects": 3.2,
                "switching_costs": 3.0,
                "intangible_assets": 4.0,
                "cost_advantages": 3.4,
                "regulatory_barriers": 2.9,
            },
            "trend": "strengthening",
            "summary": "AMD has a narrow but improving moat. Strong technical capabilities and IP provide intangible asset advantages, but faces intense competition from Intel and NVIDIA. Switching costs are moderate as customers can migrate between x86 architectures."
        },
        "GOOGL": {
            "overall_score": 4.9,
            "rating": "Wide",
            "confidence": "High",
            "factors": {
                "network_effects": 4.9,
                "switching_costs": 4.6,
                "intangible_assets": 4.8,
                "cost_advantages": 4.8,
                "regulatory_barriers": 4.1,
            },
            "trend": "stable",
            "summary": "Google possesses one of the widest moats in technology, driven by unparalleled network effects in search/advertising, massive scale advantages, and dominant brand equity. Despite regulatory challenges, the core search moat remains intact."
        },
    }
    
    # Get ticker-specific scores or use defaults
    score_data = mock_scores.get(ticker, {
        "overall_score": 3.0,
        "rating": "Narrow",
        "confidence": "Medium",
        "factors": {
            "network_effects": 3.0,
            "switching_costs": 3.0,
            "intangible_assets": 3.0,
            "cost_advantages": 3.0,
            "regulatory_barriers": 3.0,
        },
        "trend": "stable",
        "summary": f"{ticker} exhibits moderate competitive advantages with room for strengthening across multiple moat factors."
    })
    
    return {
        **score_data,
        "time_range": f"{start_date} to {end_date}",
        "computed_at": datetime.utcnow().isoformat(),
        "from_cache": False,
    }
