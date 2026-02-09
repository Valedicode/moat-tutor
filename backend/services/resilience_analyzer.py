"""
Price Resilience Analyzer

Analyzes how companies perform during market crises and connects
resilience to economic moat strength via ROIC data.

Features:
- Crisis-specific drawdown and recovery analysis
- Peer comparison during downturns
- ROIC-resilience correlation (moat = price protection)
- 20-year CAGR and risk-adjusted return metrics
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from services.stock_data import StockDataService, get_stock_data_service
from services.roic_calculator import check_roic_hurdle

logger = logging.getLogger(__name__)


# ============================================================================
# Crisis Period Definitions
# ============================================================================

CRISIS_PERIODS = {
    "dot_com_bust": {
        "start": "2000-03-10",
        "end": "2002-10-09",
        "label": "Dot-Com Bust",
        "description": "NASDAQ crash after the dot-com bubble burst.",
    },
    "financial_crisis": {
        "start": "2007-10-09",
        "end": "2009-03-09",
        "label": "2008 Financial Crisis",
        "description": "Global financial crisis triggered by the subprime mortgage collapse.",
    },
    "covid_crash": {
        "start": "2020-02-19",
        "end": "2020-03-23",
        "label": "COVID-19 Crash",
        "description": "Rapid sell-off at the onset of the COVID-19 pandemic.",
    },
    "rate_hike_2022": {
        "start": "2022-01-03",
        "end": "2022-10-12",
        "label": "2022 Rate Hike Selloff",
        "description": "Tech sell-off driven by aggressive Federal Reserve rate hikes.",
    },
}


# ============================================================================
# Single-Ticker Resilience Analysis
# ============================================================================

def analyze_crisis_resilience(
    ticker: str,
    crisis_id: Optional[str] = None,
    service: Optional[StockDataService] = None,
) -> dict:
    """
    Analyze a ticker's performance during market crises.

    For each crisis the ticker has price data for, calculates:
    - Peak-to-trough drawdown during the crisis window
    - Recovery time (days from trough to regain prior peak)
    - Post-crisis 1-year and 3-year return from the trough

    Args:
        ticker: Stock ticker symbol
        crisis_id: Optional single crisis to analyze (key from CRISIS_PERIODS).
                   If None, analyzes all crises with available data.
        service: Optional StockDataService instance

    Returns:
        Dict with ticker, crisis results list, and long-term metrics
    """
    if service is None:
        service = get_stock_data_service()

    ticker = ticker.upper()
    crises_to_check = (
        {crisis_id: CRISIS_PERIODS[crisis_id]}
        if crisis_id and crisis_id in CRISIS_PERIODS
        else CRISIS_PERIODS
    )

    results = []
    for cid, crisis in crises_to_check.items():
        result = _analyze_single_crisis(ticker, cid, crisis, service)
        if result:
            results.append(result)

    # Long-term metrics across available range
    long_term = _calculate_long_term_metrics(ticker, service)

    return {
        "ticker": ticker,
        "crises": results,
        "long_term_metrics": long_term,
        "calculated_at": datetime.now().isoformat(),
    }


def _analyze_single_crisis(
    ticker: str,
    crisis_id: str,
    crisis: dict,
    service: StockDataService,
) -> Optional[dict]:
    """Analyze a single crisis period for a ticker."""
    c_start = crisis["start"]
    c_end = crisis["end"]

    # Load price data covering crisis + 3 years post-crisis for recovery
    try:
        # Need data before crisis start for pre-crisis peak
        pre_start = str(
            (pd.to_datetime(c_start) - pd.DateOffset(months=6)).date()
        )
        # Need data after crisis end for recovery measurement
        post_end = str(
            (pd.to_datetime(c_end) + pd.DateOffset(years=3)).date()
        )
        df = service.load_ticker_data(ticker, start_date=pre_start, end_date=post_end)
    except Exception as e:
        logger.debug(f"No data for {ticker} during {crisis_id}: {e}")
        return None

    if df.empty or len(df) < 10:
        return None

    # Filter to crisis window
    crisis_mask = (df.index >= pd.to_datetime(c_start)) & (
        df.index <= pd.to_datetime(c_end)
    )
    crisis_df = df[crisis_mask]

    if crisis_df.empty or len(crisis_df) < 2:
        return None

    # Pre-crisis peak (highest close before or at crisis start)
    pre_crisis = df[df.index <= pd.to_datetime(c_start)]
    if pre_crisis.empty:
        pre_peak = crisis_df["close"].iloc[0]
    else:
        pre_peak = float(pre_crisis["close"].max())

    # Trough during crisis
    trough_price = float(crisis_df["close"].min())
    trough_date = crisis_df["close"].idxmin()

    # Drawdown
    drawdown_pct = ((trough_price - pre_peak) / pre_peak) * 100

    # Recovery time: days from trough until price >= pre_peak
    post_trough = df[df.index >= trough_date]
    recovery_df = post_trough[post_trough["close"] >= pre_peak]

    if not recovery_df.empty:
        recovery_date = recovery_df.index[0]
        recovery_days = (recovery_date - trough_date).days
    else:
        recovery_date = None
        recovery_days = None  # Not yet recovered in available data

    # Post-crisis returns (from trough)
    post_1yr_end = str((trough_date + pd.DateOffset(years=1)).date())
    post_3yr_end = str((trough_date + pd.DateOffset(years=3)).date())

    post_1yr_df = df[
        (df.index >= trough_date)
        & (df.index <= pd.to_datetime(post_1yr_end))
    ]
    post_3yr_df = df[
        (df.index >= trough_date)
        & (df.index <= pd.to_datetime(post_3yr_end))
    ]

    post_1yr_return = None
    if len(post_1yr_df) > 1:
        post_1yr_return = round(
            ((float(post_1yr_df["close"].iloc[-1]) - trough_price) / trough_price)
            * 100,
            2,
        )

    post_3yr_return = None
    if len(post_3yr_df) > 1:
        post_3yr_return = round(
            ((float(post_3yr_df["close"].iloc[-1]) - trough_price) / trough_price)
            * 100,
            2,
        )

    return {
        "crisis_id": crisis_id,
        "label": crisis["label"],
        "period": f"{c_start} to {c_end}",
        "pre_peak_price": round(pre_peak, 2),
        "trough_price": round(trough_price, 2),
        "trough_date": str(trough_date.date()),
        "drawdown_pct": round(drawdown_pct, 2),
        "recovery_days": recovery_days,
        "recovery_date": str(recovery_date.date()) if recovery_date is not None else None,
        "post_crisis_1yr_return_pct": post_1yr_return,
        "post_crisis_3yr_return_pct": post_3yr_return,
    }


def _calculate_long_term_metrics(
    ticker: str,
    service: StockDataService,
) -> dict:
    """Calculate 20-year CAGR, Sharpe, Sortino, and max drawdown."""
    try:
        df = service.load_ticker_data(ticker, start_date="2000-01-01", end_date="2025-12-31")
    except Exception:
        return {}

    if df.empty or len(df) < 252:
        return {}

    first_close = float(df["close"].iloc[0])
    last_close = float(df["close"].iloc[-1])
    trading_days = len(df)
    years = trading_days / 252

    # CAGR
    cagr = ((last_close / first_close) ** (1 / years) - 1) * 100

    # Daily returns
    daily_returns = df["close"].pct_change().dropna()
    ann_return = float(daily_returns.mean()) * 252
    ann_vol = float(daily_returns.std()) * np.sqrt(252)
    risk_free = 0.02  # 2% assumption

    # Sharpe
    sharpe = (ann_return - risk_free) / ann_vol if ann_vol > 0 else 0.0

    # Sortino (downside deviation only)
    negative_returns = daily_returns[daily_returns < 0]
    downside_std = float(negative_returns.std()) * np.sqrt(252) if len(negative_returns) > 0 else ann_vol
    sortino = (ann_return - risk_free) / downside_std if downside_std > 0 else 0.0

    # Max drawdown
    cummax = df["close"].cummax()
    drawdown = (df["close"] - cummax) / cummax
    max_drawdown_pct = abs(float(drawdown.min())) * 100

    return {
        "period": f"{df.index[0].date()} to {df.index[-1].date()}",
        "years": round(years, 1),
        "cagr_pct": round(cagr, 2),
        "annualized_return_pct": round(ann_return * 100, 2),
        "annualized_volatility_pct": round(ann_vol * 100, 2),
        "sharpe_ratio": round(sharpe, 2),
        "sortino_ratio": round(sortino, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 2),
    }


# ============================================================================
# Peer Resilience Comparison
# ============================================================================

def compare_resilience(
    ticker: str,
    peer_tickers: list[str],
    crisis_id: Optional[str] = None,
) -> dict:
    """
    Compare drawdown and recovery across a ticker and its peers during crises.

    Args:
        ticker: Primary ticker
        peer_tickers: List of peer tickers
        crisis_id: Optional single crisis to focus on

    Returns:
        Dict with comparison table and relative performance summary
    """
    service = get_stock_data_service()
    all_tickers = [ticker.upper()] + [p.upper() for p in peer_tickers]

    # Gather per-ticker results
    all_results = {}
    for t in all_tickers:
        all_results[t] = analyze_crisis_resilience(t, crisis_id=crisis_id, service=service)

    # Build comparison table per crisis
    crises_to_check = (
        {crisis_id: CRISIS_PERIODS[crisis_id]}
        if crisis_id and crisis_id in CRISIS_PERIODS
        else CRISIS_PERIODS
    )

    comparison = []
    for cid in crises_to_check:
        crisis_rows = []
        for t in all_tickers:
            crisis_data = next(
                (c for c in all_results[t]["crises"] if c["crisis_id"] == cid), None
            )
            if crisis_data:
                crisis_rows.append({
                    "ticker": t,
                    "crisis": crisis_data["label"],
                    "drawdown_pct": crisis_data["drawdown_pct"],
                    "recovery_days": crisis_data["recovery_days"],
                    "post_crisis_1yr_return_pct": crisis_data["post_crisis_1yr_return_pct"],
                    "post_crisis_3yr_return_pct": crisis_data["post_crisis_3yr_return_pct"],
                })

        if crisis_rows:
            # Calculate peer average (excluding primary ticker)
            peer_rows = [r for r in crisis_rows if r["ticker"] != ticker.upper()]
            if peer_rows:
                avg_dd = np.mean([r["drawdown_pct"] for r in peer_rows])
                primary_row = next(
                    (r for r in crisis_rows if r["ticker"] == ticker.upper()), None
                )
                if primary_row:
                    relative_perf = primary_row["drawdown_pct"] - avg_dd
                    primary_row["relative_vs_peers_pct"] = round(relative_perf, 2)

            comparison.extend(crisis_rows)

    # Long-term metrics comparison
    long_term_comparison = []
    for t in all_tickers:
        lt = all_results[t].get("long_term_metrics", {})
        if lt:
            long_term_comparison.append({"ticker": t, **lt})

    return {
        "ticker": ticker.upper(),
        "peers": [p.upper() for p in peer_tickers],
        "crisis_comparison": comparison,
        "long_term_comparison": long_term_comparison,
        "calculated_at": datetime.now().isoformat(),
    }


# ============================================================================
# ROIC-Resilience Correlation
# ============================================================================

def correlate_roic_resilience(
    ticker: str,
    peer_tickers: list[str],
) -> dict:
    """
    Correlate pre-crisis ROIC with crisis drawdown depth.

    Tests the hypothesis: companies with higher pre-crisis ROIC
    (stronger moats) experience shallower drawdowns.

    Args:
        ticker: Primary ticker
        peer_tickers: Peer tickers for comparison

    Returns:
        Dict with ROIC-drawdown pairs and correlation analysis
    """
    service = get_stock_data_service()
    all_tickers = [ticker.upper()] + [p.upper() for p in peer_tickers]

    data_points = []

    for t in all_tickers:
        # Get ROIC data
        try:
            roic_result = check_roic_hurdle(t, years=10, use_cache=True)
            if "error" in roic_result:
                continue
            avg_roic = roic_result.get("avg_roic_pct", 0)
        except Exception:
            continue

        # Get crisis drawdowns
        resilience = analyze_crisis_resilience(t, service=service)
        for crisis in resilience.get("crises", []):
            data_points.append({
                "ticker": t,
                "crisis": crisis["label"],
                "avg_roic_pct": avg_roic,
                "drawdown_pct": crisis["drawdown_pct"],
                "recovery_days": crisis["recovery_days"],
            })

    if len(data_points) < 3:
        return {
            "data_points": data_points,
            "correlation": None,
            "finding": "Insufficient data points for correlation analysis.",
        }

    # Calculate correlation between ROIC and drawdown magnitude
    roics = [dp["avg_roic_pct"] for dp in data_points]
    drawdowns = [abs(dp["drawdown_pct"]) for dp in data_points]

    try:
        correlation = float(np.corrcoef(roics, drawdowns)[0, 1])
    except Exception:
        correlation = None

    # Interpretation
    if correlation is not None:
        if correlation < -0.3:
            finding = (
                f"Negative correlation ({correlation:.2f}): Higher ROIC companies tend to "
                f"experience shallower drawdowns, supporting the hypothesis that "
                f"economic moats provide price resilience during crises."
            )
        elif correlation > 0.3:
            finding = (
                f"Positive correlation ({correlation:.2f}): Higher ROIC does not appear "
                f"to reduce drawdowns in this sample. This may reflect that high-growth "
                f"moat companies carry higher valuations vulnerable to re-rating."
            )
        else:
            finding = (
                f"Weak correlation ({correlation:.2f}): No clear relationship between "
                f"ROIC and drawdown depth in this sample."
            )
    else:
        finding = "Could not compute correlation."

    return {
        "data_points": data_points,
        "correlation": round(correlation, 3) if correlation is not None else None,
        "finding": finding,
        "calculated_at": datetime.now().isoformat(),
    }
