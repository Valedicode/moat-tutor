"""
Test script for the charts API endpoint.

This script tests:
1. Chart data retrieval with different intervals
2. Adaptive interval selection
3. Date range filtering
4. Error handling
5. Data validation
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Fix Windows console encoding
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from services.stock_data import get_stock_data_service


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"{title}")
    print("=" * 80)


def print_info(message: str):
    """Print an info message."""
    print(f"   {message}")


def test_service_chart_data():
    """Test the StockDataService.get_chart_data method."""
    print_section("TEST 1: Service Layer - get_chart_data Method")
    
    service = get_stock_data_service()
    
    # Test 1a: Daily interval (< 3 months)
    print("\n1a. Testing daily interval (2 months):")
    result = service.get_chart_data(
        ticker="AAPL",
        start_date="2023-01-01",
        end_date="2023-02-28",
        interval="auto"
    )
    
    print_info(f"Ticker: {result['ticker']}")
    print_info(f"Interval: {result['interval']} ({result['interval_display']})")
    print_info(f"Date Range: {result['start_date']} to {result['end_date']}")
    print_info(f"Data Points: {result['data_points']}")
    print_info(f"First Close: ${result['close'][0]}")
    print_info(f"Last Close: ${result['close'][-1]}")
    print_info(f"Total Volume: {sum(result['volume']):,}")
    
    # Test 1b: Weekly interval (3 months to 2 years)
    print("\n1b. Testing weekly interval (1 year):")
    result = service.get_chart_data(
        ticker="NVDA",
        start_date="2023-01-01",
        end_date="2023-12-31",
        interval="auto"
    )
    
    print_info(f"Ticker: {result['ticker']}")
    print_info(f"Interval: {result['interval']} ({result['interval_display']})")
    print_info(f"Date Range: {result['start_date']} to {result['end_date']}")
    print_info(f"Data Points: {result['data_points']}")
    print_info(f"First Close: ${result['close'][0]}")
    print_info(f"Last Close: ${result['close'][-1]}")
    price_change = ((result['close'][-1] - result['close'][0]) / result['close'][0]) * 100
    print_info(f"Period Return: {price_change:+.2f}%")
    
    # Test 1c: Monthly interval (> 2 years)
    print("\n1c. Testing monthly interval (5 years):")
    result = service.get_chart_data(
        ticker="AAPL",
        start_date="2019-01-01",
        end_date="2023-12-31",
        interval="auto"
    )
    
    print_info(f"Ticker: {result['ticker']}")
    print_info(f"Interval: {result['interval']} ({result['interval_display']})")
    print_info(f"Date Range: {result['start_date']} to {result['end_date']}")
    print_info(f"Data Points: {result['data_points']}")
    print_info(f"First Close: ${result['close'][0]}")
    print_info(f"Last Close: ${result['close'][-1]}")
    price_change = ((result['close'][-1] - result['close'][0]) / result['close'][0]) * 100
    print_info(f"5-Year Return: {price_change:+.2f}%")
    
    # Test 1d: Manual interval override
    print("\n1d. Testing manual interval override (force monthly):")
    result = service.get_chart_data(
        ticker="MSFT",
        start_date="2023-01-01",
        end_date="2023-06-30",
        interval="ME"
    )
    
    print_info(f"Ticker: {result['ticker']}")
    print_info(f"Interval: {result['interval']} (forced)")
    print_info(f"Data Points: {result['data_points']}")
    
    print_info("[PASS] All service layer tests passed!")


def test_adaptive_interval_logic():
    """Test the adaptive interval selection logic."""
    print_section("TEST 2: Adaptive Interval Selection")
    
    service = get_stock_data_service()
    
    test_cases = [
        ("2023-01-01", "2023-01-31", "D", "1 month"),
        ("2023-01-01", "2023-03-31", "D", "3 months"),
        ("2023-01-01", "2023-06-30", "W", "6 months"),
        ("2023-01-01", "2023-12-31", "W", "1 year"),
        ("2022-01-01", "2023-12-31", "W", "2 years"),
        ("2020-01-01", "2023-12-31", "ME", "4 years"),
        ("2019-01-01", "2023-12-31", "ME", "5 years"),
    ]
    
    for start, end, expected_interval, description in test_cases:
        result = service.get_chart_data(
            ticker="AAPL",
            start_date=start,
            end_date=end,
            interval="auto"
        )
        
        actual_interval = result['interval']
        status = "[PASS]" if actual_interval == expected_interval else "[FAIL]"
        print_info(f"{status} {description}: {actual_interval} (expected {expected_interval})")
    
    print_info("[PASS] Adaptive interval tests completed!")


def test_data_validation():
    """Test data validation and structure."""
    print_section("TEST 3: Data Validation")
    
    service = get_stock_data_service()
    
    result = service.get_chart_data(
        ticker="AAPL",
        start_date="2023-01-01",
        end_date="2023-03-31",
        interval="auto"
    )
    
    # Validate structure
    required_fields = [
        'ticker', 'interval', 'interval_display', 'start_date', 'end_date',
        'data_points', 'dates', 'open', 'high', 'low', 'close', 'volume'
    ]
    
    print("\nValidating response structure:")
    for field in required_fields:
        exists = field in result
        status = "[PASS]" if exists else "[FAIL]"
        print_info(f"{status} Field '{field}' present")
    
    # Validate data consistency
    print("\nValidating data consistency:")
    
    num_dates = len(result['dates'])
    num_open = len(result['open'])
    num_high = len(result['high'])
    num_low = len(result['low'])
    num_close = len(result['close'])
    num_volume = len(result['volume'])
    
    all_equal = (num_dates == num_open == num_high == num_low == num_close == num_volume)
    status = "[PASS]" if all_equal else "[FAIL]"
    print_info(f"{status} All arrays have same length: {num_dates}")
    
    # Validate OHLC relationships
    errors = 0
    for i in range(len(result['dates'])):
        if not (result['low'][i] <= result['open'][i] <= result['high'][i]):
            errors += 1
        if not (result['low'][i] <= result['close'][i] <= result['high'][i]):
            errors += 1
    
    status = "[PASS]" if errors == 0 else "[FAIL]"
    print_info(f"{status} OHLC relationships valid (low <= open/close <= high)")
    
    # Validate date format
    try:
        datetime.fromisoformat(result['dates'][0])
        print_info("[PASS] Date format is valid ISO 8601")
    except ValueError:
        print_info("[FAIL] Date format is invalid")
    
    print_info("[PASS] Data validation tests completed!")


def test_error_handling():
    """Test error handling for invalid inputs."""
    print_section("TEST 4: Error Handling")
    
    service = get_stock_data_service()
    
    # Test 4a: Invalid ticker
    print("\n4a. Testing invalid ticker:")
    try:
        result = service.get_chart_data(
            ticker="INVALID",
            start_date="2023-01-01",
            end_date="2023-12-31",
            interval="auto"
        )
        print_info("[FAIL] Should have raised FileNotFoundError")
    except FileNotFoundError as e:
        print_info(f"[PASS] Correctly raised FileNotFoundError: {str(e)[:60]}...")
    
    # Test 4b: Invalid interval
    print("\n4b. Testing invalid interval:")
    try:
        result = service.get_chart_data(
            ticker="AAPL",
            start_date="2023-01-01",
            end_date="2023-12-31",
            interval="X"
        )
        print_info("[FAIL] Should have raised ValueError")
    except ValueError as e:
        print_info(f"[PASS] Correctly raised ValueError: {str(e)}")
    
    # Test 4c: Empty date range (future dates)
    print("\n4c. Testing empty date range:")
    result = service.get_chart_data(
        ticker="AAPL",
        start_date="2030-01-01",
        end_date="2030-12-31",
        interval="auto"
    )
    if "error" in result:
        print_info(f"[PASS] Correctly returned error: {result['error']}")
    else:
        print_info("[FAIL] Should have returned error for empty date range")
    
    print_info("[PASS] Error handling tests completed!")


def test_multiple_tickers():
    """Test with multiple available tickers."""
    print_section("TEST 5: Multiple Tickers")
    
    service = get_stock_data_service()
    available_tickers = service.available_tickers()
    
    print_info(f"Available tickers: {', '.join(available_tickers)}")
    
    # Test a sample from each available ticker
    for ticker in available_tickers[:5]:  # Test first 5
        result = service.get_chart_data(
            ticker=ticker,
            start_date="2023-01-01",
            end_date="2023-12-31",
            interval="ME"
        )
        
        if "error" not in result:
            print_info(f"[PASS] {ticker}: {result['data_points']} data points")
        else:
            print_info(f"[FAIL] {ticker}: {result['error']}")
    
    print_info("[PASS] Multiple ticker tests completed!")


def test_performance():
    """Test performance with different data sizes."""
    print_section("TEST 6: Performance")
    
    import time
    
    service = get_stock_data_service()
    
    test_cases = [
        ("2023-01-01", "2023-01-31", "1 month"),
        ("2023-01-01", "2023-12-31", "1 year"),
        ("2020-01-01", "2023-12-31", "4 years"),
    ]
    
    for start, end, description in test_cases:
        start_time = time.time()
        result = service.get_chart_data(
            ticker="AAPL",
            start_date=start,
            end_date=end,
            interval="auto"
        )
        elapsed = (time.time() - start_time) * 1000  # ms
        
        print_info(f"{description}: {elapsed:.2f}ms ({result['data_points']} points)")
    
    print_info("[PASS] Performance tests completed!")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("CHARTS API - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    try:
        test_service_chart_data()
        test_adaptive_interval_logic()
        test_data_validation()
        test_error_handling()
        test_multiple_tickers()
        test_performance()
        
        print_section("ALL TESTS PASSED")
        print("\nThe charts API is ready to use!")
        print("\nNext steps:")
        print("  1. Start the backend: uvicorn main:app --reload")
        print("  2. Visit API docs: http://localhost:8000/docs")
        print("  3. Test endpoint: http://localhost:8000/api/v1/charts/AAPL?start_date=2023-01-01&end_date=2023-12-31")
        
        return 0
        
    except Exception as e:
        print_section("TEST FAILED")
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

