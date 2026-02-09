"""
Valuation Estimator & Uncertainty Rating

Provides:
1. Simplified DCF (Discounted Cash Flow) fair value estimation
2. Price / Fair Value ratio with star rating (1-5)
3. Uncertainty Rating (Low to Extreme) based on financial volatility
4. Margin of safety calculations

Uses existing Alpha Vantage fundamental data (income statement, balance sheet,
cash flow) and current price from yfinance.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import numpy as np

from services.fundamentals_provider import get_fundamental_data
from services.roic_calculator import (
    DEFAULT_WACC,
    _safe_float,
    extract_annual_financials,
    calculate_roic_time_series,
)

logger = logging.getLogger(__name__)

# Terminal growth rate assumption (long-run GDP growth)
TERMINAL_GROWTH_RATE = 0.03  # 3%

# Star rating thresholds based on Price / Fair Value ratio
STAR_THRESHOLDS = {
    5: 0.60,   # P/FV < 0.60 -> 5-star (deep discount)
    4: 0.80,   # P/FV < 0.80 -> 4-star
    3: 1.20,   # P/FV < 1.20 -> 3-star (fair value)
    2: 1.40,   # P/FV < 1.40 -> 2-star
    1: float("inf"),  # P/FV >= 1.40 -> 1-star (overvalued)
}

# Uncertainty rating thresholds
UNCERTAINTY_LEVELS = ["Low", "Medium", "High", "Very High", "Extreme"]

# Margin of safety by uncertainty level
MARGIN_OF_SAFETY = {
    "Low": 0.20,
    "Medium": 0.30,
    "High": 0.40,
    "Very High": 0.50,
    "Extreme": 0.60,
}


# ============================================================================
# Uncertainty Rating
# ============================================================================

def calculate_uncertainty_rating(
    ticker: str,
    use_cache: bool = True
) -> dict:
    """
    Calculate an uncertainty rating based on financial volatility metrics.
    
    Factors:
    - Revenue volatility (std dev of annual revenue growth)
    - ROIC volatility (std dev of annual ROIC)
    - Financial leverage (debt / equity ratio)
    - Operating leverage proxy (operating income volatility vs revenue volatility)
    
    Output: Low / Medium / High / Very High / Extreme
    
    Args:
        ticker: Stock ticker symbol
        use_cache: Whether to use cached data
        
    Returns:
        Dict with uncertainty_rating, component scores, margin_of_safety, explanation
    """
    logger.info(f"Calculating uncertainty rating for {ticker}")
    
    try:
        fundamental_data = get_fundamental_data(ticker, use_cache=use_cache)
        df = extract_annual_financials(fundamental_data)
        
        if df.empty or len(df) < 3:
            return {
                "ticker": ticker.upper(),
                "uncertainty_rating": "Very High",
                "uncertainty_score": 3.5,
                "margin_of_safety_pct": 50.0,
                "explanation": "Insufficient financial history to assess uncertainty. Defaulting to Very High.",
                "components": {},
            }
        
        # Sort ascending by year for growth calculations
        df = df.sort_values("year", ascending=True)
        
        components = {}
        scores = []  # 0-4 scale per component (maps to Low=0 ... Extreme=4)
        
        # 1. Revenue volatility
        revenues = df["revenue"].values
        if len(revenues) >= 3:
            rev_growth = np.diff(revenues) / np.abs(revenues[:-1] + 1e-9)
            rev_vol = float(np.std(rev_growth))
            
            if rev_vol < 0.10:
                rev_score = 0  # Low
            elif rev_vol < 0.20:
                rev_score = 1  # Medium
            elif rev_vol < 0.35:
                rev_score = 2  # High
            elif rev_vol < 0.50:
                rev_score = 3  # Very High
            else:
                rev_score = 4  # Extreme
            
            components["revenue_volatility"] = {
                "value": round(rev_vol * 100, 2),
                "label": f"{rev_vol*100:.1f}% std dev of annual growth",
                "score": rev_score,
            }
            scores.append(rev_score)
        
        # 2. ROIC volatility
        roic_df = calculate_roic_time_series(ticker, use_cache=use_cache)
        if not roic_df.empty and len(roic_df) >= 3:
            roic_values = roic_df["roic"].values
            roic_vol = float(np.std(roic_values))
            
            if roic_vol < 0.03:
                roic_score = 0
            elif roic_vol < 0.06:
                roic_score = 1
            elif roic_vol < 0.12:
                roic_score = 2
            elif roic_vol < 0.20:
                roic_score = 3
            else:
                roic_score = 4
            
            components["roic_volatility"] = {
                "value": round(roic_vol * 100, 2),
                "label": f"{roic_vol*100:.1f}% std dev of ROIC",
                "score": roic_score,
            }
            scores.append(roic_score)
        
        # 3. Financial leverage (Debt / Equity)
        latest = df.iloc[-1]  # Most recent year
        equity = latest.get("equity", 0)
        total_debt = latest.get("total_debt", 0)
        
        if equity > 0:
            de_ratio = total_debt / equity
        else:
            de_ratio = 5.0  # Very high if negative equity
        
        if de_ratio < 0.3:
            lev_score = 0
        elif de_ratio < 0.6:
            lev_score = 1
        elif de_ratio < 1.0:
            lev_score = 2
        elif de_ratio < 2.0:
            lev_score = 3
        else:
            lev_score = 4
        
        components["financial_leverage"] = {
            "value": round(de_ratio, 2),
            "label": f"Debt/Equity ratio: {de_ratio:.2f}",
            "score": lev_score,
        }
        scores.append(lev_score)
        
        # 4. Operating leverage (operating income volatility relative to revenue)
        op_incomes = df["operating_income"].values
        if len(op_incomes) >= 3 and len(revenues) >= 3:
            oi_growth = np.diff(op_incomes) / (np.abs(op_incomes[:-1]) + 1e-9)
            oi_vol = float(np.std(oi_growth))
            
            # Operating leverage = ratio of OI volatility to revenue volatility
            op_lev = oi_vol / (rev_vol + 1e-9) if rev_vol > 0.01 else oi_vol * 10
            
            if op_lev < 1.5:
                ol_score = 0
            elif op_lev < 2.5:
                ol_score = 1
            elif op_lev < 4.0:
                ol_score = 2
            elif op_lev < 6.0:
                ol_score = 3
            else:
                ol_score = 4
            
            components["operating_leverage"] = {
                "value": round(op_lev, 2),
                "label": f"Operating leverage ratio: {op_lev:.2f}x",
                "score": ol_score,
            }
            scores.append(ol_score)
        
        # Calculate overall uncertainty
        if scores:
            avg_score = float(np.mean(scores))
        else:
            avg_score = 3.0  # Default to High if no data
        
        # Map to rating
        rating_idx = min(4, max(0, round(avg_score)))
        uncertainty_rating = UNCERTAINTY_LEVELS[rating_idx]
        margin_of_safety = MARGIN_OF_SAFETY[uncertainty_rating]
        
        # Build explanation
        explanation_parts = []
        if "revenue_volatility" in components:
            rv = components["revenue_volatility"]
            explanation_parts.append(f"Revenue growth volatility is {rv['label']}")
        if "roic_volatility" in components:
            rv = components["roic_volatility"]
            explanation_parts.append(f"ROIC volatility is {rv['label']}")
        if "financial_leverage" in components:
            fl = components["financial_leverage"]
            explanation_parts.append(f"{fl['label']}")
        if "operating_leverage" in components:
            ol = components["operating_leverage"]
            explanation_parts.append(f"{ol['label']}")
        
        explanation = (
            f"Uncertainty Rating: {uncertainty_rating}. "
            + "; ".join(explanation_parts) + ". "
            f"A {margin_of_safety*100:.0f}% margin of safety is recommended for this level of uncertainty."
        )
        
        return {
            "ticker": ticker.upper(),
            "uncertainty_rating": uncertainty_rating,
            "uncertainty_score": round(avg_score, 2),
            "margin_of_safety_pct": round(margin_of_safety * 100, 1),
            "components": components,
            "explanation": explanation,
            "calculated_at": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Error calculating uncertainty for {ticker}: {e}")
        return {
            "ticker": ticker.upper(),
            "uncertainty_rating": "Very High",
            "uncertainty_score": 3.5,
            "margin_of_safety_pct": 50.0,
            "explanation": f"Error calculating uncertainty: {str(e)}. Defaulting to Very High.",
            "components": {},
        }


# ============================================================================
# Fair Value Estimation (Simplified DCF)
# ============================================================================

def _extract_fcf_history(fundamental_data: dict) -> list[dict]:
    """
    Extract Free Cash Flow history from cash flow and income statements.
    
    FCF = Operating Cash Flow - Capital Expenditures
    """
    cash_flow = fundamental_data.get("cash_flow", {})
    income_stmt = fundamental_data.get("income_statement", {})
    
    annual_cf = cash_flow.get("annualReports", [])
    annual_income = income_stmt.get("annualReports", [])
    
    # Build revenue lookup by year
    revenue_by_year = {}
    for report in annual_income:
        fiscal_date = report.get("fiscalDateEnding", "")
        year = fiscal_date[:4] if fiscal_date else None
        if year:
            revenue_by_year[year] = _safe_float(report.get("totalRevenue"))
    
    fcf_history = []
    for report in annual_cf:
        fiscal_date = report.get("fiscalDateEnding", "")
        year = fiscal_date[:4] if fiscal_date else None
        if not year:
            continue
        
        operating_cf = _safe_float(report.get("operatingCashflow"))
        capex = abs(_safe_float(report.get("capitalExpenditures")))
        
        fcf = operating_cf - capex
        
        fcf_history.append({
            "year": int(year),
            "fiscal_date": fiscal_date,
            "operating_cashflow": operating_cf,
            "capex": capex,
            "fcf": fcf,
            "revenue": revenue_by_year.get(year, 0),
        })
    
    return sorted(fcf_history, key=lambda x: x["year"])


def _get_current_price(ticker: str) -> Optional[float]:
    """Get current stock price using yfinance."""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
        return None
    except Exception as e:
        logger.warning(f"Could not get current price for {ticker}: {e}")
        return None


def _get_shares_outstanding(ticker: str) -> Optional[float]:
    """Get shares outstanding using yfinance."""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info
        return float(info.get("sharesOutstanding", 0)) or None
    except Exception as e:
        logger.warning(f"Could not get shares outstanding for {ticker}: {e}")
        return None


def estimate_fair_value(
    ticker: str,
    wacc: float = DEFAULT_WACC,
    terminal_growth: float = TERMINAL_GROWTH_RATE,
    projection_years: int = 10,
    use_cache: bool = True
) -> dict:
    """
    Estimate fair (intrinsic) value using a simplified DCF model.
    
    Steps:
    1. Calculate historical Free Cash Flow (FCF = Operating CF - CapEx)
    2. Estimate FCF growth rate from historical data
    3. Project future FCFs for `projection_years` years
    4. Calculate terminal value using Gordon Growth Model
    5. Discount all cash flows to present value at WACC
    6. Divide by shares outstanding to get per-share fair value
    7. Compare to current market price for P/FV ratio
    
    Args:
        ticker: Stock ticker symbol
        wacc: Discount rate (default: 10%)
        terminal_growth: Long-term growth rate (default: 3%)
        projection_years: Years to project FCF (default: 10)
        use_cache: Whether to use cached fundamental data
        
    Returns:
        Dict with fair_value_per_share, current_price, price_to_fair_value,
        star_rating, discount_premium_pct, and detailed breakdown
    """
    logger.info(f"Estimating fair value for {ticker}")
    
    try:
        # Get fundamental data
        fundamental_data = get_fundamental_data(ticker, use_cache=use_cache)
        
        # Extract FCF history
        fcf_history = _extract_fcf_history(fundamental_data)
        
        if len(fcf_history) < 3:
            return {
                "ticker": ticker.upper(),
                "error": "Insufficient cash flow data for DCF (need at least 3 years).",
            }
        
        # Calculate FCF growth rate
        fcfs = [h["fcf"] for h in fcf_history if h["fcf"] > 0]
        
        if len(fcfs) < 2:
            return {
                "ticker": ticker.upper(),
                "error": "Insufficient positive FCF years for DCF projection.",
            }
        
        # Use geometric mean growth rate of positive FCF years
        fcf_growth_rates = []
        for i in range(1, len(fcfs)):
            if fcfs[i - 1] > 0:
                growth = (fcfs[i] / fcfs[i - 1]) - 1
                fcf_growth_rates.append(growth)
        
        if not fcf_growth_rates:
            return {
                "ticker": ticker.upper(),
                "error": "Cannot calculate FCF growth rate.",
            }
        
        # Cap growth rate to reasonable bounds
        avg_growth = float(np.mean(fcf_growth_rates))
        median_growth = float(np.median(fcf_growth_rates))
        
        # Use median (more robust) but cap at 25% to avoid unrealistic projections
        estimated_growth = min(0.25, max(-0.05, median_growth))
        
        # Base FCF: average of last 2 years (smoother than single year)
        recent_fcfs = [h["fcf"] for h in fcf_history[-2:]]
        base_fcf = float(np.mean(recent_fcfs))
        
        if base_fcf <= 0:
            # Try last 3 years
            recent_fcfs = [h["fcf"] for h in fcf_history[-3:] if h["fcf"] > 0]
            if recent_fcfs:
                base_fcf = float(np.mean(recent_fcfs))
            else:
                return {
                    "ticker": ticker.upper(),
                    "error": "Recent FCF is negative -- DCF not applicable for companies not generating free cash flow.",
                }
        
        # Project future FCFs
        projected_fcfs = []
        for year in range(1, projection_years + 1):
            projected_fcf = base_fcf * ((1 + estimated_growth) ** year)
            discounted = projected_fcf / ((1 + wacc) ** year)
            projected_fcfs.append({
                "year": year,
                "projected_fcf": round(projected_fcf, 0),
                "discounted_fcf": round(discounted, 0),
            })
        
        # Terminal value (Gordon Growth Model)
        terminal_fcf = base_fcf * ((1 + estimated_growth) ** projection_years) * (1 + terminal_growth)
        terminal_value = terminal_fcf / (wacc - terminal_growth)
        discounted_terminal = terminal_value / ((1 + wacc) ** projection_years)
        
        # Total enterprise value
        sum_discounted_fcfs = sum(pf["discounted_fcf"] for pf in projected_fcfs)
        enterprise_value = sum_discounted_fcfs + discounted_terminal
        
        # Get current price and shares outstanding
        current_price = _get_current_price(ticker)
        shares_outstanding = _get_shares_outstanding(ticker)
        
        if not shares_outstanding or shares_outstanding <= 0:
            return {
                "ticker": ticker.upper(),
                "error": "Could not retrieve shares outstanding.",
                "enterprise_value": round(enterprise_value, 0),
            }
        
        # Fair value per share
        fair_value_per_share = enterprise_value / shares_outstanding
        
        # Price / Fair Value ratio
        if current_price and current_price > 0:
            price_to_fair_value = current_price / fair_value_per_share
            discount_premium_pct = (1 - price_to_fair_value) * 100
        else:
            price_to_fair_value = None
            discount_premium_pct = None
        
        # Star rating
        star_rating = _calculate_star_rating(price_to_fair_value)
        
        # Get uncertainty for adjusted star rating
        uncertainty = calculate_uncertainty_rating(ticker, use_cache=use_cache)
        margin_of_safety = uncertainty.get("margin_of_safety_pct", 30) / 100
        
        # Adjusted fair value (with margin of safety)
        adjusted_fair_value = fair_value_per_share * (1 - margin_of_safety)
        
        return {
            "ticker": ticker.upper(),
            "fair_value_per_share": round(fair_value_per_share, 2),
            "adjusted_fair_value": round(adjusted_fair_value, 2),
            "current_price": round(current_price, 2) if current_price else None,
            "price_to_fair_value": round(price_to_fair_value, 2) if price_to_fair_value else None,
            "discount_premium_pct": round(discount_premium_pct, 1) if discount_premium_pct is not None else None,
            "star_rating": star_rating,
            "uncertainty_rating": uncertainty.get("uncertainty_rating"),
            "margin_of_safety_pct": uncertainty.get("margin_of_safety_pct"),
            "dcf_assumptions": {
                "wacc_pct": round(wacc * 100, 2),
                "fcf_growth_rate_pct": round(estimated_growth * 100, 2),
                "terminal_growth_rate_pct": round(terminal_growth * 100, 2),
                "projection_years": projection_years,
                "base_fcf": round(base_fcf, 0),
            },
            "dcf_breakdown": {
                "sum_discounted_fcfs": round(sum_discounted_fcfs, 0),
                "discounted_terminal_value": round(discounted_terminal, 0),
                "enterprise_value": round(enterprise_value, 0),
                "shares_outstanding": shares_outstanding,
            },
            "fcf_history": [
                {
                    "year": h["year"],
                    "fcf": round(h["fcf"], 0),
                    "revenue": round(h["revenue"], 0),
                }
                for h in fcf_history[-5:]  # Last 5 years
            ],
            "projected_fcfs": projected_fcfs[:5],  # First 5 years of projection
            "calculated_at": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Error estimating fair value for {ticker}: {e}")
        return {
            "ticker": ticker.upper(),
            "error": f"Failed to estimate fair value: {str(e)}",
        }


def _calculate_star_rating(price_to_fair_value: Optional[float]) -> int:
    """
    Calculate star rating from Price/Fair Value ratio.
    
    5-star: P/FV < 0.60 (deep value)
    4-star: P/FV 0.60-0.80
    3-star: P/FV 0.80-1.20 (fairly valued)
    2-star: P/FV 1.20-1.40
    1-star: P/FV > 1.40 (overvalued)
    """
    if price_to_fair_value is None:
        return 3  # Default to fair value if no price
    
    for stars in sorted(STAR_THRESHOLDS.keys(), reverse=True):
        if price_to_fair_value < STAR_THRESHOLDS[stars]:
            return stars
    
    return 1
