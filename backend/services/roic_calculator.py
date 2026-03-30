"""
ROIC (Return on Invested Capital) Calculator

Calculates ROIC, NOPAT, Invested Capital, and related financial metrics
from Alpha Vantage fundamental data.

ROIC Formula:
    ROIC = NOPAT / Invested Capital

Where:
    NOPAT = Operating Income × (1 - Effective Tax Rate)
    Invested Capital = Total Equity + Total Debt - Excess Cash

This provides quantitative proof of economic moats when ROIC > WACC
consistently over 10 years.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from services.fundamentals_provider import get_fundamental_data

logger = logging.getLogger(__name__)

# Default WACC estimate for tech companies (can be refined later)
DEFAULT_WACC = 0.10  # 10%


def _safe_float(value: str | float | None) -> float:
    """Safely convert string/number to float."""
    if value is None or value == "None":
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


# ---------------------------------------------------------------------------
# Morningstar-Style WACC Estimation (Building-Block Approach)
# ---------------------------------------------------------------------------
#
# Morningstar does NOT use raw market beta or standard CAPM. Instead it uses
# a qualitative building-block method:
#
#   COE = Real Market Return + Inflation Expectation +/- Systematic Risk Premium
#   COD = Risk-Free Rate + Corporate Credit Spread (tax-adjusted)
#   WACC = w_e * COE + w_d * COD
#
# Systematic risk is assigned as a discrete category inferred from business
# and financial characteristics, not from price covariance.
# Capital structure uses normalized long-run weights, not today's market cap.

# Base assumptions (Morningstar global equity model)
_REAL_MARKET_RETURN = 0.065       # 6.5% long-run real equity return
_INFLATION_EXPECTATION = 0.025    # 2.5% expected inflation
_BASE_NOMINAL_COE = _REAL_MARKET_RETURN + _INFLATION_EXPECTATION  # ~9.0%

# Systematic risk adjustments applied to COE
_SYSTEMATIC_RISK_PREMIUM = {
    "Below Average": -0.015,   # stable, predictable businesses
    "Average":        0.000,
    "Above Average":  0.020,   # cyclical or operationally leveraged
    "Very High":      0.045,   # highly volatile or unproven
}

# Credit-spread buckets for pre-tax cost of debt (added to risk-free rate)
_CREDIT_SPREAD = {
    "Low":      0.010,   # AAA/AA equivalent, strong balance sheet
    "Moderate": 0.020,   # A/BBB, investment grade
    "Elevated": 0.035,   # BB, moderate leverage
    "High":     0.055,   # B or worse, significant leverage
}


def _classify_systematic_risk(df: "pd.DataFrame") -> str:
    """
    Infer a Morningstar-style systematic risk category from financials.

    Uses revenue volatility, operating-income volatility, and leverage
    as proxies for cyclicality, operating leverage, and financial risk.
    """
    if df.empty or len(df) < 4:
        return "Average"

    df_sorted = df.sort_values("year", ascending=True)

    # Revenue volatility
    revenues = df_sorted["revenue"].values
    rev_growth = np.diff(revenues) / (np.abs(revenues[:-1]) + 1e-9)
    rev_vol = float(np.std(rev_growth)) if len(rev_growth) >= 3 else 0.15

    # Operating income volatility
    oi = df_sorted["operating_income"].values
    oi_growth = np.diff(oi) / (np.abs(oi[:-1]) + 1e-9)
    oi_vol = float(np.std(oi_growth)) if len(oi_growth) >= 3 else 0.25

    # Leverage (D/E)
    latest = df_sorted.iloc[-1]
    equity = float(latest.get("equity", 0))
    total_debt = float(latest.get("total_debt", 0))
    de_ratio = total_debt / equity if equity > 0 else 3.0

    # Scoring: each factor contributes 0-3 points
    score = 0

    # Revenue cyclicality
    if rev_vol < 0.08:
        score += 0
    elif rev_vol < 0.15:
        score += 1
    elif rev_vol < 0.30:
        score += 2
    else:
        score += 3

    # Operating leverage / earnings volatility
    if oi_vol < 0.15:
        score += 0
    elif oi_vol < 0.30:
        score += 1
    elif oi_vol < 0.50:
        score += 2
    else:
        score += 3

    # Financial leverage
    if de_ratio < 0.3:
        score += 0
    elif de_ratio < 0.8:
        score += 1
    elif de_ratio < 1.5:
        score += 2
    else:
        score += 3

    # Map aggregate score to Morningstar category (max possible = 9)
    if score <= 2:
        return "Below Average"
    elif score <= 4:
        return "Average"
    elif score <= 6:
        return "Above Average"
    else:
        return "Very High"


def _classify_credit_risk(df: "pd.DataFrame") -> str:
    """
    Infer a credit-risk bucket from interest coverage and leverage.

    Approximates the credit-spread category Morningstar would layer
    onto the risk-free rate for cost of debt.
    """
    if df.empty:
        return "Moderate"

    latest = df.sort_values("year", ascending=False).iloc[0]
    equity = float(latest.get("equity", 0))
    total_debt = float(latest.get("total_debt", 0))
    operating_income = float(latest.get("operating_income", 0))
    interest_expense = abs(float(latest.get("interest_expense", 0))) if "interest_expense" in latest.index else 0.0

    de_ratio = total_debt / equity if equity > 0 else 5.0
    coverage = operating_income / interest_expense if interest_expense > 0 else 50.0

    if coverage > 12 and de_ratio < 0.3:
        return "Low"
    elif coverage > 5 and de_ratio < 1.0:
        return "Moderate"
    elif coverage > 2 and de_ratio < 2.0:
        return "Elevated"
    else:
        return "High"


def _normalize_capital_weights(df: "pd.DataFrame") -> tuple[float, float]:
    """
    Derive normalized equity/debt weights from long-run balance-sheet structure.

    Uses the median debt-to-total-capital ratio over available history
    rather than today's market cap, which avoids distortion from price
    momentum, bubbles, or temporary distress.
    """
    if df.empty or len(df) < 2:
        return 0.80, 0.20

    equity_vals = df["equity"].values
    debt_vals = df["total_debt"].values
    total_capital = equity_vals + debt_vals

    valid = total_capital > 0
    if not valid.any():
        return 0.80, 0.20

    debt_fractions = debt_vals[valid] / total_capital[valid]
    median_debt_frac = float(np.median(debt_fractions))
    median_debt_frac = max(0.0, min(median_debt_frac, 0.70))

    w_d = median_debt_frac
    w_e = 1.0 - w_d
    return round(w_e, 4), round(w_d, 4)


def estimate_wacc(ticker: str, use_cache: bool = True) -> float:
    """
    Estimate company-specific WACC using a Morningstar-style building-block
    approach.

    Cost of Equity:
      COE = base_nominal_return (9.0%) +/- systematic_risk_premium
      Systematic risk is classified from revenue volatility, operating
      leverage, and financial leverage -- not from market beta.

    Cost of Debt:
      COD = (risk_free_rate + credit_spread) * (1 - tax_rate)
      Credit spread is assigned from interest coverage and D/E ratio.

    Weights:
      Normalized from median historical debt/total-capital, not today's
      market cap.

    Falls back to DEFAULT_WACC when data is insufficient.
    """
    try:
        fundamental_data = get_fundamental_data(ticker, use_cache=use_cache)
        df_financials = extract_annual_financials(fundamental_data)

        if df_financials.empty:
            logger.warning(f"No financials for WACC estimation of {ticker}, using default")
            return DEFAULT_WACC

        # --- Cost of Equity ---
        risk_category = _classify_systematic_risk(df_financials)
        coe = _BASE_NOMINAL_COE + _SYSTEMATIC_RISK_PREMIUM[risk_category]

        # --- Cost of Debt ---
        credit_category = _classify_credit_risk(df_financials)
        # Morningstar COD = inflation + base spread + credit spread, tax-adjusted
        pretax_cod = _INFLATION_EXPECTATION + 0.02 + _CREDIT_SPREAD[credit_category]
        latest = df_financials.sort_values("year", ascending=False).iloc[0]
        tax_rate = float(latest.get("tax_rate", 0.21))
        cod = pretax_cod * (1 - tax_rate)

        # --- Capital Structure ---
        w_e, w_d = _normalize_capital_weights(df_financials)

        wacc = w_e * coe + w_d * cod

        logger.info(
            f"WACC for {ticker}: {wacc:.4f} "
            f"(COE={coe:.4f} [{risk_category}], "
            f"COD={cod:.4f} [{credit_category}], "
            f"w_e={w_e:.2f}, w_d={w_d:.2f})"
        )
        return round(wacc, 4)

    except Exception as e:
        logger.warning(f"WACC estimation failed for {ticker}: {e}, using default")
        return DEFAULT_WACC


def estimate_wacc_detailed(ticker: str, use_cache: bool = True) -> dict:
    """
    Return full WACC breakdown for transparency and teaching.

    Same logic as estimate_wacc() but returns the intermediate
    classifications and assumptions so the tutor can explain *why*
    a particular WACC was chosen.
    """
    result = {
        "ticker": ticker.upper(),
        "wacc": DEFAULT_WACC,
        "methodology": "Morningstar-style building-block",
        "assumptions": {
            "real_market_return_pct": _REAL_MARKET_RETURN * 100,
            "inflation_expectation_pct": _INFLATION_EXPECTATION * 100,
            "base_nominal_coe_pct": _BASE_NOMINAL_COE * 100,
        },
    }
    try:
        fundamental_data = get_fundamental_data(ticker, use_cache=use_cache)
        df_financials = extract_annual_financials(fundamental_data)

        if df_financials.empty:
            result["error"] = "Insufficient financial data"
            return result

        risk_category = _classify_systematic_risk(df_financials)
        coe = _BASE_NOMINAL_COE + _SYSTEMATIC_RISK_PREMIUM[risk_category]

        credit_category = _classify_credit_risk(df_financials)
        pretax_cod = _INFLATION_EXPECTATION + 0.02 + _CREDIT_SPREAD[credit_category]
        latest = df_financials.sort_values("year", ascending=False).iloc[0]
        tax_rate = float(latest.get("tax_rate", 0.21))
        cod = pretax_cod * (1 - tax_rate)

        w_e, w_d = _normalize_capital_weights(df_financials)
        wacc = w_e * coe + w_d * cod

        result.update({
            "wacc": round(wacc, 4),
            "wacc_pct": round(wacc * 100, 2),
            "cost_of_equity": {
                "coe_pct": round(coe * 100, 2),
                "systematic_risk_category": risk_category,
                "risk_premium_pct": round(_SYSTEMATIC_RISK_PREMIUM[risk_category] * 100, 2),
            },
            "cost_of_debt": {
                "pretax_cod_pct": round(pretax_cod * 100, 2),
                "aftertax_cod_pct": round(cod * 100, 2),
                "credit_risk_category": credit_category,
                "credit_spread_pct": round(_CREDIT_SPREAD[credit_category] * 100, 2),
                "tax_rate_pct": round(tax_rate * 100, 2),
            },
            "capital_structure": {
                "equity_weight_pct": round(w_e * 100, 2),
                "debt_weight_pct": round(w_d * 100, 2),
                "source": "normalized median historical D/(D+E)",
            },
        })

    except Exception as e:
        result["error"] = str(e)

    return result


def calculate_nopat(operating_income: float, tax_rate: float) -> float:
    """
    Calculate NOPAT (Net Operating Profit After Tax).
    
    NOPAT = Operating Income × (1 - Tax Rate)
    
    Args:
        operating_income: Operating income (EBIT)
        tax_rate: Effective tax rate (as decimal, e.g., 0.21 for 21%)
        
    Returns:
        NOPAT value
    """
    if operating_income <= 0:
        return 0.0
    
    # Tax rate should be between 0 and 1
    tax_rate = max(0.0, min(1.0, tax_rate))
    
    nopat = operating_income * (1 - tax_rate)
    return nopat


def calculate_invested_capital(
    equity: float,
    total_debt: float,
    cash: float,
    excess_cash_ratio: float = 0.02
) -> float:
    """
    Calculate Invested Capital.
    
    Invested Capital = Total Equity + Total Debt - Excess Cash
    
    Excess cash is typically defined as cash beyond operational needs
    (often 2% of revenue, but we use total cash as a simplification).
    
    Args:
        equity: Total shareholder equity
        total_debt: Total debt (short-term + long-term)
        cash: Cash and cash equivalents
        excess_cash_ratio: Ratio of cash to consider as excess (default: 1.0 = all cash)
        
    Returns:
        Invested capital value
    """
    # For simplicity, treat all cash as excess cash
    # (In reality, companies need some cash for operations)
    excess_cash = cash * (1.0 if excess_cash_ratio >= 1.0 else excess_cash_ratio)
    
    invested_capital = equity + total_debt - excess_cash
    
    # Invested capital should be positive
    return max(invested_capital, 1.0)  # Avoid division by zero


def calculate_roic(nopat: float, invested_capital: float) -> float:
    """
    Calculate ROIC (Return on Invested Capital).
    
    ROIC = NOPAT / Invested Capital
    
    Args:
        nopat: Net Operating Profit After Tax
        invested_capital: Invested capital (equity + debt - excess cash)
        
    Returns:
        ROIC as decimal (e.g., 0.15 for 15%)
    """
    if invested_capital <= 0:
        return 0.0
    
    roic = nopat / invested_capital
    return roic


def calculate_economic_profit(
    roic: float,
    wacc: float,
    invested_capital: float
) -> dict:
    """
    Calculate Economic Profit (excess returns above cost of capital).
    
    Economic Profit = (ROIC - WACC) x Invested Capital
    
    This is the dollar amount of value created (or destroyed) above what
    investors require. Positive economic profit = moat evidence.
    
    Args:
        roic: Return on Invested Capital (decimal, e.g. 0.30 for 30%)
        wacc: Weighted Average Cost of Capital (decimal, e.g. 0.10 for 10%)
        invested_capital: Total invested capital in dollars
        
    Returns:
        Dict with spread_pct, economic_profit (dollar amount)
    """
    spread = roic - wacc
    economic_profit = spread * invested_capital
    
    return {
        "spread_pct": round(spread * 100, 2),
        "economic_profit": round(economic_profit, 0),
    }


def calculate_effective_tax_rate(
    income_tax_expense: float,
    income_before_tax: float
) -> float:
    """
    Calculate effective tax rate.
    
    Effective Tax Rate = Income Tax Expense / Income Before Tax
    
    Args:
        income_tax_expense: Total income tax expense
        income_before_tax: Income before tax (typically operating income or net income + tax)
        
    Returns:
        Effective tax rate as decimal (e.g., 0.21 for 21%)
    """
    if income_before_tax <= 0:
        return 0.21  # Default corporate tax rate assumption
    
    tax_rate = income_tax_expense / income_before_tax
    
    # Tax rate should be between 0 and 100%
    return max(0.0, min(1.0, tax_rate))


def extract_annual_financials(fundamental_data: dict) -> pd.DataFrame:
    """
    Extract and combine annual financial data into a DataFrame.
    
    Args:
        fundamental_data: Combined fundamental data from get_fundamental_data()
        
    Returns:
        DataFrame with columns: year, revenue, operating_income, net_income,
                                total_assets, equity, cash, total_debt, tax_rate
    """
    income_stmt = fundamental_data.get("income_statement", {})
    balance_sheet = fundamental_data.get("balance_sheet", {})
    
    annual_income = income_stmt.get("annualReports", [])
    annual_balance = balance_sheet.get("annualReports", [])
    
    # Create dict keyed by fiscal year
    data_by_year = {}
    
    # Process income statement
    for report in annual_income:
        fiscal_date = report.get("fiscalDateEnding", "")
        year = fiscal_date[:4] if fiscal_date else None
        
        if not year:
            continue
        
        if year not in data_by_year:
            data_by_year[year] = {}
        
        data_by_year[year].update({
            "fiscal_date": fiscal_date,
            "revenue": _safe_float(report.get("totalRevenue")),
            "operating_income": _safe_float(report.get("operatingIncome")),
            "net_income": _safe_float(report.get("netIncome")),
            "interest_expense": _safe_float(report.get("interestExpense")),
            "income_tax_expense": _safe_float(report.get("incomeTaxExpense")),
            "income_before_tax": _safe_float(report.get("incomeBeforeTax")),
        })
    
    # Process balance sheet
    for report in annual_balance:
        fiscal_date = report.get("fiscalDateEnding", "")
        year = fiscal_date[:4] if fiscal_date else None
        
        if not year:
            continue
        
        if year not in data_by_year:
            data_by_year[year] = {}
        
        long_term_debt = _safe_float(report.get("longTermDebt"))
        short_term_debt = _safe_float(report.get("shortTermDebt"))
        
        # If short/long term debt not available, try alternative fields
        if long_term_debt == 0 and short_term_debt == 0:
            # Try shortLongTermDebtTotal (used by some companies like GOOGL, PLTR)
            short_long_total = _safe_float(report.get("shortLongTermDebtTotal"))
            if short_long_total > 0:
                # Split proportionally or use as long-term (conservative)
                long_term_debt = short_long_total
            else:
                # Try other alternative fields
                long_term_debt = _safe_float(report.get("longTermDebtNoncurrent"))
                short_term_debt = _safe_float(report.get("currentDebt"))
        
        data_by_year[year].update({
            "total_assets": _safe_float(report.get("totalAssets")),
            "equity": _safe_float(report.get("totalShareholderEquity")),
            "total_liabilities": _safe_float(report.get("totalLiabilities")),
            "current_liabilities": _safe_float(report.get("totalCurrentLiabilities")),
            "cash": _safe_float(report.get("cashAndCashEquivalentsAtCarryingValue")),
            "long_term_debt": long_term_debt,
            "short_term_debt": short_term_debt,
        })
    
    # Convert to DataFrame
    records = []
    for year, data in sorted(data_by_year.items()):
        # Calculate total debt
        total_debt = data.get("long_term_debt", 0) + data.get("short_term_debt", 0)
        
        # Calculate effective tax rate
        income_tax = data.get("income_tax_expense", 0)
        income_before_tax = data.get("income_before_tax", 0)
        
        # If income_before_tax not available, estimate it
        if income_before_tax == 0:
            net_income = data.get("net_income", 0)
            income_before_tax = net_income + income_tax
        
        tax_rate = calculate_effective_tax_rate(income_tax, income_before_tax)
        
        records.append({
            "year": int(year),
            "fiscal_date": data.get("fiscal_date", ""),
            "revenue": data.get("revenue", 0),
            "operating_income": data.get("operating_income", 0),
            "net_income": data.get("net_income", 0),
            "total_assets": data.get("total_assets", 0),
            "equity": data.get("equity", 0),
            "cash": data.get("cash", 0),
            "total_debt": total_debt,
            "interest_expense": data.get("interest_expense", 0),
            "tax_rate": tax_rate,
        })
    
    df = pd.DataFrame(records)
    return df.sort_values("year", ascending=False)  # Most recent first


def calculate_roic_time_series(
    ticker: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Calculate ROIC time series for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        start_year: Start year (inclusive), None for all available
        end_year: End year (inclusive), None for all available
        use_cache: Whether to use cached fundamental data
        
    Returns:
        DataFrame with columns: year, roic, nopat, invested_capital, operating_income, etc.
    """
    logger.info(f"Calculating ROIC time series for {ticker}")
    
    # Fetch fundamental data
    fundamental_data = get_fundamental_data(ticker, use_cache=use_cache)
    
    # Extract annual financials
    df = extract_annual_financials(fundamental_data)
    
    if df.empty:
        logger.warning(f"No financial data available for {ticker}")
        return pd.DataFrame()
    
    # Filter by year range
    if start_year:
        df = df[df["year"] >= start_year]
    if end_year:
        df = df[df["year"] <= end_year]
    
    # Calculate ROIC for each year
    df["nopat"] = df.apply(
        lambda row: calculate_nopat(row["operating_income"], row["tax_rate"]),
        axis=1
    )
    
    df["invested_capital"] = df.apply(
        lambda row: calculate_invested_capital(
            row["equity"],
            row["total_debt"],
            row["cash"]
        ),
        axis=1
    )
    
    df["roic"] = df.apply(
        lambda row: calculate_roic(row["nopat"], row["invested_capital"]),
        axis=1
    )
    
    # Add percentage columns for easier reading
    df["roic_pct"] = df["roic"] * 100
    df["tax_rate_pct"] = df["tax_rate"] * 100
    
    # Add economic profit columns (ROIC - WACC spread and dollar amount)
    df["roic_wacc_spread"] = df["roic"] - DEFAULT_WACC
    df["roic_wacc_spread_pct"] = df["roic_wacc_spread"] * 100
    df["economic_profit"] = df["roic_wacc_spread"] * df["invested_capital"]
    
    return df


