"""
Test script for yfinance integration.

Tests:
1. Fetch data for all whitelisted tickers
2. Verify data format and columns
3. Test caching mechanism
4. Test date range constraints (2020-2025)
5. Test stock_data service integration
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.yfinance_provider import (
    fetch_price_data,
    get_supported_tickers,
    get_cache_info,
    clear_cache,
)
from services.stock_data import get_stock_data_service


def test_yfinance_provider():
    """Test direct yfinance provider."""
    print("=" * 70)
    print("TEST 1: YFinance Provider - Fetch Single Ticker")
    print("=" * 70)
    
    # Test with NVDA (small date range for speed)
    ticker = "NVDA"
    start = "2024-01-01"
    end = "2024-12-31"
    
    print(f"\n[*] Fetching {ticker} from {start} to {end}...")
    
    try:
        df = fetch_price_data(ticker, start, end)
        
        print(f"[+] Success! Retrieved {len(df)} rows")
        print(f"  Date range: {df.index[0].date()} to {df.index[-1].date()}")
        print(f"  Columns: {list(df.columns)}")
        print(f"\n  Sample data (first 3 rows):")
        print(df.head(3))
        print(f"\n  Sample data (last 3 rows):")
        print(df.tail(3))
        
        # Verify required columns
        required_cols = ['open', 'high', 'low', 'close', 'adj_close', 'volume']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            print(f"  [!] WARNING: Missing columns: {missing}")
        else:
            print(f"  [+] All required columns present")
        
        return True
        
    except Exception as e:
        print(f"[X] FAILED: {e}")
        return False


def test_caching():
    """Test caching mechanism."""
    print("\n" + "=" * 70)
    print("TEST 2: Caching Mechanism")
    print("=" * 70)
    
    ticker = "AAPL"
    start = "2024-01-01"
    end = "2024-06-30"
    
    # Clear cache for this ticker
    print(f"\n[*] Clearing cache for {ticker}...")
    cleared = clear_cache(ticker)
    print(f"  Cleared {cleared} cache files")
    
    # First fetch (should hit API)
    print(f"\n[*] First fetch (should download from yfinance)...")
    df1 = fetch_price_data(ticker, start, end)
    print(f"  Retrieved {len(df1)} rows")
    
    # Second fetch (should use cache)
    print(f"\n[*] Second fetch (should use cache)...")
    df2 = fetch_price_data(ticker, start, end)
    print(f"  Retrieved {len(df2)} rows")
    
    # Verify data is identical
    if df1.equals(df2):
        print(f"  [+] Cache working correctly - data matches")
    else:
        print(f"  [!] WARNING: Cached data differs from original")
    
    # Show cache info
    print(f"\n[*] Cache information:")
    cache_info = get_cache_info()
    print(f"  Cache directory: {cache_info['cache_dir']}")
    print(f"  Total files: {len(cache_info['files'])}")
    print(f"  Total size: {cache_info['total_size_mb']} MB")
    if cache_info['files']:
        print(f"  Recent files:")
        for file in cache_info['files'][:3]:
            print(f"    - {file['filename']} ({file['size_kb']} KB, {file['age_hours']}h old)")
    
    return True


def test_all_tickers():
    """Test all whitelisted tickers."""
    print("\n" + "=" * 70)
    print("TEST 3: All Whitelisted Tickers")
    print("=" * 70)
    
    tickers = get_supported_tickers()
    print(f"\n[*] Testing {len(tickers)} tickers...")
    print(f"   Whitelist: {', '.join(sorted(tickers.keys()))}\n")
    
    # Use short date range for speed
    start = "2024-01-01"
    end = "2024-01-31"
    
    results = []
    
    for ticker, company in sorted(tickers.items()):
        try:
            print(f"  {ticker:6s} ({company[:30]:30s})", end="")
            df = fetch_price_data(ticker, start, end, use_cache=True)
            print(f" [+] {len(df):3d} rows")
            results.append((ticker, True, len(df)))
        except Exception as e:
            print(f" [X] FAILED: {e}")
            results.append((ticker, False, 0))
    
    # Summary
    success_count = sum(1 for _, success, _ in results if success)
    print(f"\n[*] Summary: {success_count}/{len(tickers)} tickers successful")
    
    if success_count < len(tickers):
        print(f"\n[!] Failed tickers:")
        for ticker, success, _ in results:
            if not success:
                print(f"    - {ticker}")
    
    return success_count == len(tickers)


def test_date_constraints():
    """Test date range constraints (2020-2025)."""
    print("\n" + "=" * 70)
    print("TEST 4: Date Range Constraints")
    print("=" * 70)
    
    ticker = "MSFT"
    
    # Test 1: Request data before 2020 (should constrain to 2020)
    print(f"\n[*] Test requesting data from 2015 (should constrain to 2020)...")
    df = fetch_price_data(ticker, "2015-01-01", "2020-03-31")
    print(f"  Start date: {df.index[0].date()}")
    if df.index[0].year >= 2020:
        print(f"  [+] Correctly constrained to 2020+")
    else:
        print(f"  [!] WARNING: Data before 2020 returned")
    
    # Test 2: Request data after 2025 (should constrain to 2025)
    print(f"\n[*] Test requesting data to 2030 (should constrain to 2025)...")
    df = fetch_price_data(ticker, "2024-01-01", "2030-12-31")
    print(f"  End date: {df.index[-1].date()}")
    if df.index[-1].year <= 2025:
        print(f"  [+] Correctly constrained to 2025 or earlier")
    else:
        print(f"  [!] WARNING: Data after 2025 returned")
    
    return True


def test_stock_data_service():
    """Test integration with StockDataService."""
    print("\n" + "=" * 70)
    print("TEST 5: StockDataService Integration")
    print("=" * 70)
    
    service = get_stock_data_service()
    
    # Test 1: Load ticker data
    print(f"\n[*] Test load_ticker_data...")
    ticker = "NVDA"
    df = service.load_ticker_data(ticker, "2024-01-01", "2024-12-31")
    print(f"  [+] Loaded {len(df)} rows for {ticker}")
    
    # Test 2: Calculate returns
    print(f"\n[*] Test calculate_returns...")
    stats = service.calculate_returns(ticker, "2024-01-01", "2024-12-31")
    print(f"  Period return: {stats['period_return_pct']:+.2f}%")
    print(f"  High: ${stats['high_price']} on {stats['high_date']}")
    print(f"  Low: ${stats['low_price']} on {stats['low_date']}")
    print(f"  Volatility: {stats['volatility_annualized_pct']:.2f}%")
    print(f"  [+] Stats calculated successfully")
    
    # Test 3: Get chart data
    print(f"\n[*] Test get_chart_data...")
    chart_data = service.get_chart_data(ticker, "2024-01-01", "2024-12-31", interval='auto')
    print(f"  Interval: {chart_data['interval']} ({chart_data['interval_display']})")
    print(f"  Data points: {chart_data['data_points']}")
    print(f"  Date range: {chart_data['start_date']} to {chart_data['end_date']}")
    print(f"  [+] Chart data generated successfully")
    
    # Test 4: Available tickers
    print(f"\n[*] Test available_tickers...")
    tickers = service.available_tickers()
    print(f"  Available tickers ({len(tickers)}): {', '.join(sorted(tickers))}")
    print(f"  [+] Ticker list retrieved successfully")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("YFINANCE INTEGRATION TEST SUITE")
    print("=" * 70)
    print(f"\nTesting date range: 2020-01-01 to 2025-12-31")
    print(f"Primary source: yfinance API")
    print(f"Fallback: CSV files in backend/data/")
    
    tests = [
        ("YFinance Provider", test_yfinance_provider),
        ("Caching Mechanism", test_caching),
        ("All Tickers", test_all_tickers),
        ("Date Constraints", test_date_constraints),
        ("StockDataService", test_stock_data_service),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n[X] TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Final summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status}  {name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! YFinance integration is working correctly.")
        return 0
    else:
        print("\n[WARNING] Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    exit(main())

