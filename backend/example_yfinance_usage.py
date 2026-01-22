"""
Example: How to use the yfinance integration

This shows how existing code continues to work without changes.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.stock_data import get_stock_data_service

# Get the service (same as before)
service = get_stock_data_service()

print("=" * 70)
print("EXAMPLE 1: Get Price Data (now from yfinance)")
print("=" * 70)

# This now uses yfinance instead of CSV, but code is identical
df = service.get_price_data("NVDA", "2024-01-01", "2024-12-31")
print(f"\nRetrieved {len(df)} rows for NVDA")
print(f"Columns: {list(df.columns)}")
print(f"\nFirst 5 rows:")
print(df.head())

print("\n" + "=" * 70)
print("EXAMPLE 2: Calculate Returns (no code changes)")
print("=" * 70)

# Same API, now using yfinance data
stats = service.calculate_returns("AAPL", "2024-01-01", "2024-12-31")
print(f"\nAAPL Performance (2024):")
print(f"  Opening price: ${stats['opening_price']}")
print(f"  Closing price: ${stats['closing_price']}")
print(f"  Period return: {stats['period_return_pct']:+.2f}%")
print(f"  High: ${stats['high_price']} on {stats['high_date']}")
print(f"  Low: ${stats['low_price']} on {stats['low_date']}")
print(f"  Volatility: {stats['volatility_annualized_pct']:.2f}%")

print("\n" + "=" * 70)
print("EXAMPLE 3: Chart Data for Frontend (no changes)")
print("=" * 70)

# Get chart-ready data (automatic interval selection)
chart_data = service.get_chart_data("MSFT", "2024-01-01", "2024-12-31", interval='auto')
print(f"\nMSFT Chart Data:")
print(f"  Ticker: {chart_data['ticker']}")
print(f"  Interval: {chart_data['interval']} ({chart_data['interval_display']})")
print(f"  Data points: {chart_data['data_points']}")
print(f"  Date range: {chart_data['start_date']} to {chart_data['end_date']}")
print(f"\nFirst 3 data points:")
for i in range(min(3, len(chart_data['dates']))):
    print(f"  {chart_data['dates'][i]}: "
          f"O=${chart_data['open'][i]} "
          f"H=${chart_data['high'][i]} "
          f"L=${chart_data['low'][i]} "
          f"C=${chart_data['close'][i]}")

print("\n" + "=" * 70)
print("EXAMPLE 4: Available Tickers (includes yfinance whitelist)")
print("=" * 70)

tickers = service.available_tickers()
print(f"\nAvailable tickers ({len(tickers)}): {', '.join(tickers)}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("\n[SUCCESS] All examples ran successfully!")
print("\nKey points:")
print("  - Existing code requires NO changes")
print("  - Data now comes from yfinance (live, up-to-date)")
print("  - Disk caching makes it fast (24h cache validity)")
print("  - CSV files kept as fallback for reliability")
print("  - Date range: 2020-2025 (5 years)")
print("  - 10 supported tickers (whitelist)")