def estimate_fade_period(
    df: pd.DataFrame,
    wacc: float = DEFAULT_WACC
) -> dict:
    """
    Estimate how long excess returns (ROIC > WACC) can be sustained.
    
    Uses linear regression on ROIC time series to project when ROIC
    would converge to WACC. Classifies into three stages:
    - Stage I (Explicit): Recent actual ROIC data (last 5 years)
    - Stage II (Fade): Projected years until ROIC converges to WACC  
    - Stage III (Terminal): ROIC = WACC (no excess returns)
    
    Args:
        df: DataFrame with 'year' and 'roic' columns (from calculate_roic_time_series)
        wacc: Cost of capital threshold
        
    Returns:
        Dict with estimated_fade_years, stage classification, moat durability assessment
    """
    if df.empty or len(df) < 3:
        return {
            "estimated_fade_years": None,
            "stage": "insufficient_data",
            "durability": "unknown",
            "explanation": "Insufficient data to estimate fade period."
        }
    
    # Sort by year ascending for regression
    sorted_df = df.sort_values("year", ascending=True)
    years = sorted_df["year"].values.astype(float)
    roics = sorted_df["roic"].values
    
    # Current average ROIC
    avg_roic = float(roics.mean())
    recent_roic = float(roics[-3:].mean()) if len(roics) >= 3 else avg_roic
    
    # If ROIC is already below WACC, no moat
    if avg_roic <= wacc:
        return {
            "estimated_fade_years": 0,
            "stage": "terminal",
            "durability": "none",
            "explanation": (
                f"Average ROIC ({avg_roic*100:.1f}%) is at or below cost of capital "
                f"({wacc*100:.1f}%). No excess returns to fade."
            )
        }
    
    # Linear regression: ROIC = slope * year + intercept
    try:
        slope, intercept = np.polyfit(years, roics, 1)
    except (np.linalg.LinAlgError, ValueError):
        slope = 0.0
        intercept = avg_roic
    
    # Project when ROIC crosses WACC (solve: slope * year + intercept = wacc)
    if slope >= 0:
        # ROIC is stable or improving -- moat not fading
        if recent_roic > wacc * 2:
            fade_years = 20
            durability = "very_strong"
        elif recent_roic > wacc * 1.5:
            fade_years = 15
            durability = "strong"
        else:
            fade_years = 10
            durability = "moderate"
        
        explanation = (
            f"ROIC trend is {'improving' if slope > 0.001 else 'stable'} "
            f"(slope: {slope*100:+.2f}% per year). "
            f"Recent ROIC ({recent_roic*100:.1f}%) is {recent_roic/wacc:.1f}x the cost of capital. "
            f"Estimated {fade_years}+ years of excess returns."
        )
    else:
        # ROIC is declining -- calculate crossover year
        last_year = float(years[-1])
        crossover_year = (wacc - intercept) / slope if slope != 0 else last_year + 50
        fade_years = max(0, int(crossover_year - last_year))
        
        if fade_years > 20:
            durability = "strong"
            fade_years = 20  # Cap at 20
        elif fade_years > 10:
            durability = "moderate"
        elif fade_years > 5:
            durability = "weak"
        else:
            durability = "eroding"
        
        explanation = (
            f"ROIC trend is declining ({slope*100:+.2f}% per year). "
            f"At current trajectory, ROIC would reach cost of capital "
            f"({wacc*100:.1f}%) in approximately {fade_years} years. "
        )
        if durability == "eroding":
            explanation += "The moat appears to be eroding rapidly."
        elif durability == "weak":
            explanation += "The moat has limited remaining durability."
    
    # Stage classification
    if fade_years >= 15:
        stage = "wide_moat"
        stage_description = (
            f"Stage I (actual, last 5yr): ROIC ~{recent_roic*100:.1f}%. "
            f"Stage II (fade): {fade_years}+ years until ROIC converges to WACC. "
            f"Stage III (terminal): ROIC = WACC ({wacc*100:.1f}%)."
        )
    elif fade_years >= 8:
        stage = "narrow_moat"
        stage_description = (
            f"Stage I (actual): ROIC ~{recent_roic*100:.1f}%. "
            f"Stage II (fade): ~{fade_years} years until convergence. "
            f"Stage III (terminal): ROIC = WACC."
        )
    else:
        stage = "no_moat"
        stage_description = (
            f"Stage I (actual): ROIC ~{recent_roic*100:.1f}%. "
            f"Stage II (fade): ~{fade_years} years -- rapid convergence expected. "
            f"Stage III (terminal): Approaching."
        )
    
    return {
        "estimated_fade_years": fade_years,
        "stage": stage,
        "durability": durability,
        "roic_slope_pct_per_year": round(slope * 100, 3),
        "recent_roic_pct": round(recent_roic * 100, 2),
        "stage_description": stage_description,
        "explanation": explanation,
    }


