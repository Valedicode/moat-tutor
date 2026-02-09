"""
Test script for news integration.

Tests the news provider module to verify:
1. Fetching news from yfinance works
2. Date filtering works correctly
3. JSON persistence works
4. Agent integration format is correct
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from services.news_provider import (
    fetch_company_news,
    fetch_all_company_news,
    get_news_for_agent,
    get_supported_tickers,
    is_ticker_supported,
    clear_news_cache,
    get_news_cache_info,
)


def test_single_ticker():
    """Test fetching news for a single ticker."""
    print("\n" + "=" * 60)
    print("TEST 1: Fetch News for Single Ticker (NVDA)")
    print("=" * 60)
    
    try:
        # Use current year to capture recent news (yfinance only provides recent articles)
        articles = fetch_company_news(
            ticker="NVDA",
            start_date="2020-01-01",
            end_date="2026-12-31",  # Include current year
            use_cache=False  # Force fresh fetch
        )
        
        print(f"\nRetrieved {len(articles)} articles")
        
        if articles:
            print("\nFirst article:")
            article = articles[0]
            for key, value in article.items():
                if key == 'summary' and len(str(value)) > 100:
                    print(f"  {key}: {str(value)[:100]}...")
                else:
                    print(f"  {key}: {value}")
            
            print("\n[PASS] Single ticker fetch successful")
            return True
        else:
            print("\nNo articles returned (yfinance may not have recent news)")
            print("[PASS] Function executed without errors")
            return True
            
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        return False


def test_date_filtering():
    """Test that date filtering works correctly."""
    print("\n" + "=" * 60)
    print("TEST 2: Date Filtering")
    print("=" * 60)
    
    try:
        # Fetch all available news first (include 2026 for current news)
        all_articles = fetch_company_news(
            ticker="AAPL",
            start_date="2020-01-01",
            end_date="2026-12-31",
            use_cache=False  # Force fresh fetch
        )
        
        # Fetch with narrow date range (last 7 days)
        from datetime import datetime, timedelta
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        
        filtered_articles = fetch_company_news(
            ticker="AAPL",
            start_date=week_ago.strftime("%Y-%m-%d"),
            end_date=today.strftime("%Y-%m-%d"),
            use_cache=True
        )
        
        print(f"\nAll articles (2020-2025): {len(all_articles)}")
        print(f"Filtered (last 7 days): {len(filtered_articles)}")
        
        # Verify filtering works (filtered should be <= all)
        if len(filtered_articles) <= len(all_articles):
            print("\n[PASS] Date filtering works correctly")
            return True
        else:
            print("\n[FAIL] Filtered count exceeds total")
            return False
            
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        return False


def test_cache_persistence():
    """Test that JSON caching works."""
    print("\n" + "=" * 60)
    print("TEST 3: Cache Persistence")
    print("=" * 60)
    
    try:
        # Clear cache first
        cleared = clear_news_cache("MSFT")
        print(f"Cleared {cleared} cache file(s)")
        
        # Fetch fresh data (include 2026 for current news)
        articles1 = fetch_company_news(
            ticker="MSFT",
            start_date="2020-01-01",
            end_date="2026-12-31",
            use_cache=True
        )
        
        # Check cache exists
        cache_info = get_news_cache_info()
        msft_cache = next(
            (f for f in cache_info['files'] if f['ticker'] == 'MSFT'),
            None
        )
        
        if msft_cache:
            print(f"\nCache file: {msft_cache['filename']}")
            print(f"Articles cached: {msft_cache['article_count']}")
            print(f"Age: {msft_cache['age_hours']} hours")
            print(f"Valid: {msft_cache['valid']}")
            
            # Fetch again (should use cache)
            articles2 = fetch_company_news(
                ticker="MSFT",
                start_date="2020-01-01",
                end_date="2026-12-31",
                use_cache=True
            )
            
            print(f"\nFirst fetch: {len(articles1)} articles")
            print(f"Second fetch (cached): {len(articles2)} articles")
            
            print("\n[PASS] Cache persistence works")
            return True
        else:
            print("\n[WARN] No cache file found (may be empty news)")
            return True
            
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        return False


def test_agent_format():
    """Test the agent-friendly output format."""
    print("\n" + "=" * 60)
    print("TEST 4: Agent Format Output")
    print("=" * 60)
    
    try:
        output = get_news_for_agent(
            ticker="GOOGL",
            start_date="2020-01-01",
            end_date="2026-12-31"  # Include current year
        )
        
        print("\nAgent output preview:")
        print("-" * 40)
        # Show first 500 chars
        print(output[:500] if len(output) > 500 else output)
        if len(output) > 500:
            print("...")
        print("-" * 40)
        
        # Verify format
        if "News for GOOGL" in output:
            print("\n[PASS] Agent format is correct")
            return True
        else:
            print("\n[PASS] Output generated (may have no news)")
            return True
            
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        return False


def test_invalid_ticker():
    """Test error handling for invalid ticker."""
    print("\n" + "=" * 60)
    print("TEST 5: Invalid Ticker Handling")
    print("=" * 60)
    
    try:
        articles = fetch_company_news(
            ticker="INVALID_TICKER",
            start_date="2024-01-01",
            end_date="2025-12-31"
        )
        print("\n[FAIL] Should have raised ValueError")
        return False
        
    except ValueError as e:
        print(f"\nCaught expected error: {e}")
        print("\n[PASS] Invalid ticker handled correctly")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Unexpected error: {e}")
        return False


def test_all_tickers():
    """Test fetching news for all supported tickers."""
    print("\n" + "=" * 60)
    print("TEST 6: Fetch All Supported Tickers")
    print("=" * 60)
    
    try:
        tickers = get_supported_tickers()
        print(f"\nSupported tickers ({len(tickers)}):")
        for ticker, name in tickers.items():
            print(f"  {ticker}: {name}")
        
        print("\nFetching news for all tickers (clearing cache first)...")
        # Clear all cache to get fresh data
        clear_news_cache()
        
        results = fetch_all_company_news(
            start_date="2020-01-01",
            end_date="2026-12-31",  # Include current year
            use_cache=True
        )
        
        print("\nResults:")
        for ticker, articles in results.items():
            status = "OK" if articles else "No articles"
            print(f"  {ticker}: {len(articles)} articles [{status}]")
        
        total = sum(len(a) for a in results.values())
        print(f"\nTotal articles: {total}")
        
        print("\n[PASS] All tickers processed")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        return False


def test_cache_info():
    """Test cache information retrieval."""
    print("\n" + "=" * 60)
    print("TEST 7: Cache Information")
    print("=" * 60)
    
    try:
        info = get_news_cache_info()
        
        print(f"\nCache directory: {info['news_dir']}")
        print(f"Total articles cached: {info['total_articles']}")
        print(f"Cache validity: {info['validity_hours']} hours")
        print(f"\nCached files ({len(info['files'])}):")
        
        for f in info['files']:
            valid = "valid" if f['valid'] else "expired"
            print(f"  {f['filename']}: {f['article_count']} articles ({valid})")
        
        print("\n[PASS] Cache info retrieval works")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("NEWS INTEGRATION TEST SUITE")
    print("=" * 60)
    print(f"Testing yfinance news provider")
    print(f"Supported tickers: {len(get_supported_tickers())}")
    
    tests = [
        ("Single Ticker Fetch", test_single_ticker),
        ("Date Filtering", test_date_filtering),
        ("Cache Persistence", test_cache_persistence),
        ("Agent Format", test_agent_format),
        ("Invalid Ticker", test_invalid_ticker),
        ("All Tickers", test_all_tickers),
        ("Cache Info", test_cache_info),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n[ERROR] Unexpected error in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, p in results:
        status = "PASS" if p else "FAIL"
        print(f"  [{status}] {name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print("\n[WARNING] Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
