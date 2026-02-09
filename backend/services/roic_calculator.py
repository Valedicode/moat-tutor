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
    
    return df


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
    
    # Build annual data list
    annual_data = []
    for _, row in df.iterrows():
        annual_data.append({
            "year": int(row["year"]),
            "roic": round(float(row["roic"]), 4),
            "roic_pct": round(float(row["roic_pct"]), 2),
            "above_wacc": bool(row["roic"] > wacc),
            "nopat": round(float(row["nopat"]), 0),
            "invested_capital": round(float(row["invested_capital"]), 0),
        })
    
    # Determine if hurdle passed
    # Criteria: Average ROIC > WACC AND at least 70% of years above WACC
    hurdle_passed = (avg_roic > wacc) and (years_above_hurdle_pct >= 70)
    
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