def check_roic_hurdle(
    ticker: str,
    years: int = 10,
    wacc: Optional[float] = None,
    use_cache: bool = True
) -> dict:
    """
    Check if a company passes the ROIC hurdle (sustained ROIC > WACC over time).
    
    Args:
        ticker: Stock ticker symbol
        years: Number of years to analyze (default: 10)
        wacc: Weighted Average Cost of Capital (default: 10% for tech)
        use_cache: Whether to use cached data
        
    Returns:
        Dictionary with ROIC hurdle analysis including:
        - ticker
        - period
        - years_analyzed
        - avg_roic, median_roic, min_roic, max_roic
        - wacc
        - hurdle_passed (True if avg ROIC > WACC)
        - years_above_wacc
        - years_above_hurdle_pct
        - roic_trend ("strengthening", "stable", "weakening")
        - annual_data (list of yearly ROIC values)
    """
    if wacc is None:
        wacc = DEFAULT_WACC
    
    # Calculate ROIC time series
    df = calculate_roic_time_series(ticker, use_cache=use_cache)
    
    if df.empty:
        return {
            "ticker": ticker.upper(),
            "error": "No financial data available",
            "hurdle_passed": False
        }
    
    # Limit to requested number of years (most recent)
    df = df.head(years)
    
    if len(df) == 0:
        return {
            "ticker": ticker.upper(),
            "error": "Insufficient data",
            "hurdle_passed": False
        }
    
    # Calculate statistics
    roic_values = df["roic"].values
    years_analyzed = len(df)
    
    avg_roic = float(roic_values.mean())
    median_roic = float(df["roic"].median())
    min_roic = float(roic_values.min())
    max_roic = float(roic_values.max())
    
    # Check years above WACC
    years_above_wacc = int((roic_values > wacc).sum())
    years_above_hurdle_pct = (years_above_wacc / years_analyzed) * 100
    
    # Determine trend (compare recent 3 years vs older years)
    if years_analyzed >= 6:
        recent_avg = roic_values[:3].mean()
        older_avg = roic_values[3:].mean()
        
        if recent_avg > older_avg * 1.1:
            trend = "strengthening"
        elif recent_avg < older_avg * 0.9:
            trend = "weakening"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"
    
    # Calculate excess profit metrics
    avg_spread = avg_roic - wacc
    avg_invested_capital = float(df["invested_capital"].mean())
    avg_economic_profit = avg_spread * avg_invested_capital
    cumulative_economic_profit = float(df["economic_profit"].sum()) if "economic_profit" in df.columns else 0.0
    
    # Build annual data list with economic profit
    annual_data = []
    for _, row in df.iterrows():
        ep = calculate_economic_profit(float(row["roic"]), wacc, float(row["invested_capital"]))
        annual_data.append({
            "year": int(row["year"]),
            "roic": round(float(row["roic"]), 4),
            "roic_pct": round(float(row["roic_pct"]), 2),
            "above_wacc": bool(row["roic"] > wacc),
            "nopat": round(float(row["nopat"]), 0),
            "invested_capital": round(float(row["invested_capital"]), 0),
            "roic_wacc_spread_pct": ep["spread_pct"],
            "economic_profit": ep["economic_profit"],
        })
    
    # Determine if hurdle passed
    # Criteria: Average ROIC > WACC AND at least 70% of years above WACC
    hurdle_passed = (avg_roic > wacc) and (years_above_hurdle_pct >= 70)
    
    # Estimate fade period
    fade = estimate_fade_period(df, wacc)
    
    return {
        "ticker": ticker.upper(),
        "period": f"{df['year'].min()}-{df['year'].max()}",
        "years_analyzed": years_analyzed,
        "avg_roic": round(avg_roic, 4),
        "avg_roic_pct": round(avg_roic * 100, 2),
        "median_roic": round(median_roic, 4),
        "median_roic_pct": round(median_roic * 100, 2),
        "min_roic": round(min_roic, 4),
        "min_roic_pct": round(min_roic * 100, 2),
        "max_roic": round(max_roic, 4),
        "max_roic_pct": round(max_roic * 100, 2),
        "wacc": round(wacc, 4),
        "wacc_pct": round(wacc * 100, 2),
        "hurdle_passed": hurdle_passed,
        "years_above_wacc": years_above_wacc,
        "years_above_hurdle_pct": round(years_above_hurdle_pct, 1),
        "roic_trend": trend,
        # Excess profit metrics (NEW)
        "avg_roic_wacc_spread_pct": round(avg_spread * 100, 2),
        "avg_economic_profit": round(avg_economic_profit, 0),
        "cumulative_economic_profit": round(cumulative_economic_profit, 0),
        # Fade period (NEW)
        "fade_period": fade,
        "annual_data": annual_data,
        "calculated_at": datetime.now().isoformat()
    }


