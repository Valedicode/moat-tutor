"""
Fundamentals API endpoints for ROIC analysis.

Provides endpoints to calculate ROIC, check moat hurdle, and compare to peers.
"""

from fastapi import APIRouter, HTTPException, Query
import logging

from services.roic_calculator import check_roic_hurdle, compare_roic_to_peers, compare_moat_profiles
from services.valuation_estimator import estimate_fair_value, calculate_uncertainty_rating
from services.resilience_analyzer import analyze_crisis_resilience, compare_resilience
from services.moat_news_classifier import classify_passages_by_moat_source, detect_moat_milestones

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
            "excess_profit": {
                "avg_roic_wacc_spread_pct": roic_result.get("avg_roic_wacc_spread_pct"),
                "avg_economic_profit": roic_result.get("avg_economic_profit"),
                "cumulative_economic_profit": roic_result.get("cumulative_economic_profit"),
            },
            "fade_period": roic_result.get("fade_period"),
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


@router.get("/{ticker}/valuation")
async def get_valuation(ticker: str):
    """
    Get fair value estimation using simplified DCF model.
    
    Estimates intrinsic value based on projected Free Cash Flows, discounted
    at WACC, and compares to current market price. Includes star rating (1-5)
    and uncertainty-adjusted fair value.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Fair value per share, P/FV ratio, star rating, DCF breakdown
    
    Example:
        GET /api/v1/fundamentals/AAPL/valuation
    """
    try:
        logger.info(f"Estimating fair value for {ticker}")
        
        result = estimate_fair_value(ticker.upper(), use_cache=True)
        
        if "error" in result:
            raise HTTPException(
                status_code=404,
                detail=f"Unable to estimate fair value for {ticker}: {result['error']}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error estimating fair value for {ticker}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to estimate fair value: {str(e)}"
        )


@router.get("/{ticker}/uncertainty")
async def get_uncertainty(ticker: str):
    """
    Get uncertainty rating based on financial volatility metrics.
    
    Assesses revenue volatility, ROIC volatility, financial leverage,
    and operating leverage to determine predictability of future cash flows.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Uncertainty rating (Low to Extreme), component scores,
        recommended margin of safety
    
    Example:
        GET /api/v1/fundamentals/AAPL/uncertainty
    """
    try:
        logger.info(f"Calculating uncertainty for {ticker}")
        
        result = calculate_uncertainty_rating(ticker.upper(), use_cache=True)
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating uncertainty for {ticker}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate uncertainty: {str(e)}"
        )


@router.get("/{ticker}/moat-comparison")
async def get_moat_comparison(
    ticker: str,
    peers: str = Query(..., description="Comma-separated peer ticker symbols"),
    years: int = Query(10, description="Number of years to analyze", ge=1, le=20)
):
    """
    Multi-dimensional moat comparison across standardized metrics.
    
    Compares ROIC spread, operating margin, revenue growth, economic profit,
    and fade period across companies using a globally standardized methodology.
    
    Args:
        ticker: Primary ticker to analyze
        peers: Comma-separated peer tickers
        years: Number of years to analyze
    
    Returns:
        Multi-dimensional comparison table with advantages
    
    Example:
        GET /api/v1/fundamentals/NVDA/moat-comparison?peers=AMD,INTC,AVGO&years=10
    """
    try:
        logger.info(f"Comparing moat profiles: {ticker} vs {peers}")
        
        peer_list = [p.strip().upper() for p in peers.split(',') if p.strip()]
        
        if not peer_list:
            raise HTTPException(
                status_code=400,
                detail="Please provide at least one peer ticker."
            )
        
        if len(peer_list) > 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 peer tickers allowed."
            )
        
        result = compare_moat_profiles(
            ticker.upper(),
            peer_list,
            years=years,
            use_cache=True
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=404,
                detail=f"Unable to compare moat profiles: {result['error']}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing moat profiles: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare moat profiles: {str(e)}"
        )


@router.get("/{ticker}/resilience")
async def get_resilience(
    ticker: str,
    crisis: str = Query("", description="Optional crisis ID: dot_com_bust, financial_crisis, covid_crash, rate_hike_2022")
):
    """
    Analyze crisis resilience for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        crisis: Optional single crisis to analyze
    
    Returns:
        Crisis drawdown/recovery analysis and long-term metrics
    """
    try:
        cid = crisis if crisis else None
        result = analyze_crisis_resilience(ticker.upper(), crisis_id=cid)
        return result
    except Exception as e:
        logger.error(f"Error analyzing resilience for {ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/resilience-comparison")
async def get_resilience_comparison(
    ticker: str,
    peers: str = Query(..., description="Comma-separated peer tickers"),
    crisis: str = Query("", description="Optional crisis ID")
):
    """
    Compare crisis resilience across peers.
    
    Args:
        ticker: Primary ticker
        peers: Comma-separated peer tickers
        crisis: Optional single crisis to focus on
    """
    try:
        peer_list = [p.strip().upper() for p in peers.split(",") if p.strip()]
        if not peer_list:
            raise HTTPException(status_code=400, detail="Provide at least one peer.")
        cid = crisis if crisis else None
        result = compare_resilience(ticker.upper(), peer_list, crisis_id=cid)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing resilience: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/moat-news")
async def get_moat_news(
    ticker: str,
    start_date: str = Query("", description="Optional start date YYYY-MM-DD"),
    end_date: str = Query("", description="Optional end date YYYY-MM-DD"),
):
    """
    Classify historical news by moat source.
    
    Args:
        ticker: Stock ticker symbol
        start_date: Optional start date
        end_date: Optional end date
    """
    try:
        sd = start_date if start_date else None
        ed = end_date if end_date else None
        result = classify_passages_by_moat_source(ticker.upper(), start_date=sd, end_date=ed)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error classifying moat news for {ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/milestones")
async def get_milestones(ticker: str):
    """
    Detect moat milestones for a ticker.
    
    Combines price-anchored events, moat-themed news scans, and ROIC context
    to identify the most significant moat events in a company's history.
    """
    try:
        result = detect_moat_milestones(ticker.upper(), top_n=15)
        if "error" in result and not result.get("milestones"):
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting milestones for {ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
