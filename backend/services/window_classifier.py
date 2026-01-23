"""
Window classification and policy determination.

Determines the appropriate analysis policy based on the time window duration.
"""

from datetime import datetime
from typing import Tuple, Optional

from api.models.window import TimeWindow, WindowPolicy


def calculate_duration_years(start_date: str, end_date: str) -> float:
    """
    Calculate the duration between two dates in years.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        Duration in years (fractional)
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        delta = end - start
        return delta.days / 365.25
    except ValueError:
        return 0.0


def classify_window(start_date: str, end_date: str) -> Tuple[WindowPolicy, str]:
    """
    Classify a time window and determine the appropriate analysis policy.
    
    Rules:
    - < 3 years: Signals only (no rating, high uncertainty)
    - 3-7 years: Direction only (partial confidence, no rating)
    - ≥ 8 years: Full rating allowed (structural moat assessment)
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        Tuple of (WindowPolicy, window_category)
    """
    duration = calculate_duration_years(start_date, end_date)
    
    # Signal-only window (< 3 years)
    if duration < 3.0:
        return (
            WindowPolicy(
                allow_rating=False,
                allow_scores=False,
                require_disclaimer=True,
                output_mode="signals"
            ),
            "short_term_signals"
        )
    
    # Direction-only window (3-7 years)
    elif duration < 8.0:
        return (
            WindowPolicy(
                allow_rating=False,
                allow_scores=True,
                require_disclaimer=True,
                output_mode="direction"
            ),
            "medium_term_direction"
        )
    
    # Full rating window (≥ 8 years)
    else:
        return (
            WindowPolicy(
                allow_rating=True,
                allow_scores=True,
                require_disclaimer=False,
                output_mode="rating"
            ),
            "structural_rating"
        )


def create_custom_window(
    start_date: str,
    end_date: str,
    description: Optional[str] = None
) -> TimeWindow:
    """
    Create a custom time window with automatically determined policy.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        description: Optional human-readable description
        
    Returns:
        TimeWindow with appropriate policy
    """
    duration = calculate_duration_years(start_date, end_date)
    policy, category = classify_window(start_date, end_date)
    
    # Determine window type
    if duration >= 8.0:
        window_type = "structural"
    elif duration >= 3.0:
        window_type = "phase"
    else:
        window_type = "signal"
    
    if description is None:
        description = f"Custom {category.replace('_', ' ')} ({start_date} to {end_date})"
    
    return TimeWindow(
        start_date=start_date,
        end_date=end_date,
        label="custom",
        window_type=window_type,
        duration_years=round(duration, 1),
        policy=policy,
        description=description
    )


def get_window_guidance(window: TimeWindow) -> str:
    """
    Get user-facing guidance text for a window based on its policy.
    
    Args:
        window: TimeWindow to get guidance for
        
    Returns:
        Human-readable guidance string
    """
    duration = window.duration_years
    
    if duration < 3.0:
        return (
            f"⚠️ Short window ({duration:.1f} years): Signals only. "
            "Too short for structural moat assessment. "
            "Focus: market expectations, tactical events, sentiment shifts."
        )
    elif duration < 8.0:
        return (
            f"📊 Medium window ({duration:.1f} years): Direction only. "
            "Sufficient for moat evolution trends but not full structural rating. "
            "Focus: strengthening/weakening mechanisms, competitive dynamics."
        )
    else:
        return (
            f"✓ Structural window ({duration:.1f} years): Full rating enabled. "
            "Sufficient duration to assess durable competitive advantages. "
            "Focus: Wide/Narrow/None rating with high confidence."
        )
