"""
Capital Allocation Assessment

Evaluates management's capital allocation decisions across three pillars:
1. Balance Sheet Management - leverage discipline and debt serviceability
2. Investment Strategy - whether reinvestment earns returns above cost of capital
3. Shareholder Distributions - appropriateness of dividends and buybacks

Ratings: Exemplary / Standard / Poor
"""

from __future__ import annotations

import logging
from datetime import datetime
import numpy as np

from services.fundamentals_provider import get_fundamental_data
from services.roic_calculator import (
    extract_annual_financials,
    check_roic_hurdle,
    _safe_float,
)

logger = logging.getLogger(__name__)


def assess_capital_allocation(ticker: str, use_cache: bool = True) -> dict:
    """
    Assess capital allocation quality for a company.

    Returns a rating of Exemplary / Standard / Poor based on three pillars
    each scored 0-2 (total 0-6).
    """
    ticker = ticker.upper()
    logger.info(f"Assessing capital allocation for {ticker}")

    try:
        fundamental_data = get_fundamental_data(ticker, use_cache=use_cache)
        df = extract_annual_financials(fundamental_data)

        if df.empty or len(df) < 3:
            return _default_result(ticker, "Insufficient financial data")

        df = df.sort_values("year", ascending=True)

        cash_flow = fundamental_data.get("cash_flow", {})
        annual_cf = cash_flow.get("annualReports", [])

        bsm = _score_balance_sheet_management(df)
        inv = _score_investment_strategy(ticker, df, use_cache)
        dist = _score_shareholder_distributions(df, annual_cf)

        overall_score = bsm["score"] + inv["score"] + dist["score"]

        if overall_score >= 4.5:
            rating = "Exemplary"
        elif overall_score >= 2.5:
            rating = "Standard"
        else:
            rating = "Poor"

        explanation = (
            f"Capital Allocation Rating: {rating} (score {overall_score:.1f}/6.0). "
            f"Balance Sheet: {bsm['score']:.1f}/2 - {bsm['rationale']}. "
            f"Investment Strategy: {inv['score']:.1f}/2 - {inv['rationale']}. "
            f"Shareholder Distributions: {dist['score']:.1f}/2 - {dist['rationale']}."
        )

        return {
            "ticker": ticker,
            "capital_allocation_rating": rating,
            "pillar_scores": {
                "balance_sheet_management": bsm,
                "investment_strategy": inv,
                "shareholder_distributions": dist,
            },
            "overall_score": round(overall_score, 2),
            "explanation": explanation,
            "calculated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error assessing capital allocation for {ticker}: {e}")
        return _default_result(ticker, str(e))


def _score_balance_sheet_management(df) -> dict:
    """Score 0-2: leverage discipline, interest coverage, debt trajectory."""
    score = 1.0
    rationale_parts = []

    latest = df.iloc[-1]
    equity = float(latest.get("equity", 0))
    total_debt = float(latest.get("total_debt", 0))
    operating_income = float(latest.get("operating_income", 0))

    if equity > 0:
        de_ratio = total_debt / equity
        if de_ratio < 0.3:
            score += 0.4
            rationale_parts.append(f"low leverage (D/E {de_ratio:.2f})")
        elif de_ratio < 0.8:
            score += 0.2
            rationale_parts.append(f"moderate leverage (D/E {de_ratio:.2f})")
        elif de_ratio > 2.0:
            score -= 0.5
            rationale_parts.append(f"high leverage (D/E {de_ratio:.2f})")
    else:
        score -= 0.5
        rationale_parts.append("negative equity")

    interest_expense = abs(float(latest.get("interest_expense", 0))) if "interest_expense" in latest.index else 0.0
    if interest_expense > 0 and operating_income > 0:
        coverage = operating_income / interest_expense
        if coverage > 10:
            score += 0.4
            rationale_parts.append(f"strong interest coverage ({coverage:.1f}x)")
        elif coverage > 4:
            score += 0.2
            rationale_parts.append(f"adequate interest coverage ({coverage:.1f}x)")
        elif coverage < 2:
            score -= 0.3
            rationale_parts.append(f"weak interest coverage ({coverage:.1f}x)")

    if len(df) >= 4:
        debts = df["total_debt"].values
        if len(debts) >= 4:
            recent_debt = np.mean(debts[-2:])
            older_debt = np.mean(debts[:2])
            if older_debt > 0 and recent_debt < older_debt * 0.8:
                score += 0.2
                rationale_parts.append("debt declining over time")
            elif older_debt > 0 and recent_debt > older_debt * 1.5:
                score -= 0.2
                rationale_parts.append("debt increasing substantially")

    score = max(0.0, min(2.0, score))
    rationale = "; ".join(rationale_parts) if rationale_parts else "standard leverage position"

    return {"score": round(score, 2), "rationale": rationale}


