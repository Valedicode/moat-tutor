"""
Chart data endpoints for stock price visualization.

These endpoints provide optimized chart data with adaptive interval selection
based on the date range, ensuring optimal performance and readability.
"""

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query

from api.models.responses import ChartDataResponse, ErrorResponse
from services.stock_data import get_stock_data_service

router = APIRouter(prefix="/api/v1/charts", tags=["charts"])


@router.get("/{ticker}", response_model=ChartDataResponse)
async def get_chart_data(
    ticker: str,
    start_date: Optional[str] = Query(
        None,
        description="Start date in YYYY-MM-DD format",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    ),
    end_date: Optional[str] = Query(
        None,
        description="End date in YYYY-MM-DD format",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    ),
    interval: Literal["auto", "D", "W", "ME", "M"] = Query(
        "auto",
        description="Time interval: 'auto' (adaptive), 'D' (daily), 'W' (weekly), 'ME' (monthly)"
    )
) -> ChartDataResponse:
    """
    Get chart-ready OHLCV data for a stock ticker.
    
    This endpoint provides optimized chart data with automatic interval selection:
    - **Daily (D)**: For periods < 3 months (~60-75 data points)
    - **Weekly (W)**: For periods 3 months to 2 years (~52 points/year)
    - **Monthly (ME)**: For periods > 2 years (~12 points/year)
    
    The data is resampled using proper OHLC aggregation:
    - Open: First value in the period
    - High: Maximum value in the period
    - Low: Minimum value in the period
    - Close: Last value in the period
    - Volume: Sum of volumes in the period
    
    ## Example Requests
    
    Get 3 months of Apple data (will return daily):
    ```
    GET /api/v1/charts/AAPL?start_date=2023-01-01&end_date=2023-03-31
    ```
    
    Get 1 year of NVIDIA data (will return weekly):
    ```
    GET /api/v1/charts/NVDA?start_date=2023-01-01&end_date=2023-12-31
    ```
    
    Get all available data for Microsoft with monthly intervals:
    ```
    GET /api/v1/charts/MSFT?interval=ME
    ```
    
    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT, GOOGL, NVDA)
        start_date: Optional start date in YYYY-MM-DD format
        end_date: Optional end date in YYYY-MM-DD format
        interval: Time interval (auto, D, W, ME, or M for backward compatibility)
        
    Returns:
        ChartDataResponse with OHLCV data ready for plotting
        
    Raises:
        HTTPException: 404 if ticker not found, 400 for invalid parameters
    """
    try:
        service = get_stock_data_service()
        
        # Get chart data from service
        result = service.get_chart_data(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )
        
        # Check for errors in result
        if "error" in result:
            raise HTTPException(
                status_code=404 if "not available" in result["error"].lower() else 400,
                detail=result["error"]
            )
        
        return ChartDataResponse(**result)
        
    except FileNotFoundError:
        # Ticker not available
        service = get_stock_data_service()
        available = service.available_tickers()
        raise HTTPException(
            status_code=404,
            detail=f"Ticker '{ticker}' not found. Available tickers: {', '.join(available)}"
        )
    except ValueError as e:
        # Invalid parameters
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        # Unexpected error
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{ticker}/intervals", response_model=dict)
async def get_available_intervals(ticker: str) -> dict:
    """
    Get recommended intervals for different date ranges.
    
    This is a helper endpoint that shows what interval would be used
    for different common date ranges.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with interval recommendations
    """
    try:
        service = get_stock_data_service()
        
        # Verify ticker exists
        _ = service.load_ticker_data(ticker)
        
        return {
            "ticker": ticker.upper(),
            "recommendations": {
                "1_month": "D (Daily) - ~20-22 trading days",
                "3_months": "D (Daily) - ~60-75 trading days",
                "6_months": "W (Weekly) - ~26 weeks",
                "1_year": "W (Weekly) - ~52 weeks",
                "2_years": "W (Weekly) - ~104 weeks",
                "5_years": "ME (Monthly) - ~60 months",
                "10_years": "ME (Monthly) - ~120 months"
            },
            "available_intervals": ["D", "W", "ME"],
            "default": "auto (adaptive based on date range)"
        }
        
    except FileNotFoundError:
        service = get_stock_data_service()
        available = service.available_tickers()
        raise HTTPException(
            status_code=404,
            detail=f"Ticker '{ticker}' not found. Available tickers: {', '.join(available)}"
        )

