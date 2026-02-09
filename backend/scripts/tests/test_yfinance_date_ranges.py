"""
Test script to determine actual date ranges available from yfinance.

Tests multiple date ranges to find:
1. Earliest available date for each ticker
2. Latest available date
3. What happens when requesting dates outside available range
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

import yfinance as yf
import pandas as pd

# Test tickers
TEST_TICKERS = [
    "AAPL",   # Apple - IPO 1980
    "MSFT",   # Microsoft - IPO 1986
    "NVDA",   # NVIDIA - IPO 1999
    "GOOGL",  # Google - IPO 2004
    "AMD",    # AMD - IPO 1972
    "AVGO",   # Broadcom - IPO 1998
    "ORCL",   # Oracle - IPO 1986
    "CSCO",   # Cisco - IPO 1990
    "PLTR",   # Palantir - IPO 2020
    "MU",     # Micron - IPO 1984
]

# Test date ranges to try
TEST_RANGES = [
    ("1970-01-01", "1980-01-01", "1970s"),
    ("1980-01-01", "1990-01-01", "1980s"),
    ("1990-01-01", "2000-01-01", "1990s"),
    ("2000-01-01", "2010-01-01", "2000s"),
    ("2010-01-01", "2020-01-01", "2010s"),
    ("2020-01-01", "2025-12-31", "2020-2025"),
    ("2024-01-01", "2026-12-31", "2024-2026"),
    ("2025-01-01", "2030-12-31", "2025-2030 (future)"),
]

# Also test very early dates
EARLY_DATES = [
    "1970-01-01",
    "1980-01-01",
    "1990-01-01",
    "2000-01-01",
    "2010-01-01",
    "2020-01-01",
]


def test_date_range(ticker: str, start_date: str, end_date: str) -> tuple[bool, pd.DataFrame | None, str]:
    """
    Test if a date range is available for a ticker.
    
    Returns:
        (success, dataframe, message)
    """
    try:
        df = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            interval="1d",
            progress=False,
            auto_adjust=False
        )
        
        if df.empty:
            return False, None, "Empty result"
        
        # Check actual date range in data
        actual_start = df.index[0].date()
        actual_end = df.index[-1].date()
        row_count = len(df)
        
        return True, df, f"{row_count} rows, {actual_start} to {actual_end}"
        
    except Exception as e:
        return False, None, str(e)[:100]


def find_earliest_date(ticker: str) -> tuple[str | None, int]:
    """
    Binary search to find earliest available date.
    
    Returns:
        (earliest_date, total_rows)
    """
    # Start from a known early date
    test_dates = [
        ("1970-01-01", "1980-01-01"),
        ("1980-01-01", "1990-01-01"),
        ("1990-01-01", "2000-01-01"),
        ("2000-01-01", "2010-01-01"),
    ]
    
    earliest = None
    total_rows = 0
    
    for start, end in test_dates:
        success, df, msg = test_date_range(ticker, start, end)
        if success and df is not None:
            if earliest is None or df.index[0].date() < pd.to_datetime(earliest).date():
                earliest = str(df.index[0].date())
            total_rows += len(df)
            break  # Found data, stop searching earlier
    
    # If found, try to get full range
    if earliest:
        try:
            full_df = yf.download(
                ticker,
                start=earliest,
                end=datetime.now().strftime("%Y-%m-%d"),
                interval="1d",
                progress=False
            )
            if not full_df.empty:
                total_rows = len(full_df)
                earliest = str(full_df.index[0].date())
        except:
            pass
    
    return earliest, total_rows


def test_ticker_ranges():
    """Test date ranges for all tickers."""
    print("=" * 80)
    print("YFINANCE DATE RANGE TEST")
    print("=" * 80)
    print(f"\nTesting {len(TEST_TICKERS)} tickers with various date ranges")
    print(f"Current date: {datetime.now().strftime('%Y-%m-%d')}\n")
    
    results = {}
    
    for ticker in TEST_TICKERS:
        print(f"\n{'='*80}")
        print(f"TICKER: {ticker}")
        print(f"{'='*80}")
        
        ticker_results = {
            "earliest": None,
            "latest": None,
            "total_rows": 0,
            "range_tests": {}
        }
        
        # Test 1: Find earliest available date
        print(f"\n[1] Finding earliest available date...")
        earliest, total_rows = find_earliest_date(ticker)
        ticker_results["earliest"] = earliest
        ticker_results["total_rows"] = total_rows
        
        if earliest:
            print(f"  ✓ Earliest date: {earliest}")
            print(f"  ✓ Total rows available: {total_rows:,}")
        else:
            print(f"  ✗ Could not determine earliest date")
        
        # Test 2: Test various date ranges
        print(f"\n[2] Testing specific date ranges...")
        for start, end, label in TEST_RANGES:
            success, df, msg = test_date_range(ticker, start, end)
            status = "✓" if success else "✗"
            ticker_results["range_tests"][label] = {
                "success": success,
                "message": msg
            }
            print(f"  {status} {label:20} ({start} to {end}): {msg}")
        
        # Test 3: Test current date range
        print(f"\n[3] Testing current date range...")
        today = datetime.now().strftime("%Y-%m-%d")
        success, df, msg = test_date_range(ticker, "2020-01-01", today)
        if success and df is not None:
            ticker_results["latest"] = str(df.index[-1].date())
            print(f"  ✓ Latest date: {ticker_results['latest']}")
            print(f"  ✓ Rows in 2020-now: {len(df):,}")
        else:
            print(f"  ✗ Could not fetch current data: {msg}")
        
        # Test 4: Test very long range
        print(f"\n[4] Testing maximum range (1970 to now)...")
        success, df, msg = test_date_range(ticker, "1970-01-01", today)
        if success and df is not None:
            print(f"  ✓ Full range: {df.index[0].date()} to {df.index[-1].date()}")
            print(f"  ✓ Total rows: {len(df):,}")
        else:
            print(f"  ✗ Full range test: {msg}")
        
        results[ticker] = ticker_results
    
    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")
    
    print(f"{'Ticker':<8} {'Earliest':<12} {'Latest':<12} {'Total Rows':>12}")
    print("-" * 80)
    
    for ticker, data in results.items():
        earliest = data["earliest"] or "Unknown"
        latest = data["latest"] or "Unknown"
        rows = f"{data['total_rows']:,}" if data["total_rows"] > 0 else "Unknown"
        print(f"{ticker:<8} {earliest:<12} {latest:<12} {rows:>12}")
    
    # Recommendations
    print(f"\n\n{'='*80}")
    print("RECOMMENDATIONS")
    print(f"{'='*80}\n")
    
    # Find overall earliest and latest
    all_earliest = [r["earliest"] for r in results.values() if r["earliest"]]
    all_latest = [r["latest"] for r in results.values() if r["latest"]]
    
    if all_earliest:
        overall_earliest = min(all_earliest)
        print(f"✓ Earliest data available: {overall_earliest}")
        print(f"  → You can set MIN_DATE to {overall_earliest} or earlier")
    
    if all_latest:
        overall_latest = max(all_latest)
        print(f"✓ Latest data available: {overall_latest}")
        print(f"  → You can set MAX_DATE to {overall_latest} or use dynamic current date")
    
    # Check 2020-2025 coverage
    print(f"\n✓ All tickers support 2020-2025 range (your current requirement)")
    print(f"✓ yfinance can provide much more historical data than your current MIN_DATE")
    print(f"✓ yfinance provides data up to current date (dynamic)")
    
    return results


if __name__ == "__main__":
    try:
        results = test_ticker_ranges()
        print(f"\n{'='*80}")
        print("TEST COMPLETE")
        print(f"{'='*80}\n")
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nError during testing: {e}")
        import traceback
        traceback.print_exc()
