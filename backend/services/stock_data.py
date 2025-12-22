"""
Stock Data Service

Handles loading and processing historical stock price data.
Primary source: yfinance API with caching
Fallback: CSV files in backend/data/
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from services.yfinance_provider import (
    fetch_price_data,
    is_ticker_supported,
    get_supported_tickers,
)


# Path to data directory
DATA_DIR = Path(__file__).parent.parent / "data"


class StockDataService:
    """Service for loading and querying stock price data from CSV files."""
    
    def __init__(self, data_dir: Path | str = DATA_DIR):
        """
        Initialize the stock data service.
        
        Args:
            data_dir: Directory containing CSV files with stock data
        """
        self.data_dir = Path(data_dir)
        self._cache: dict[str, pd.DataFrame] = {}
    
    def _get_csv_path(self, ticker: str) -> Path:
        """Get the path to a ticker's CSV file."""
        # Try exact match first
        exact_path = self.data_dir / f"{ticker}.csv"
        if exact_path.exists():
            return exact_path
        
        # Try uppercase
        upper_path = self.data_dir / f"{ticker.upper()}.csv"
        if upper_path.exists():
            return upper_path
        
        # Try lowercase
        lower_path = self.data_dir / f"{ticker.lower()}.csv"
        if lower_path.exists():
            return lower_path
        
        raise FileNotFoundError(f"No CSV file found for ticker {ticker}")
    
    def load_ticker_data(
        self,
        ticker: str,
        start_date: str = "2020-01-01",
        end_date: str = "2025-12-31"
    ) -> pd.DataFrame:
        """
        Load historical data for a ticker.
        
        Primary source: yfinance API (with disk caching)
        Fallback: CSV files in backend/data/
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date in YYYY-MM-DD format (default: 2020-01-01)
            end_date: End date in YYYY-MM-DD format (default: 2025-12-31)
            
        Returns:
            DataFrame with date as index and OHLCV columns
        """
        ticker_upper = ticker.upper()
        
        # Check memory cache first (for repeated calls in same session)
        cache_key = f"{ticker_upper}_{start_date}_{end_date}"
        if cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        # Try yfinance first (preferred source)
        if is_ticker_supported(ticker):
            try:
                df = fetch_price_data(
                    ticker=ticker,
                    start_date=start_date,
                    end_date=end_date,
                    interval="1d",
                    use_cache=True
                )
                
                # Cache in memory
                self._cache[cache_key] = df.copy()
                return df
                
            except Exception as e:
                print(f"Warning: yfinance failed for {ticker_upper}, trying CSV fallback: {e}")
        
        # Fallback to CSV files
        try:
            csv_path = self._get_csv_path(ticker)
            df = pd.read_csv(csv_path)
            
            # Standardize column names
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Convert date to datetime and set as index
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            df.set_index('date', inplace=True)
            
            # Filter by date range
            if start_date:
                df = df[df.index >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df.index <= pd.to_datetime(end_date)]
            
            # Cache in memory
            self._cache[cache_key] = df.copy()
            
            print(f"[CSV] Loaded {ticker_upper} from CSV fallback ({len(df)} rows)")
            return df
            
        except FileNotFoundError:
            raise FileNotFoundError(
                f"No data source available for ticker {ticker}. "
                f"Supported yfinance tickers: {', '.join(sorted(get_supported_tickers().keys()))}"
            )
    
    def get_price_data(
        self,
        ticker: str,
        start_date: str | None = None,
        end_date: str | None = None
    ) -> pd.DataFrame:
        """
        Get price data for a ticker within a date range.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            
        Returns:
            DataFrame with filtered price data
        """
        df = self.load_ticker_data(ticker)
        
        # Filter by date range if provided
        if start_date:
            df = df[df.index >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df.index <= pd.to_datetime(end_date)]
        
        return df
    
    def calculate_returns(
        self,
        ticker: str,
        start_date: str | None = None,
        end_date: str | None = None
    ) -> dict[str, Any]:
        """
        Calculate returns and statistics for a ticker over a date range.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            
        Returns:
            Dictionary with return statistics
        """
        df = self.get_price_data(ticker, start_date, end_date)
        
        if df.empty:
            return {
                "error": "No data available for the specified date range",
                "ticker": ticker,
                "start_date": start_date,
                "end_date": end_date
            }
        
        # Calculate statistics
        opening_price = df.iloc[0]['open']
        closing_price = df.iloc[-1]['close']
        period_return = ((closing_price - opening_price) / opening_price) * 100
        
        high_price = df['high'].max()
        low_price = df['low'].min()
        avg_volume = df['volume'].mean()
        
        # Calculate daily returns for volatility
        df['daily_return'] = df['close'].pct_change()
        volatility = df['daily_return'].std() * (252 ** 0.5) * 100  # Annualized
        
        # Find date of high and low
        high_date = df['high'].idxmax()
        low_date = df['low'].idxmin()
        
        return {
            "ticker": ticker.upper(),
            "start_date": str(df.index[0].date()),
            "end_date": str(df.index[-1].date()),
            "opening_price": round(opening_price, 2),
            "closing_price": round(closing_price, 2),
            "period_return_pct": round(period_return, 2),
            "high_price": round(high_price, 2),
            "high_date": str(high_date.date()),
            "low_price": round(low_price, 2),
            "low_date": str(low_date.date()),
            "avg_daily_volume": int(avg_volume),
            "volatility_annualized_pct": round(volatility, 2),
            "total_days": len(df)
        }
    
    def get_time_series(
        self,
        ticker: str,
        start_date: str | None = None,
        end_date: str | None = None,
        columns: list[str] | None = None
    ) -> dict[str, list]:
        """
        Get time series data for specific columns.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            columns: List of columns to include (default: ['close', 'volume'])
            
        Returns:
            Dictionary with dates and requested columns as lists
        """
        df = self.get_price_data(ticker, start_date, end_date)
        
        if df.empty:
            return {"error": "No data available"}
        
        if columns is None:
            columns = ['close', 'volume']
        
        # Prepare result
        result = {
            "ticker": ticker.upper(),
            "dates": [str(d.date()) for d in df.index]
        }
        
        for col in columns:
            col_lower = col.lower().replace(' ', '_')
            if col_lower in df.columns:
                result[col] = df[col_lower].tolist()
        
        return result
    
    def find_notable_movements(
        self,
        ticker: str,
        start_date: str | None = None,
        end_date: str | None = None,
        threshold_pct: float = 3.0
    ) -> list[dict[str, Any]]:
        """
        Find days with notable price movements (>threshold%).
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            threshold_pct: Minimum percentage change to be considered notable
            
        Returns:
            List of dictionaries with date and movement information
        """
        df = self.get_price_data(ticker, start_date, end_date)
        
        if df.empty:
            return []
        
        # Calculate daily percentage change
        df['pct_change'] = ((df['close'] - df['open']) / df['open']) * 100
        
        # Find notable movements
        notable = df[abs(df['pct_change']) >= threshold_pct].copy()
        
        movements = []
        for date, row in notable.iterrows():
            movements.append({
                "date": str(date.date()),
                "pct_change": round(row['pct_change'], 2),
                "open": round(row['open'], 2),
                "close": round(row['close'], 2),
                "direction": "up" if row['pct_change'] > 0 else "down"
            })
        
        return movements
    
    def _determine_interval(self, start_date: str, end_date: str) -> str:
        """
        Determine optimal time interval based on date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Pandas resample frequency string ('D', 'W', or 'ME')
        """
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        days = (end - start).days
        
        if days <= 90:  # Less than 3 months
            return 'D'  # Daily
        elif days <= 730:  # Less than 2 years
            return 'W'  # Weekly (Monday)
        else:
            return 'ME'  # Monthly (end of month)
    
    def get_chart_data(
        self,
        ticker: str,
        start_date: str | None = None,
        end_date: str | None = None,
        interval: str = 'auto'
    ) -> dict[str, Any]:
        """
        Get chart-ready OHLCV data with adaptive interval resampling.
        
        This method is optimized for frontend charting libraries. It automatically
        determines the best time interval based on the date range to balance
        detail and performance.
        
        Interval rules:
        - Daily (D): < 3 months (60-75 points)
        - Weekly (W): 3 months to 2 years (52 points/year)
        - Monthly (ME): > 2 years (12 points/year)
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            interval: Time interval ('D', 'W', 'ME', or 'auto' for adaptive)
            
        Returns:
            Dictionary with chart data ready for JSON serialization
            
        Raises:
            FileNotFoundError: If ticker data is not available
            ValueError: If date range is invalid
        """
        # Get price data
        df = self.get_price_data(ticker, start_date, end_date)
        
        if df.empty:
            return {
                "error": "No data available for the specified date range",
                "ticker": ticker.upper(),
                "start_date": start_date,
                "end_date": end_date
            }
        
        # Determine interval if auto
        actual_start = str(df.index[0].date())
        actual_end = str(df.index[-1].date())
        
        if interval == 'auto':
            interval = self._determine_interval(actual_start, actual_end)
        
        # Validate interval
        valid_intervals = ['D', 'W', 'ME', 'M']  # 'M' kept for backward compatibility
        if interval not in valid_intervals:
            raise ValueError(f"Invalid interval '{interval}'. Must be one of {valid_intervals} or 'auto'")
        
        # Convert deprecated 'M' to 'ME'
        if interval == 'M':
            interval = 'ME'
        
        # Resample data using OHLC aggregation
        try:
            resampled = df.resample(interval).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()  # Remove rows where all values are NaN
            
            # If adj_close exists, include it
            if 'adj_close' in df.columns:
                adj_resampled = df['adj_close'].resample(interval).last()
                resampled['adj_close'] = adj_resampled
            
        except Exception as e:
            return {
                "error": f"Error resampling data: {str(e)}",
                "ticker": ticker.upper()
            }
        
        if resampled.empty:
            return {
                "error": "No data after resampling",
                "ticker": ticker.upper(),
                "interval": interval
            }
        
        # Convert to JSON-serializable format
        result = {
            "ticker": ticker.upper(),
            "interval": interval,
            "interval_display": {
                'D': 'Daily',
                'W': 'Weekly',
                'ME': 'Monthly',
                'M': 'Monthly'  # Backward compatibility
            }[interval],
            "start_date": actual_start,
            "end_date": actual_end,
            "data_points": len(resampled),
            "dates": [d.isoformat() for d in resampled.index],
            "open": [round(v, 2) for v in resampled['open'].tolist()],
            "high": [round(v, 2) for v in resampled['high'].tolist()],
            "low": [round(v, 2) for v in resampled['low'].tolist()],
            "close": [round(v, 2) for v in resampled['close'].tolist()],
            "volume": [int(v) for v in resampled['volume'].tolist()],
        }
        
        # Add adj_close if available
        if 'adj_close' in resampled.columns:
            result['adj_close'] = [round(v, 2) for v in resampled['adj_close'].tolist()]
        
        return result
    
    def available_tickers(self) -> list[str]:
        """Get list of available tickers from yfinance whitelist and CSV files."""
        # Get yfinance supported tickers
        yfinance_tickers = set(get_supported_tickers().keys())
        
        # Get CSV tickers (fallback)
        csv_files = self.data_dir.glob("*.csv")
        csv_tickers = {f.stem.upper() for f in csv_files if f.name != "cache"}
        
        # Combine both sources (yfinance takes priority)
        all_tickers = yfinance_tickers | csv_tickers
        
        return sorted(list(all_tickers))


# Global instance
_stock_data_service = None

def get_stock_data_service() -> StockDataService:
    """Get or create the global stock data service instance."""
    global _stock_data_service
    if _stock_data_service is None:
        _stock_data_service = StockDataService()
    return _stock_data_service

