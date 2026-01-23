"""
Windowed moat analysis endpoints.

Provides time-window-aware moat analysis with policy enforcement.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from api.models.window import TimeWindow, get_default_windows
from api.models.responses import WindowedMoatReport, MultiWindowReport, ErrorResponse
from services.windowed_moat_service import (
    analyze_single_window,
    analyze_structural_and_phases,
    get_available_windows
)
from services.window_classifier import create_custom_window

router = APIRouter(prefix="/api/v1/moat", tags=["Windowed Moat Analysis"])


@router.get("/windows", response_model=dict)
async def list_available_windows():
    """
    List all available default window presets.
    
    Returns window configurations with their policies and guidance.
    """
    windows = get_available_windows()
    
    # Convert to serializable dict
    result = {}
    for label, window in windows.items():
        result[label] = {
            "label": window.label,
            "window_type": window.window_type,
            "start_date": window.start_date,
            "end_date": window.end_date,
            "duration_years": window.duration_years,
            "description": window.description,
            "policy": {
                "output_mode": window.policy.output_mode,
                "allow_rating": window.policy.allow_rating,
                "allow_scores": window.policy.allow_scores,
                "require_disclaimer": window.policy.require_disclaimer
            }
        }
    
    return result


@router.post("/analyze/window", response_model=WindowedMoatReport)
async def analyze_with_window(
    ticker: str = Query(..., description="Stock ticker symbol"),
    window_label: str = Query(..., description="Window preset label (e.g., 'structural', 'phase_foundation')")
):
    """
    Analyze a company's moat using a specific time window preset.
    
    Available windows:
    - `structural`: 2015-2025 (full rating)
    - `phase_foundation`: 2015-2018 (early moat formation)
    - `phase_acceleration`: 2019-2021 (stress test)
    - `phase_monetization`: 2022-2025 (pricing power)
    """
    try:
        # Get the window preset
        windows = get_available_windows()
        if window_label not in windows:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown window label '{window_label}'. Available: {list(windows.keys())}"
            )
        
        window = windows[window_label]
        
        # Perform analysis
        report = analyze_single_window(ticker.upper(), window)
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/custom", response_model=WindowedMoatReport)
async def analyze_with_custom_window(
    ticker: str = Query(..., description="Stock ticker symbol"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    description: Optional[str] = Query(None, description="Optional window description")
):
    """
    Analyze a company's moat using a custom time window.
    
    The system will automatically determine the appropriate analysis policy
    based on the window duration:
    - ≥8 years: Full rating
    - 3-7 years: Direction only
    - <3 years: Signals only
    """
    try:
        # Create custom window with policy
        window = create_custom_window(start_date, end_date, description)
        
        # Perform analysis
        report = analyze_single_window(ticker.upper(), window)
        
        return report
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/comprehensive", response_model=MultiWindowReport)
async def analyze_comprehensive(
    ticker: str = Query(..., description="Stock ticker symbol"),
    include_phases: bool = Query(True, description="Include phase-level analysis (Foundation, Acceleration, Monetization)")
):
    """
    Comprehensive multi-window moat analysis.
    
    Analyzes:
    1. Structural window (2015-2025): Primary long-term rating
    2. Phase windows (optional): Foundation, Acceleration, Monetization
    
    Provides synthesis comparing insights across windows.
    """
    try:
        report = analyze_structural_and_phases(
            ticker.upper(),
            include_phases=include_phases
        )
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
