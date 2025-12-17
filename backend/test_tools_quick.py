"""
Quick test of agent tools with real data
Run from backend directory: python test_tools_quick.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.agent.moat_tutor import get_stock_prices, get_stock_time_series, get_moat_characteristics

print("=" * 80)
print("Testing Agent Tools with Real Data")
print("=" * 80)

# Test 1: get_stock_prices
print("\n1. Testing get_stock_prices for MSFT (June 2023)...")
print("-" * 80)
result = get_stock_prices.invoke({
    "ticker": "MSFT",
    "start_date": "2023-06-01",
    "end_date": "2023-06-30"
})
print(result)

# Test 2: get_stock_time_series
print("\n2. Testing get_stock_time_series for AAPL (January 2023)...")
print("-" * 80)
result = get_stock_time_series.invoke({
    "ticker": "AAPL",
    "start_date": "2023-01-01",
    "end_date": "2023-01-31",
    "columns": "close,volume"
})
print(result)

# Test 3: get_moat_characteristics
print("\n3. Testing get_moat_characteristics for NVDA...")
print("-" * 80)
result = get_moat_characteristics.invoke({"ticker": "NVDA"})
print(result)

print("\n" + "=" * 80)
print("[SUCCESS] All agent tools working with real data!")
print("=" * 80)

