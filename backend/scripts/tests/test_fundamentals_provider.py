"""
Test script for Alpha Vantage fundamentals provider

Run this to verify the API connection and understand the response structure.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from services.fundamentals_provider import (
    fetch_income_statement,
    fetch_balance_sheet,
    fetch_cash_flow,
    get_fundamental_data,
)


def test_income_statement():
    """Test fetching income statement."""
    print("\n" + "="*60)
    print("TEST: Fetching Income Statement for AAPL")
    print("="*60)
    
    try:
        data = fetch_income_statement("AAPL", use_cache=False)
        print(f"\nSuccess! Response keys: {list(data.keys())}")
        
        if "annualReports" in data and len(data["annualReports"]) > 0:
            latest = data["annualReports"][0]
            print(f"\nLatest annual report:")
            print(f"  Fiscal Date: {latest.get('fiscalDateEnding', 'N/A')}")
            print(f"  Revenue: ${float(latest.get('totalRevenue', 0)):,.0f}")
            print(f"  Operating Income: ${float(latest.get('operatingIncome', 0)):,.0f}")
            print(f"  Net Income: ${float(latest.get('netIncome', 0)):,.0f}")
        
        return True
    except Exception as e:
        print(f"\nError: {e}")
        return False


def test_balance_sheet():
    """Test fetching balance sheet."""
    print("\n" + "="*60)
    print("TEST: Fetching Balance Sheet for AAPL")
    print("="*60)
    
    try:
        data = fetch_balance_sheet("AAPL", use_cache=False)
        print(f"\nSuccess! Response keys: {list(data.keys())}")
        
        if "annualReports" in data and len(data["annualReports"]) > 0:
            latest = data["annualReports"][0]
            print(f"\nLatest annual report:")
            print(f"  Fiscal Date: {latest.get('fiscalDateEnding', 'N/A')}")
            print(f"  Total Assets: ${float(latest.get('totalAssets', 0)):,.0f}")
            print(f"  Total Equity: ${float(latest.get('totalShareholderEquity', 0)):,.0f}")
            print(f"  Cash: ${float(latest.get('cashAndCashEquivalentsAtCarryingValue', 0)):,.0f}")
        
        return True
    except Exception as e:
        print(f"\nError: {e}")
        return False


def test_nvda():
    """Test with NVDA (known high-ROIC company)."""
    print("\n" + "="*60)
    print("TEST: Fetching Income Statement for NVDA")
    print("="*60)
    
    try:
        data = fetch_income_statement("NVDA", use_cache=False)
        
        if "annualReports" in data and len(data["annualReports"]) > 0:
            latest = data["annualReports"][0]
            print(f"\nSuccess! Latest NVDA report:")
            print(f"  Fiscal Date: {latest.get('fiscalDateEnding', 'N/A')}")
            print(f"  Revenue: ${float(latest.get('totalRevenue', 0))/1e9:.2f}B")
            print(f"  Operating Income: ${float(latest.get('operatingIncome', 0))/1e9:.2f}B")
            print(f"  Net Income: ${float(latest.get('netIncome', 0))/1e9:.2f}B")
            
            # Show available fields
            print(f"\nAvailable fields in response:")
            for key in list(latest.keys())[:15]:
                print(f"  - {key}")
            if len(latest.keys()) > 15:
                print(f"  ... and {len(latest.keys()) - 15} more fields")
        
        return True
    except Exception as e:
        print(f"\nError: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Alpha Vantage Fundamentals Provider Test Suite")
    print("="*60)
    
    results = []
    
    # Test 1: Income Statement (AAPL)
    results.append(("Income Statement (AAPL)", test_income_statement()))
    
    # Test 2: Balance Sheet (AAPL)
    results.append(("Balance Sheet (AAPL)", test_balance_sheet()))
    
    # Test 3: Different ticker (NVDA)
    results.append(("Income Statement (NVDA)", test_nvda()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("\nAll tests passed! Ready to implement ROIC calculator.")
    else:
        print("\nSome tests failed. Check API key and rate limits.")
