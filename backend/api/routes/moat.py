"""
Overall moat score endpoint for full 2015-2025 analysis.

The moat rating is defined only for the fixed period 2015-01-01 to 2025-12-31.
Query params start_date/end_date are ignored; the response always reflects
and displays this analysis period.

This endpoint now uses REAL data-driven analysis instead of mock scores.
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
import hashlib
import logging

from services.data_driven_moat_scorer import DataDrivenMoatScorer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/moat", tags=["moat"])

# Fixed analysis period for overall moat rating (not user-configurable)
MOAT_START = "2015-01-01"
MOAT_END = "2025-12-31"

# In-memory cache for computed scores (in production, use Redis or similar)
_moat_cache: dict = {}

# Global scorer instance (reused across requests)
_moat_scorer = DataDrivenMoatScorer()


def _cache_key(ticker: str) -> str:
    """Cache key is ticker-only; period is always 2015-2025."""
    return hashlib.md5(f"{ticker}_{MOAT_START}_{MOAT_END}".encode()).hexdigest()


@router.get("/overall")
async def get_overall_moat_score(
    ticker: str = Query(..., description="Stock ticker symbol"),
):
    """
    Get overall moat score for a ticker.

    The rating is always computed for the fixed analysis period 2015-01-01
    to 2025-12-31. The response field time_range always reflects this period.
    Any start_date/end_date query params are ignored.

    Returns:
        OverallMoatScore with comprehensive moat analysis and time_range 2015-2025.
    """
    try:
        key = _cache_key(ticker.upper())

        if key in _moat_cache:
            out = _moat_cache[key]
            out["from_cache"] = True
            return out

        moat_score = _compute_moat_score(ticker.upper())
        _moat_cache[key] = moat_score
        return moat_score

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute moat score: {str(e)}"
        )


def _compute_moat_score(ticker: str) -> dict:
    """
    Compute overall moat score for a ticker over the fixed period 2015-2025.

    Uses real data-driven analysis:
    1. Loads historical price data from yfinance (2015-2025)
    2. Analyzes news coverage from FNSPID dataset
    3. Calculates quantitative metrics for each moat factor
    4. Scores based on financial performance and stability
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dict with overall_score, rating, confidence, factors, trend, summary
    """
    logger.info(f"Computing data-driven moat score for {ticker}")
    
    try:
        # Use the data-driven scorer
        score_data = _moat_scorer.calculate_moat_score(
            ticker=ticker,
            start_date=MOAT_START,
            end_date=MOAT_END
        )
        
        logger.info(
            f"Computed moat score for {ticker}: "
            f"{score_data['overall_score']:.2f} ({score_data['rating']}) "
            f"confidence={score_data['confidence']}"
        )
        
        return score_data
        
    except Exception as e:
        logger.error(f"Error computing moat score for {ticker}: {e}", exc_info=True)
        # Return default score on error
        return {
            "overall_score": 3.0,
            "rating": "Narrow",
            "confidence": "Low",
            "factors": {
                "network_effects": 3.0,
                "switching_costs": 3.0,
                "intangible_assets": 3.0,
                "cost_advantages": 3.0,
                "regulatory_barriers": 3.0,
            },
            "trend": "stable",
            "summary": f"Unable to compute moat score for {ticker} due to data availability issues. Using default neutral values.",
            "time_range": f"{MOAT_START} to {MOAT_END}",
            "computed_at": datetime.utcnow().isoformat(),
            "from_cache": False,
        }