def compare_roic_to_peers(
    ticker: str,
    peer_tickers: list[str],
    years: int = 10,
    use_cache: bool = True
) -> dict:
    """
    Compare a company's ROIC to peer group average.
    
    Args:
        ticker: Primary ticker to analyze
        peer_tickers: List of peer ticker symbols
        years: Number of years to analyze
        use_cache: Whether to use cached data
        
    Returns:
        Dictionary with comparison data including:
        - ticker
        - ticker_avg_roic
        - peer_avg_roic
        - roic_advantage (ticker - peer average)
        - peer_data (list of peer ROIC values)
    """
    logger.info(f"Comparing {ticker} ROIC to {len(peer_tickers)} peers")
    
    # Get ticker ROIC
    ticker_result = check_roic_hurdle(ticker, years=years, use_cache=use_cache)
    
    if "error" in ticker_result:
        return ticker_result
    
    ticker_avg_roic = ticker_result["avg_roic"]
    
    # Get peer ROICs
    peer_data = []
    peer_roics = []
    
    for peer in peer_tickers:
        try:
            peer_result = check_roic_hurdle(peer, years=years, use_cache=use_cache)
            if "error" not in peer_result:
                peer_avg_roic = peer_result["avg_roic"]
                peer_roics.append(peer_avg_roic)
                peer_data.append({
                    "ticker": peer.upper(),
                    "avg_roic": round(peer_avg_roic, 4),
                    "avg_roic_pct": round(peer_avg_roic * 100, 2),
                })
        except Exception as e:
            logger.warning(f"Failed to get ROIC for peer {peer}: {e}")
    
    # Calculate peer average
    if peer_roics:
        peer_avg_roic = sum(peer_roics) / len(peer_roics)
    else:
        peer_avg_roic = 0.0
    
    roic_advantage = ticker_avg_roic - peer_avg_roic
    
    return {
        "ticker": ticker.upper(),
        "ticker_avg_roic": round(ticker_avg_roic, 4),
        "ticker_avg_roic_pct": round(ticker_avg_roic * 100, 2),
        "peer_avg_roic": round(peer_avg_roic, 4),
        "peer_avg_roic_pct": round(peer_avg_roic * 100, 2),
        "roic_advantage": round(roic_advantage, 4),
        "roic_advantage_pct": round(roic_advantage * 100, 2),
        "period": ticker_result["period"],
        "years_analyzed": ticker_result["years_analyzed"],
        "peer_data": peer_data,
        "calculated_at": datetime.now().isoformat()
    }


