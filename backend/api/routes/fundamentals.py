"""
Fundamentals API endpoints for ROIC analysis.

Provides endpoints to calculate ROIC, check moat hurdle, and compare to peers.
"""

from fastapi import APIRouter, HTTPException, Query
import logging

from services.roic_calculator import check_roic_hurdle, compare_roic_to_peers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/fundamentals", tags=["fundamentals"])


@router.get("/{ticker}/roic")
async def get_roic_metrics(
    ticker: str,
    years: int = Query(10, description="Number of years to analyze", ge=1, le=20)
):
    """
    Get ROIC (Return on Invested Capital) analysis for a ticker.
    
    ROIC is the definitive quantitative proof of economic moats. A company with
    sustained ROIC > Cost of Capital (WACC) over 10 years demonstrates durable
    competitive advantages.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'NVDA', 'AAPL', 'MSFT')
        years: Number of years to analyze (default: 10, max: 20)
    
    Returns:
        ROIC analysis including:
        - Average, median, min, max ROIC over the period
        - Comparison to estimated WACC (cost of capital)
        - Year-by-year ROIC values
        - Hurdle pass/fail status
        - ROIC trend (strengthening/stable/weakening)
    
    Example:
        GET /api/v1/fundamentals/NVDA/roic?years=10
    """
    try:
        logger.info(f"Calculating ROIC for {ticker} over {years} years")
        
        result = check_roic_hurdle(ticker.upper(), years=years, use_cache=True)
        
        if "error" in result:
            raise HTTPException(
                status_code=404,
                detail=f"Unable to calculate ROIC for {ticker}: {result['error']}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating ROIC for {ticker}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate ROIC: {str(e)}"
        )


@router.get("/{ticker}/compare")
async def compare_fundamentals(
    ticker: str,
    peers: str = Query(..., description="Comma-separated peer ticker symbols (e.g., 'AMD,INTC,AVGO')"),
    years: int = Query(10, description="Number of years to analyze", ge=1, le=20)
):
    """
    Compare a company's ROIC to its peer group average.
    
    This helps contextualize whether a company's ROIC truly represents a competitive
    advantage or is just industry-standard. A wide moat company should have ROIC
    significantly higher than peers.
    
    Args:
        ticker: Primary ticker to analyze (e.g., 'NVDA')
        peers: Comma-separated peer tickers (e.g., 'AMD,INTC,AVGO,MU')
        years: Number of years to analyze (default: 10, max: 20)
    
    Returns:
        Comparison showing:
        - Ticker average ROIC
        - Peer group average ROIC
        - ROIC advantage (ticker - peer average)
        - Individual peer ROIC values
    
    Example:
        GET /api/v1/fundamentals/NVDA/compare?peers=AMD,INTC,AVGO&years=10
    """
    try:
        logger.info(f"Comparing {ticker} ROIC to peers: {peers}")
        
        # Parse peer tickers
        peer_list = [p.strip().upper() for p in peers.split(',') if p.strip()]
        
        if not peer_list:
            raise HTTPException(
                status_code=400,
                detail="Please provide at least one peer ticker (comma-separated)"
            )
        
        if len(peer_list) > 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 peer tickers allowed"
            )
        
        result = compare_roic_to_peers(
            ticker.upper(),
            peer_list,
            years=years,
            use_cache=True
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=404,
                detail=f"Unable to compare ROIC: {result['error']}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing ROIC for {ticker}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare ROIC: {str(e)}"
        )


@router.get("/{ticker}/summary")
async def get_fundamental_summary(ticker: str):
    """
    Get a summary of fundamental metrics including ROIC.
    
    This endpoint provides a quick overview combining ROIC analysis
    with other key fundamental metrics.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Summary of fundamental metrics and moat indicators
    """
    try:
        logger.info(f"Getting fundamental summary for {ticker}")
        
        # Get ROIC data
        roic_result = check_roic_hurdle(ticker.upper(), years=10, use_cache=True)
        
        if "error" in roic_result:
            raise HTTPException(
                status_code=404,
                detail=f"Unable to get fundamentals for {ticker}: {roic_result['error']}"
            )
        
        # Build summary
        summary = {
            "ticker": ticker.upper(),
            "roic_metrics": {
                "average_roic_pct": roic_result.get("avg_roic_pct"),
                "wacc_pct": roic_result.get("wacc_pct"),
                "hurdle_passed": roic_result.get("hurdle_passed"),
                "roic_trend": roic_result.get("roic_trend"),
                "years_analyzed": roic_result.get("years_analyzed"),
            },
            "moat_indicator": "Strong" if roic_result.get("hurdle_passed") else "Weak or None",
            "period": roic_result.get("period"),
            "calculated_at": roic_result.get("calculated_at"),
        }
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting summary for {ticker}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get fundamental summary: {str(e)}"
        )
