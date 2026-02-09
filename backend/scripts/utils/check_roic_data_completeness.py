"""
Check if all tickers have the minimum required data for ROIC calculation.

ROIC requires:
- Income Statement: Operating Income, Income Tax Expense, Income Before Tax
- Balance Sheet: Total Equity, Total Debt, Cash and Cash Equivalents

Cash Flow statement is optional (not strictly required for ROIC).
"""

from pathlib import Path
import json
from dotenv import load_dotenv

load_dotenv()

from services.fundamentals_provider import FUNDAMENTALS_CACHE_DIR

# All supported tickers
ALL_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "NVDA", "AMD", "AVGO", "ORCL", "CSCO", "MU", "PLTR"
]

# Required fields for ROIC calculation
REQUIRED_INCOME_FIELDS = [
    "operatingIncome",  # Operating Income (EBIT)
    "incomeBeforeTax",  # Income Before Tax (for tax rate calculation)
    "incomeTaxExpense",  # Income Tax Expense (for tax rate calculation)
]

REQUIRED_BALANCE_FIELDS = [
    "totalShareholderEquity",  # Total Equity
    # Total Debt can be calculated from shortTermDebt + longTermDebt
    # So we check for either totalDebt OR (shortTermDebt AND longTermDebt)
    "cashAndCashEquivalentsAtCarryingValue",  # Cash
]

# Alternative debt fields (if totalDebt not available)
ALTERNATIVE_DEBT_FIELDS = [
    "shortTermDebt",  # Short-term debt
    "longTermDebt",  # Long-term debt
]


def check_statement_completeness(ticker: str, statement_type: str) -> dict:
    """
    Check if a financial statement has the required fields for ROIC.
    
    Returns:
        Dict with {"complete": bool, "missing_fields": list, "has_data": bool}
    """
    ticker_dir = FUNDAMENTALS_CACHE_DIR / ticker.upper()
    cache_path = ticker_dir / f"{statement_type}.json"
    
    if not cache_path.exists():
        return {
            "complete": False,
            "missing_fields": [],
            "has_data": False,
            "error": "File not found"
        }
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Alpha Vantage structure: data['annualReports'] or data['quarterlyReports']
        annual_reports = data.get('annualReports', [])
        
        if not annual_reports:
            return {
                "complete": False,
                "missing_fields": [],
                "has_data": False,
                "error": "No annual reports found"
            }
        
        # Check the most recent report (index 0)
        latest_report = annual_reports[0]
        
        if statement_type == "income-statement":
            required_fields = REQUIRED_INCOME_FIELDS
            missing_fields = []
            for field in required_fields:
                # Check if field exists and has a non-null value
                value = latest_report.get(field)
                if value is None or value == "None" or value == "":
                    missing_fields.append(field)
        elif statement_type == "balance-sheet":
            required_fields = REQUIRED_BALANCE_FIELDS
            # Special handling for debt: check totalDebt OR (shortTermDebt AND longTermDebt)
            missing_fields = []
            for field in required_fields:
                value = latest_report.get(field)
                if value is None or value == "None" or value == "":
                    missing_fields.append(field)
            
            # Check debt fields: need totalDebt OR shortLongTermDebtTotal OR (shortTermDebt AND longTermDebt)
            total_debt = latest_report.get("totalDebt")
            short_long_total = latest_report.get("shortLongTermDebtTotal")  # Alternative field name
            short_debt = latest_report.get("shortTermDebt")
            long_debt = latest_report.get("longTermDebt")
            
            has_debt = (
                (total_debt is not None and total_debt != "None" and total_debt != "") or
                (short_long_total is not None and short_long_total != "None" and short_long_total != "") or
                ((short_debt is not None and short_debt != "None" and short_debt != "") and
                 (long_debt is not None and long_debt != "None" and long_debt != ""))
            )
            
            if not has_debt:
                missing_fields.append("totalDebt (or shortTermDebt+longTermDebt)")
        else:
            # Cash flow or other statement types - not required for ROIC
            missing_fields = []
        
        return {
            "complete": len(missing_fields) == 0,
            "missing_fields": missing_fields,
            "has_data": True,
            "years_available": len(annual_reports)
        }
        
    except Exception as e:
        return {
            "complete": False,
            "missing_fields": [],
            "has_data": False,
            "error": str(e)
        }


