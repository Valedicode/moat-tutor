"""
Fetch remaining fundamental data for all supported tickers.

This script checks which tickers are missing fundamental data and fetches them
with proper rate limiting (1 request per second) to respect Alpha Vantage free tier limits.

Alpha Vantage Free Tier Limits:
- 25 API calls per day
- 5 calls per minute
- 1 call per second (burst limit)
"""

import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from services.fundamentals_provider import (
    fetch_income_statement,
    fetch_balance_sheet,
    fetch_cash_flow,
    FUNDAMENTALS_CACHE_DIR,
)

# All supported tickers (from your FNSPID/news data)
ALL_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "NVDA", "AMD", "AVGO", "ORCL", "CSCO", "MU", "PLTR"
]

# Financial statements to fetch
STATEMENTS = ["income-statement", "balance-sheet", "cash-flow"]


def check_ticker_data(ticker: str) -> dict:
    """
    Check which statements are already cached for a ticker.
    
    Returns:
        Dict with status for each statement: {"income-statement": True/False, ...}
    """
    ticker_dir = FUNDAMENTALS_CACHE_DIR / ticker.upper()
    
    status = {}
    for stmt in STATEMENTS:
        cache_path = ticker_dir / f"{stmt}.json"
        status[stmt] = cache_path.exists()
    
    return status


def get_missing_tickers() -> list[tuple[str, list[str]]]:
    """
    Find tickers missing fundamental data.
    
    Returns:
        List of (ticker, [missing_statements]) tuples
    """
    missing = []
    
    for ticker in ALL_TICKERS:
        status = check_ticker_data(ticker)
        missing_statements = [stmt for stmt, exists in status.items() if not exists]
        
        if missing_statements:
            missing.append((ticker, missing_statements))
    
    return missing


def fetch_ticker_fundamentals(ticker: str, statements: list[str] = None) -> dict:
    """
    Fetch fundamental data for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        statements: List of statements to fetch (default: all)
    
    Returns:
        Dict with fetch results: {"income-statement": "success"/"error", ...}
    """
    if statements is None:
        statements = STATEMENTS
    
    results = {}
    
    for stmt in statements:
        try:
            print(f"  Fetching {stmt} for {ticker}...", end=" ", flush=True)
            
            if stmt == "income-statement":
                fetch_income_statement(ticker, use_cache=False)
            elif stmt == "balance-sheet":
                fetch_balance_sheet(ticker, use_cache=False)
            elif stmt == "cash-flow":
                fetch_cash_flow(ticker, use_cache=False)
            
            results[stmt] = "success"
            print("[OK]")
            
            # Rate limiting: 1 request per second (Alpha Vantage free tier)
            time.sleep(1.0)
            
        except Exception as e:
            error_msg = str(e)
            if "rate limit" in error_msg.lower() or "25 requests" in error_msg.lower():
                results[stmt] = "rate_limit"
                print("[RATE LIMIT HIT]")
                return results  # Stop fetching for this ticker
            else:
                results[stmt] = f"error: {error_msg[:50]}"
                print(f"[ERROR: {error_msg[:50]}]")
    
    return results


def main():
    """Main function to fetch remaining fundamental data."""
    print("=" * 70)
    print("Fundamental Data Fetch Script")
    print("=" * 70)
    print()
    
    # Check what's already cached
    print("Checking existing data...")
    missing = get_missing_tickers()
    
    if not missing:
        print("\n[OK] All tickers have complete fundamental data!")
        return
    
    print(f"\nFound {len(missing)} tickers with missing data:\n")
    
    for ticker, missing_statements in missing:
        existing = [s for s in STATEMENTS if s not in missing_statements]
        print(f"  {ticker}: Missing {len(missing_statements)} statements")
        if existing:
            print(f"    Already have: {', '.join(existing)}")
        print(f"    Need to fetch: {', '.join(missing_statements)}")
    
    print("\n" + "=" * 70)
    print("Starting fetch process...")
    print("Rate limiting: 1 request per second (Alpha Vantage free tier)")
    print("=" * 70)
    print()
    
    total_requests = sum(len(stmts) for _, stmts in missing)
    print(f"Total API calls needed: {total_requests}")
    print(f"Estimated time: ~{total_requests} seconds ({total_requests/60:.1f} minutes)")
    print()
    
    # Auto-proceed (user requested continuation)
    print("Auto-proceeding with fetch...")
    print()
    
    # Fetch missing data
    success_count = 0
    error_count = 0
    rate_limit_hit = False
    
    for ticker, missing_statements in missing:
        if rate_limit_hit:
            print(f"\n⚠ Rate limit hit. Stopping fetch.")
            print(f"Remaining tickers: {[t for t, _ in missing[missing.index((ticker, missing_statements)):]]}")
            break
        
        print(f"Fetching {ticker} ({len(missing_statements)} statements)...")
        
        results = fetch_ticker_fundamentals(ticker, missing_statements)
        
        for stmt, result in results.items():
            if result == "success":
                success_count += 1
            elif result == "rate_limit":
                rate_limit_hit = True
                error_count += 1
                break
            else:
                error_count += 1
        
        print()
        
        if rate_limit_hit:
            break
    
    # Summary
    print("=" * 70)
    print("Fetch Summary")
    print("=" * 70)
    print(f"Successfully fetched: {success_count} statements")
    print(f"Errors: {error_count} statements")
    
    if rate_limit_hit:
        print("\n⚠ Rate limit reached. You've used your daily quota (25 requests/day).")
        print("Run this script again tomorrow to fetch remaining data.")
    else:
        print("\n[OK] All fundamental data fetched successfully!")
    
    # Show updated status
    print("\nCurrent data status:")
    remaining = get_missing_tickers()
    if remaining:
        print(f"Still missing: {len(remaining)} tickers")
        for ticker, stmts in remaining:
            print(f"  {ticker}: {', '.join(stmts)}")
    else:
        print("✓ All tickers have complete data!")


if __name__ == "__main__":
    main()