def compare_moat_profiles(
    ticker: str,
    peer_tickers: list[str],
    years: int = 10,
    use_cache: bool = True
) -> dict:
    """
    Multi-dimensional peer comparison using standardized metrics.
    
    Compares across:
    - ROIC spread (ROIC - WACC)
    - Operating margin
    - Revenue growth consistency
    - Economic profit
    - Fade period estimate
    
    This provides a standardized, globally comparable methodology.
    
    Args:
        ticker: Primary ticker to analyze
        peer_tickers: List of peer ticker symbols
        years: Number of years to analyze
        use_cache: Whether to use cached data
        
    Returns:
        Dict with multi-dimensional comparison table
    """
    logger.info(f"Comparing moat profiles: {ticker} vs {peer_tickers}")
    
    all_tickers = [ticker.upper()] + [p.upper() for p in peer_tickers]
    profiles = []
    
    for t in all_tickers:
        profile = _build_company_profile(t, years=years, use_cache=use_cache)
        profiles.append(profile)
    
    if not profiles:
        return {"error": "No data available for comparison."}
    
    # Find the primary ticker's profile
    primary = profiles[0]
    peers = profiles[1:]
    
    # Calculate peer averages for each metric
    peer_metrics = {}
    metric_keys = [
        "avg_roic_pct", "roic_wacc_spread_pct", "avg_op_margin_pct",
        "avg_revenue_growth_pct", "avg_economic_profit", "fade_years"
    ]
    
    for key in metric_keys:
        peer_values = [p.get(key) for p in peers if p.get(key) is not None]
        if peer_values:
            peer_metrics[key] = round(float(np.mean(peer_values)), 2)
        else:
            peer_metrics[key] = None
    
    # Build comparison
    comparison = {
        "ticker": ticker.upper(),
        "period": primary.get("period", "N/A"),
        "primary_profile": primary,
        "peer_profiles": peers,
        "peer_averages": peer_metrics,
        "advantages": {},
        "calculated_at": datetime.now().isoformat(),
    }
    
    # Determine advantages
    for key in metric_keys:
        primary_val = primary.get(key)
        peer_avg = peer_metrics.get(key)
        
        if primary_val is not None and peer_avg is not None and peer_avg != 0:
            diff = primary_val - peer_avg
            comparison["advantages"][key] = {
                "primary": primary_val,
                "peer_avg": peer_avg,
                "difference": round(diff, 2),
                "advantage": diff > 0,
            }
    
    return comparison


