"""
Overall moat score endpoint for comprehensive 2000-2025 analysis.

The moat rating uses the LLM agent's comprehensive analysis combining:
- ROIC and financial metrics (2006-2025 when available)
- News analysis (2000-2023 FNSPID, 2024+ yfinance)
- Price resilience and milestones
- Qualitative moat reasoning

This provides the highest quality moat assessment by integrating quantitative
and qualitative factors.
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
import hashlib
import logging

from agent.moat_tutor import invoke_agent_windowed
from services.parser import AgentResponseParser
from services.financial_health import assess_financial_health

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/moat", tags=["moat"])

# Fixed analysis period for overall moat rating (not user-configurable)
MOAT_START = "2000-01-01"
MOAT_END = "2025-12-31"

# In-memory cache for computed scores (in production, use Redis or similar)
_moat_cache: dict = {}


def _cache_key(ticker: str) -> str:
    """Cache key is ticker-only; period is always 2000-2025."""
    return hashlib.md5(f"{ticker}_{MOAT_START}_{MOAT_END}".encode()).hexdigest()


@router.get("/overall")
async def get_overall_moat_score(
    ticker: str = Query(..., description="Stock ticker symbol"),
):
    """
    Get overall moat score for a ticker using comprehensive LLM agent analysis.

    The rating is computed for the fixed analysis period 2000-01-01 to 2025-12-31.
    Uses the LLM agent which combines:
    - ROIC and financial metrics (2006-2025 when available)
    - News analysis (2000-2023 FNSPID, 2024+ yfinance)
    - Price resilience and milestones
    - Qualitative moat reasoning

    Returns:
        OverallMoatScore with comprehensive moat analysis and time_range 2000-2025.
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
        logger.error(f"Error getting overall moat score for {ticker}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute moat score: {str(e)}"
        )


def _compute_moat_score(ticker: str) -> dict:
    """
    Compute overall moat score using comprehensive LLM agent analysis.
    
    Uses the LLM agent which combines:
    1. ROIC and financial metrics (2006-2025 when available)
    2. News analysis (2000-2023 FNSPID, 2024+ yfinance)
    3. Price resilience and milestones
    4. Qualitative moat reasoning
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dict with overall_score, rating, confidence, factors, trend, summary
    """
    logger.info(f"Computing comprehensive moat score for {ticker} using LLM agent")
    
    try:
        # Calculate duration for window policy
        from datetime import datetime
        start_dt = datetime.strptime(MOAT_START, "%Y-%m-%d")
        end_dt = datetime.strptime(MOAT_END, "%Y-%m-%d")
        duration_years = (end_dt - start_dt).days / 365.25
        
        # Invoke agent with full analysis query - explicitly request structured assessment
        query = f"Analyze {ticker}'s economic moat comprehensively from {MOAT_START} to {MOAT_END}. Provide a full moat analysis with all sections including the structured moat assessment JSON block."
        
        raw_response = invoke_agent_windowed(
            query=query,
            window_start=MOAT_START,
            window_end=MOAT_END,
            window_duration=duration_years,
            output_mode="rating",  # Full structural rating for 20+ year window
            conversation_history=None
        )
        
        # Parse the agent response
        parser = AgentResponseParser()
        parsed = parser.parse(raw_response, ticker, MOAT_START, MOAT_END)
        
        # Extract moat assessment
        if not parsed.moat_assessment:
            logger.warning(f"No moat assessment found in agent response for {ticker}")
            raise ValueError("Agent response did not include structured moat assessment")
        
        assessment = parsed.moat_assessment
        
        # Convert to OverallMoatScore format
        score_data = {
            "overall_score": assessment.overall_score,
            "rating": assessment.overall_rating,
            "confidence": assessment.overall_confidence,
            "factors": {
                "network_effects": assessment.network_effects.score,
                "switching_costs": assessment.switching_costs.score,
                "intangible_assets": assessment.intangible_assets.score,
                "cost_advantages": assessment.cost_advantages.score,
                "efficient_scale": assessment.efficient_scale.score,
            },
            "trend": assessment.network_effects.direction.lower() if assessment.network_effects.direction else "stable",
            "summary": parsed.summary or f"Comprehensive moat analysis for {ticker} covering {MOAT_START} to {MOAT_END}.",
            "time_range": f"{MOAT_START} to {MOAT_END}",
            "computed_at": datetime.utcnow().isoformat(),
            "from_cache": False,
        }
        
        # Determine trend from dimension directions
        directions = [
            assessment.network_effects.direction,
            assessment.switching_costs.direction,
            assessment.intangible_assets.direction,
            assessment.cost_advantages.direction,
            assessment.efficient_scale.direction,
        ]
        strengthening_count = sum(1 for d in directions if d == "Strengthening")
        weakening_count = sum(1 for d in directions if d == "Weakening")
        
        if strengthening_count > weakening_count:
            score_data["trend"] = "strengthening"
        elif weakening_count > strengthening_count:
            score_data["trend"] = "weakening"
        else:
            score_data["trend"] = "stable"
        
        # Financial health override: if severe distress, force No Moat
        try:
            fh = assess_financial_health(ticker)
            score_data["financial_health_status"] = fh.get("financial_health_status", "Watch")
            if fh.get("moat_override_flag"):
                score_data["rating"] = "None"
                score_data["overall_score"] = min(score_data["overall_score"], 2.0)
                score_data["summary"] += (
                    f" [OVERRIDE] Financial health is Critical "
                    f"(value destruction risk {fh['value_destruction_risk']:.0%}), "
                    f"forcing No-Moat rating regardless of competitive advantages."
                )
                logger.warning(f"Financial health override applied for {ticker}: forced No Moat")
        except Exception as fh_err:
            logger.warning(f"Financial health check failed for {ticker}: {fh_err}")

        logger.info(
            f"Computed comprehensive moat score for {ticker}: "
            f"{score_data['overall_score']:.2f} ({score_data['rating']}) "
            f"confidence={score_data['confidence']}, trend={score_data['trend']}"
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
                "efficient_scale": 3.0,
            },
            "trend": "stable",
            "summary": f"Unable to compute moat score for {ticker} due to error: {str(e)}",
            "time_range": f"{MOAT_START} to {MOAT_END}",
            "computed_at": datetime.utcnow().isoformat(),
            "from_cache": False,
        }
