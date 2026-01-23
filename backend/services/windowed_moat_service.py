"""
Windowed moat analysis service.

Orchestrates moat analysis over multiple time windows with appropriate policies.
"""

from typing import List, Optional

from agent.moat_tutor import invoke_agent_windowed
from api.models.window import TimeWindow, get_default_windows, get_phase_windows, get_structural_window
from api.models.responses import WindowedMoatReport, MultiWindowReport, ParsedAnalysis
from services.parser import AgentResponseParser
from services.window_classifier import get_window_guidance


def analyze_single_window(
    ticker: str,
    window: TimeWindow,
    conversation_history: list[dict] = None
) -> WindowedMoatReport:
    """
    Perform moat analysis for a single time window.
    
    Args:
        ticker: Stock ticker symbol
        window: TimeWindow with policy constraints
        conversation_history: Optional conversation history
        
    Returns:
        WindowedMoatReport with analysis and window metadata
    """
    # Construct analysis query
    query = f"Analyze the moat characteristics for {ticker}"
    
    # Invoke agent with window policy
    raw_response = invoke_agent_windowed(
        query=query,
        window_start=window.start_date,
        window_end=window.end_date,
        window_duration=window.duration_years,
        output_mode=window.policy.output_mode,
        conversation_history=conversation_history
    )
    
    # Parse the response
    parser = AgentResponseParser()
    parsed = parser.parse(raw_response, ticker, window.start_date, window.end_date)
    
    # Build windowed report
    return WindowedMoatReport(
        window_label=window.label,
        window_type=window.window_type,
        start_date=window.start_date,
        end_date=window.end_date,
        duration_years=window.duration_years,
        output_mode=window.policy.output_mode,
        allows_rating=window.policy.allow_rating,
        requires_disclaimer=window.policy.require_disclaimer,
        guidance=get_window_guidance(window),
        parsed_analysis=parsed
    )


def analyze_structural_and_phases(
    ticker: str,
    include_phases: bool = True,
    conversation_history: list[dict] = None
) -> MultiWindowReport:
    """
    Perform comprehensive multi-window moat analysis.
    
    Analyzes the structural window (2015-2025) and optionally all phase windows
    (Foundation, Acceleration, Monetization).
    
    Args:
        ticker: Stock ticker symbol
        include_phases: Whether to include phase-level analysis
        conversation_history: Optional conversation history
        
    Returns:
        MultiWindowReport with structural and phase analyses
    """
    # Analyze structural window (primary)
    structural_window = get_structural_window()
    structural_report = analyze_single_window(ticker, structural_window, conversation_history)
    
    # Analyze phase windows if requested
    phase_reports = []
    if include_phases:
        for phase_window in get_phase_windows():
            phase_report = analyze_single_window(ticker, phase_window, conversation_history)
            phase_reports.append(phase_report)
    
    # TODO: Add synthesis logic that compares structural vs phase findings
    synthesis = None
    if phase_reports:
        synthesis = _generate_synthesis(ticker, structural_report, phase_reports)
    
    return MultiWindowReport(
        ticker=ticker,
        structural=structural_report,
        phases=phase_reports,
        synthesis=synthesis
    )


def _generate_synthesis(
    ticker: str,
    structural: WindowedMoatReport,
    phases: List[WindowedMoatReport]
) -> str:
    """
    Generate a synthesis comparing structural and phase-level insights.
    
    Args:
        ticker: Stock ticker
        structural: Structural window report
        phases: List of phase window reports
        
    Returns:
        Human-readable synthesis string
    """
    # Extract overall ratings/directions
    structural_rating = "Unknown"
    if structural.parsed_analysis.moat_assessment:
        structural_rating = structural.parsed_analysis.moat_assessment.overall_rating
    
    phase_summaries = []
    for phase in phases:
        label = phase.window_label.replace("phase_", "").title()
        summary = phase.parsed_analysis.summary or "No summary available"
        phase_summaries.append(f"- **{label}**: {summary}")
    
    synthesis = f"""
## Cross-Window Synthesis for {ticker}

**Structural Assessment (2015-2025):** {structural_rating} Moat

**Phase Evolution:**
{chr(10).join(phase_summaries)}

**Key Insight:**
The structural assessment provides the long-term moat rating, while the phase windows reveal how competitive advantages evolved over time. Compare the early foundation phase against the recent monetization phase to understand whether the moat is strengthening, stable, or weakening.
"""
    
    return synthesis.strip()


def get_available_windows() -> dict:
    """
    Get all available default window presets.
    
    Returns:
        Dictionary mapping window labels to TimeWindow objects
    """
    return get_default_windows()
