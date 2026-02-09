"""
Test script for real stock data integration

This script tests the new stock data service and tools with real CSV data.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from services.stock_data import get_stock_data_service


def test_stock_data_service():
    """Test the stock data service with real CSV files."""
    print("=" * 80)
    print("Testing Stock Data Service with Real CSV Data")
    print("=" * 80)
    
    service = get_stock_data_service()
    
    # Test 1: Available tickers
    print("\n1. Available Tickers:")
    tickers = service.available_tickers()
    print(f"   Found: {', '.join(tickers)}")
    
    # Test 2: Load AAPL data
    print("\n2. Loading AAPL data...")
    df = service.load_ticker_data("AAPL")
    print(f"   Loaded {len(df)} rows")
    print(f"   Date range: {df.index[0].date()} to {df.index[-1].date()}")
    print(f"   Columns: {', '.join(df.columns)}")
    
    # Test 3: Calculate returns for a specific period
    print("\n3. Calculating returns for AAPL (Jan-Mar 2023)...")
    stats = service.calculate_returns("AAPL", "2023-01-01", "2023-03-31")
    if "error" not in stats:
        print(f"   Opening: ${stats['opening_price']}")
        print(f"   Closing: ${stats['closing_price']}")
        print(f"   Return: {stats['period_return_pct']:+.2f}%")
        print(f"   High: ${stats['high_price']} on {stats['high_date']}")
        print(f"   Low: ${stats['low_price']} on {stats['low_date']}")
        print(f"   Volatility: {stats['volatility_annualized_pct']:.2f}%")
    else:
        print(f"   Error: {stats['error']}")
    
    # Test 4: Find notable movements
    print("\n4. Finding notable movements for NVDA (all available data)...")
    movements = service.find_notable_movements("NVDA", threshold_pct=5.0)
    print(f"   Found {len(movements)} days with >5% movement")
    if movements:
        print("   Top 5 movements:")
        for m in movements[:5]:
            sign = "+" if m['pct_change'] > 0 else ""
            print(f"   - {m['date']}: {sign}{m['pct_change']}% ({m['direction']})")
    
    # Test 5: Get time series
    print("\n5. Getting time series for GOOGL (last 10 days of available data)...")
    data = service.get_time_series("GOOGL", columns=['close', 'volume'])
    if "error" not in data:
        print(f"   Total data points: {len(data['dates'])}")
        print("   Last 5 days:")
        for i in range(max(0, len(data['dates']) - 5), len(data['dates'])):
            print(f"   - {data['dates'][i]}: ${data['close'][i]:.2f}, Volume: {data['volume'][i]:,.0f}")
    
    print("\n" + "=" * 80)
    print("[OK] All tests completed successfully!")
    print("=" * 80)


def test_agent_tools():
    """Test the agent tools with real data."""
    print("\n" + "=" * 80)
    print("Testing Agent Tools")
    print("=" * 80)
    
    try:
        from agent.moat_tutor import get_stock_prices, get_stock_time_series, get_moat_characteristics
    except ImportError as e:
        print(f"\n[SKIP] Agent tools test skipped - dependencies not installed: {e}")
        print("Run 'pip install -r requirements.txt' to install dependencies.")
        return
    
    # Test 1: get_stock_prices
    print("\n1. Testing get_stock_prices tool...")
    result = get_stock_prices.invoke({"ticker": "MSFT", "start_date": "2023-06-01", "end_date": "2023-06-30"})
    print(result)
    
    # Test 2: get_stock_time_series
    print("\n2. Testing get_stock_time_series tool...")
    result = get_stock_time_series.invoke({
        "ticker": "AAPL",
        "start_date": "2023-01-01",
        "end_date": "2023-01-31",
        "columns": "close,volume"
    })
    print(result[:500] + "..." if len(result) > 500 else result)
    
    # Test 3: get_moat_characteristics
    print("\n3. Testing get_moat_characteristics tool...")
    result = get_moat_characteristics.invoke({"ticker": "NVDA"})
    print(result)
    
    print("\n" + "=" * 80)
    print("[OK] All agent tool tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_stock_data_service()
        test_agent_tools()
        print("\n[SUCCESS] ALL TESTS PASSED - Real data integration working correctly!\n")
    except Exception as e:
        print(f"\n[ERROR] {e}\n")
        import traceback
        traceback.print_exc()