def _score_investment_strategy(ticker: str, df, use_cache: bool) -> dict:
    """Score 0-2: reinvestment effectiveness measured by ROIC vs WACC."""
    score = 1.0
    rationale_parts = []

    try:
        roic_result = check_roic_hurdle(ticker, years=10, use_cache=use_cache)
        if "error" not in roic_result:
            if roic_result.get("hurdle_passed"):
                avg_roic = roic_result.get("avg_roic_pct", 0)
                if avg_roic > 25:
                    score += 0.8
                    rationale_parts.append(f"reinvestment earns {avg_roic:.1f}% ROIC, well above WACC")
                elif avg_roic > 15:
                    score += 0.5
                    rationale_parts.append(f"reinvestment earns {avg_roic:.1f}% ROIC, above WACC")
                else:
                    score += 0.2
                    rationale_parts.append(f"ROIC ({avg_roic:.1f}%) modestly above WACC")
            else:
                score -= 0.3
                rationale_parts.append("ROIC does not consistently exceed cost of capital")

            trend = roic_result.get("roic_trend", "stable")
            if trend == "strengthening":
                score += 0.2
                rationale_parts.append("ROIC trend improving")
            elif trend == "weakening":
                score -= 0.2
                rationale_parts.append("ROIC trend declining")
    except Exception:
        rationale_parts.append("ROIC data unavailable")

    revenues = df["revenue"].values
    if len(revenues) >= 3:
        rev_growth = np.diff(revenues) / (np.abs(revenues[:-1]) + 1e-9)
        avg_growth = float(np.mean(rev_growth))
        if avg_growth > 0.10:
            score += 0.2
            rationale_parts.append(f"strong revenue growth ({avg_growth*100:.1f}%)")
        elif avg_growth < 0:
            score -= 0.2
            rationale_parts.append(f"revenue declining ({avg_growth*100:.1f}%)")

    score = max(0.0, min(2.0, score))
    rationale = "; ".join(rationale_parts) if rationale_parts else "standard investment strategy"

    return {"score": round(score, 2), "rationale": rationale}


def _score_shareholder_distributions(df, annual_cf: list) -> dict:
    """Score 0-2: dividend policy and buyback effectiveness."""
    score = 1.0
    rationale_parts = []

    cf_by_year = {}
    for report in annual_cf:
        fiscal_date = report.get("fiscalDateEnding", "")
        year = fiscal_date[:4] if fiscal_date else None
        if year:
            cf_by_year[year] = {
                "dividends": abs(_safe_float(report.get("dividendPayout", 0))),
                "buybacks": -_safe_float(report.get("issuanceBuybackOfEquityShares",
                                         report.get("issuanceOfStock", 0))),
                "operating_cf": _safe_float(report.get("operatingCashflow", 0)),
            }

    if cf_by_year:
        total_dividends = sum(v["dividends"] for v in cf_by_year.values())
        total_buybacks = sum(max(0, v["buybacks"]) for v in cf_by_year.values())
        total_ocf = sum(v["operating_cf"] for v in cf_by_year.values())

        if total_ocf > 0:
            payout_ratio = (total_dividends + total_buybacks) / total_ocf
            if 0.2 <= payout_ratio <= 0.7:
                score += 0.4
                rationale_parts.append(f"balanced total payout ({payout_ratio*100:.0f}% of OCF)")
            elif payout_ratio > 0.9:
                score -= 0.3
                rationale_parts.append(f"excessive payout ({payout_ratio*100:.0f}% of OCF)")
            elif payout_ratio < 0.1 and total_ocf > 0:
                rationale_parts.append("minimal shareholder returns despite positive cash flow")

        if total_buybacks > 0:
            score += 0.3
            rationale_parts.append("active share repurchase program")

        if total_dividends > 0:
            div_values = [v["dividends"] for v in sorted(cf_by_year.values(), key=lambda x: x.get("operating_cf", 0))]
            if len(div_values) >= 3 and all(d > 0 for d in div_values[-3:]):
                score += 0.3
                rationale_parts.append("consistent dividend payments")
    else:
        rationale_parts.append("no cash flow data for distribution analysis")

    score = max(0.0, min(2.0, score))
    rationale = "; ".join(rationale_parts) if rationale_parts else "standard distribution policy"

    return {"score": round(score, 2), "rationale": rationale}


def _default_result(ticker: str, reason: str) -> dict:
    return {
        "ticker": ticker.upper(),
        "capital_allocation_rating": "Standard",
        "pillar_scores": {
            "balance_sheet_management": {"score": 1.0, "rationale": reason},
            "investment_strategy": {"score": 1.0, "rationale": reason},
            "shareholder_distributions": {"score": 1.0, "rationale": reason},
        },
        "overall_score": 3.0,
        "explanation": f"Default Standard rating due to: {reason}",
        "calculated_at": datetime.now().isoformat(),
    }