def check_ticker_roic_readiness(ticker: str) -> dict:
    """
    Check if a ticker has all data needed for ROIC calculation.
    
    Returns:
        Dict with completeness status for income statement, balance sheet, and overall readiness
    """
    income_status = check_statement_completeness(ticker, "income-statement")
    balance_status = check_statement_completeness(ticker, "balance-sheet")
    cashflow_status = check_statement_completeness(ticker, "cash-flow")
    
    # ROIC can be calculated if income statement AND balance sheet are complete
    roic_ready = income_status["complete"] and balance_status["complete"]
    
    return {
        "ticker": ticker,
        "roic_ready": roic_ready,
        "income_statement": income_status,
        "balance_sheet": balance_status,
        "cash_flow": cashflow_status,  # Optional but nice to have
    }


def main():
    """Check ROIC data completeness for all tickers."""
    print("=" * 80)
    print("ROIC Data Completeness Check")
    print("=" * 80)
    print()
    print("Required for ROIC calculation:")
    print("  [REQ] Income Statement: Operating Income, Income Before Tax, Income Tax Expense")
    print("  [REQ] Balance Sheet: Total Equity, Total Debt, Cash")
    print("  [OPT] Cash Flow: Optional (not required)")
    print()
    print("=" * 80)
    print()
    
    results = []
    ready_count = 0
    missing_count = 0
    
    for ticker in ALL_TICKERS:
        result = check_ticker_roic_readiness(ticker)
        results.append(result)
        
        if result["roic_ready"]:
            ready_count += 1
        else:
            missing_count += 1
    
    # Print detailed results
    for result in results:
        ticker = result["ticker"]
        status_icon = "[OK]" if result["roic_ready"] else "[MISSING]"
        
        print(f"{status_icon} {ticker}:")
        
        # Income Statement
        inc = result["income_statement"]
        if inc["has_data"]:
            if inc["complete"]:
                print(f"    Income Statement: [OK] Complete ({inc['years_available']} years)")
            else:
                print(f"    Income Statement: [MISSING] Missing fields: {', '.join(inc['missing_fields'])}")
        else:
            print(f"    Income Statement: [MISSING] {inc.get('error', 'Not found')}")
        
        # Balance Sheet
        bal = result["balance_sheet"]
        if bal["has_data"]:
            if bal["complete"]:
                print(f"    Balance Sheet: [OK] Complete ({bal['years_available']} years)")
            else:
                print(f"    Balance Sheet: [MISSING] Missing fields: {', '.join(bal['missing_fields'])}")
        else:
            print(f"    Balance Sheet: [MISSING] {bal.get('error', 'Not found')}")
        
        # Cash Flow (optional)
        cf = result["cash_flow"]
        if cf["has_data"]:
            years = cf.get('years_available', 'unknown')
            print(f"    Cash Flow: [OPT] Available ({years} years)")
        else:
            print(f"    Cash Flow: [OPT] {cf.get('error', 'Not found')} (optional)")
        
        print()
    
    # Summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"ROIC-Ready Tickers: {ready_count}/{len(ALL_TICKERS)}")
    print(f"Missing Data: {missing_count}/{len(ALL_TICKERS)}")
    print()
    
    if missing_count > 0:
        print("Tickers needing data:")
        for result in results:
            if not result["roic_ready"]:
                ticker = result["ticker"]
                missing_items = []
                
                if not result["income_statement"]["complete"]:
                    missing_items.append("Income Statement")
                if not result["balance_sheet"]["complete"]:
                    missing_items.append("Balance Sheet")
                
                print(f"  - {ticker}: {', '.join(missing_items)}")
    else:
        print("[OK] All tickers have complete data for ROIC calculation!")


if __name__ == "__main__":
    main()
