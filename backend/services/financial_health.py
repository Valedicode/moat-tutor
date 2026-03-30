"""
Financial Health Assessment

Evaluates whether financial distress could destroy cumulative economic profit.
Acts as a potential No-Moat override: a company with severe financial health
risk is rated No Moat regardless of structural competitive advantages.

Components:
1. Leverage - debt levels relative to earnings and equity
2. Liquidity - ability to meet short-term obligations
3. Cash Flow Sufficiency - ability to service and repay debt from operations
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


def assess_financial_health(ticker: str, use_cache: bool = True) -> dict:
    """
    Assess financial health risk and determine if a No-Moat override is warranted.

    Returns status of Healthy / Watch / Distressed / Critical with a
    moat_override_flag that forces No Moat when True.
    """
    ticker = ticker.upper()
    logger.info(f"Assessing financial health for {ticker}")

    try:
        fundamental_data = get_fundamental_data(ticker, use_cache=use_cache)
        df = extract_annual_financials(fundamental_data)

        if df.empty or len(df) < 3:
            return _default_result(ticker, "Insufficient financial data")

        df = df.sort_values("year", ascending=False)

        cash_flow = fundamental_data.get("cash_flow", {})
        annual_cf = cash_flow.get("annualReports", [])

        lev = _score_leverage(df)
        liq = _score_liquidity(df, fundamental_data)
        cfs = _score_cash_flow_sufficiency(df, annual_cf)

        component_scores = [lev["score"], liq["score"], cfs["score"]]
        avg_score = float(np.mean(component_scores))

        if avg_score >= 3.5:
            status = "Healthy"
        elif avg_score >= 2.5:
            status = "Watch"
        elif avg_score >= 1.5:
            status = "Distressed"
        else:
            status = "Critical"

        value_destruction_risk = max(0.0, min(1.0, (4.0 - avg_score) / 4.0))

        override_flag = False
        if status == "Critical":
            try:
                roic_result = check_roic_hurdle(ticker, years=10, use_cache=use_cache)
                cum_ep = roic_result.get("cumulative_economic_profit", 0)
                if cum_ep <= 0 or value_destruction_risk > 0.8:
                    override_flag = True
            except Exception:
                override_flag = True

        explanation = (
            f"Financial Health: {status} (avg score {avg_score:.1f}/4.0, "
            f"value destruction risk {value_destruction_risk:.0%}). "
            f"Leverage: {lev['rationale']}. "
            f"Liquidity: {liq['rationale']}. "
            f"Cash Flow: {cfs['rationale']}."
        )
        if override_flag:
            explanation += (
                " OVERRIDE: Financial distress risk is severe enough to warrant "
                "a No-Moat rating regardless of competitive advantages."
            )

        return {
            "ticker": ticker,
            "financial_health_status": status,
            "value_destruction_risk": round(value_destruction_risk, 3),
            "moat_override_flag": override_flag,
            "components": {
                "leverage": lev,
                "liquidity": liq,
                "cash_flow_sufficiency": cfs,
            },
            "explanation": explanation,
            "calculated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error assessing financial health for {ticker}: {e}")
        return _default_result(ticker, str(e))


def _score_leverage(df) -> dict:
    """Score 0-4: debt levels relative to earnings and equity."""
    score = 2.0
    rationale_parts = []

    latest = df.iloc[0]
    equity = float(latest.get("equity", 0))
    total_debt = float(latest.get("total_debt", 0))
    operating_income = float(latest.get("operating_income", 0))

    if equity > 0:
        de_ratio = total_debt / equity
        if de_ratio < 0.2:
            score += 1.0
            rationale_parts.append(f"very low leverage (D/E {de_ratio:.2f})")
        elif de_ratio < 0.5:
            score += 0.5
            rationale_parts.append(f"low leverage (D/E {de_ratio:.2f})")
        elif de_ratio > 2.0:
            score -= 1.0
            rationale_parts.append(f"high leverage (D/E {de_ratio:.2f})")
        elif de_ratio > 1.0:
            score -= 0.5
            rationale_parts.append(f"elevated leverage (D/E {de_ratio:.2f})")
        else:
            rationale_parts.append(f"moderate leverage (D/E {de_ratio:.2f})")
    else:
        score -= 1.5
        rationale_parts.append("negative equity - severe concern")

    interest_expense = abs(float(latest.get("interest_expense", 0))) if "interest_expense" in latest.index else 0.0
    if interest_expense > 0 and operating_income > 0:
        coverage = operating_income / interest_expense
        if coverage > 10:
            score += 0.5
            rationale_parts.append(f"excellent interest coverage ({coverage:.1f}x)")
        elif coverage > 5:
            score += 0.3
            rationale_parts.append(f"strong interest coverage ({coverage:.1f}x)")
        elif coverage < 1.5:
            score -= 1.0
            rationale_parts.append(f"dangerously low interest coverage ({coverage:.1f}x)")
        elif coverage < 3:
            score -= 0.5
            rationale_parts.append(f"tight interest coverage ({coverage:.1f}x)")

    if operating_income > 0 and total_debt > 0:
        debt_to_ebit = total_debt / operating_income
        if debt_to_ebit > 6:
            score -= 0.5
            rationale_parts.append(f"Debt/EBIT ratio very high ({debt_to_ebit:.1f}x)")
        elif debt_to_ebit < 2:
            score += 0.5
            rationale_parts.append(f"Debt/EBIT ratio comfortable ({debt_to_ebit:.1f}x)")

    score = max(0.0, min(4.0, score))
    rationale = "; ".join(rationale_parts) if rationale_parts else "standard leverage"

    return {"score": round(score, 2), "rationale": rationale}


def _score_liquidity(df, fundamental_data: dict) -> dict:
    """Score 0-4: ability to meet short-term obligations."""
    score = 2.0
    rationale_parts = []

    latest = df.iloc[0]
    cash = float(latest.get("cash", 0))
    current_liabilities = float(latest.get("current_liabilities", 0)) if "current_liabilities" in latest.index else 0.0

    balance_sheet = fundamental_data.get("balance_sheet", {})
    annual_bs = balance_sheet.get("annualReports", [])
    current_assets = 0.0
    if annual_bs:
        most_recent = annual_bs[0]
        current_assets = _safe_float(most_recent.get("totalCurrentAssets", 0))

    if current_liabilities > 0:
        if current_assets > 0:
            current_ratio = current_assets / current_liabilities
            if current_ratio > 2.0:
                score += 1.0
                rationale_parts.append(f"strong current ratio ({current_ratio:.2f})")
            elif current_ratio > 1.2:
                score += 0.5
                rationale_parts.append(f"adequate current ratio ({current_ratio:.2f})")
            elif current_ratio < 0.8:
                score -= 1.0
                rationale_parts.append(f"weak current ratio ({current_ratio:.2f})")
            elif current_ratio < 1.0:
                score -= 0.5
                rationale_parts.append(f"tight current ratio ({current_ratio:.2f})")
        else:
            cash_ratio = cash / current_liabilities if current_liabilities > 0 else 0
            if cash_ratio > 0.5:
                score += 0.3
                rationale_parts.append(f"cash covers {cash_ratio:.0%} of current liabilities")
            elif cash_ratio < 0.2:
                score -= 0.5
                rationale_parts.append(f"low cash coverage ({cash_ratio:.0%} of current liabilities)")
    else:
        rationale_parts.append("current liabilities data unavailable")

    total_debt = float(latest.get("total_debt", 0))
    total_assets = float(latest.get("total_assets", 0)) if "total_assets" in latest.index else 0.0
    if total_assets > 0:
        cash_to_assets = cash / total_assets
        if cash_to_assets > 0.15:
            score += 0.5
            rationale_parts.append(f"strong cash position ({cash_to_assets:.0%} of assets)")
        elif cash_to_assets < 0.03:
            score -= 0.5
            rationale_parts.append(f"minimal cash reserves ({cash_to_assets:.0%} of assets)")

    score = max(0.0, min(4.0, score))
    rationale = "; ".join(rationale_parts) if rationale_parts else "standard liquidity"

    return {"score": round(score, 2), "rationale": rationale}


def _score_cash_flow_sufficiency(df, annual_cf: list) -> dict:
    """Score 0-4: ability to service debt from operating cash flows."""
    score = 2.0
    rationale_parts = []

    fcf_values = []
    for report in annual_cf:
        ocf = _safe_float(report.get("operatingCashflow", 0))
        capex = abs(_safe_float(report.get("capitalExpenditures", 0)))
        fcf = ocf - capex
        fcf_values.append(fcf)

    if len(fcf_values) >= 3:
        avg_fcf = float(np.mean(fcf_values[:5]))
        positive_years = sum(1 for f in fcf_values[:5] if f > 0)
        total_years = min(5, len(fcf_values))

        if positive_years == total_years:
            score += 0.5
            rationale_parts.append(f"FCF positive all {total_years} years")
        elif positive_years >= total_years * 0.6:
            rationale_parts.append(f"FCF positive {positive_years}/{total_years} years")
        else:
            score -= 0.5
            rationale_parts.append(f"FCF positive only {positive_years}/{total_years} years")

        latest = df.iloc[0]
        total_debt = float(latest.get("total_debt", 0))

        if total_debt > 0 and avg_fcf > 0:
            years_to_repay = total_debt / avg_fcf
            if years_to_repay < 3:
                score += 1.0
                rationale_parts.append(f"can repay all debt in {years_to_repay:.1f} years from FCF")
            elif years_to_repay < 5:
                score += 0.5
                rationale_parts.append(f"debt repayable in {years_to_repay:.1f} years from FCF")
            elif years_to_repay > 10:
                score -= 1.0
                rationale_parts.append(f"would take {years_to_repay:.1f} years to repay debt from FCF")
            elif years_to_repay > 7:
                score -= 0.5
                rationale_parts.append(f"debt repayment from FCF would take {years_to_repay:.1f} years")
        elif total_debt > 0 and avg_fcf <= 0:
            score -= 1.0
            rationale_parts.append("negative average FCF cannot service debt")
        elif total_debt == 0:
            score += 0.5
            rationale_parts.append("no debt to service")
    else:
        rationale_parts.append("insufficient cash flow history")

    score = max(0.0, min(4.0, score))
    rationale = "; ".join(rationale_parts) if rationale_parts else "standard cash flow"

    return {"score": round(score, 2), "rationale": rationale}


def _default_result(ticker: str, reason: str) -> dict:
    return {
        "ticker": ticker.upper(),
        "financial_health_status": "Watch",
        "value_destruction_risk": 0.25,
        "moat_override_flag": False,
        "components": {
            "leverage": {"score": 2.0, "rationale": reason},
            "liquidity": {"score": 2.0, "rationale": reason},
            "cash_flow_sufficiency": {"score": 2.0, "rationale": reason},
        },
        "explanation": f"Default Watch status due to: {reason}",
        "calculated_at": datetime.now().isoformat(),
    }