def _build_company_profile(
    ticker: str,
    years: int = 10,
    use_cache: bool = True
) -> dict:
    """Build a standardized financial profile for a single company."""
    profile = {"ticker": ticker.upper()}
    
    try:
        # Get ROIC hurdle data (includes economic profit and fade)
        hurdle = check_roic_hurdle(ticker, years=years, use_cache=use_cache)
        
        if "error" in hurdle:
            profile["error"] = hurdle["error"]
            return profile
        
        profile["period"] = hurdle.get("period")
        profile["avg_roic_pct"] = hurdle.get("avg_roic_pct")
        profile["roic_wacc_spread_pct"] = hurdle.get("avg_roic_wacc_spread_pct")
        profile["hurdle_passed"] = hurdle.get("hurdle_passed")
        profile["roic_trend"] = hurdle.get("roic_trend")
        profile["avg_economic_profit"] = hurdle.get("avg_economic_profit")
        
        # Fade period
        fade = hurdle.get("fade_period", {})
        profile["fade_years"] = fade.get("estimated_fade_years")
        profile["fade_durability"] = fade.get("durability")
        
        # Get financial data for margin analysis
        fundamental_data = get_fundamental_data(ticker, use_cache=use_cache)
        df = extract_annual_financials(fundamental_data)
        
        if not df.empty and len(df) >= 3:
            df = df.sort_values("year", ascending=True)
            
            # Operating margin
            revenues = df["revenue"].values
            op_incomes = df["operating_income"].values
            valid_mask = revenues > 0
            
            if valid_mask.sum() >= 2:
                op_margins = op_incomes[valid_mask] / revenues[valid_mask]
                profile["avg_op_margin_pct"] = round(float(np.mean(op_margins)) * 100, 2)
            
            # Revenue growth
            if len(revenues) >= 3:
                rev_growth = np.diff(revenues) / (np.abs(revenues[:-1]) + 1e-9)
                profile["avg_revenue_growth_pct"] = round(float(np.mean(rev_growth)) * 100, 2)
                profile["revenue_growth_consistency"] = round(
                    float((rev_growth > 0).sum() / len(rev_growth)) * 100, 1
                )
        
    except Exception as e:
        logger.warning(f"Error building profile for {ticker}: {e}")
        profile["error"] = str(e)
    
    return profile
