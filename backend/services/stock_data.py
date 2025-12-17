"""
Stock Data Service

Handles loading and processing historical stock price data from CSV files.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


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
    
    def load_ticker_data(self, ticker: str) -> pd.DataFrame:
        """
        Load historical data for a ticker from CSV.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            DataFrame with date as index and OHLCV columns
        """
        # Check cache first
        ticker_upper = ticker.upper()
        if ticker_upper in self._cache:
            return self._cache[ticker_upper].copy()
        
        # Load from CSV
        csv_path = self._get_csv_path(ticker)
        df = pd.read_csv(csv_path)
        
        # Standardize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Convert date to datetime and set as index
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        df.set_index('date', inplace=True)
        
        # Cache it
        self._cache[ticker_upper] = df.copy()
        
        return df
    
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
    
    def available_tickers(self) -> list[str]:
        """Get list of available tickers from CSV files."""
        csv_files = self.data_dir.glob("*.csv")
        return [f.stem.upper() for f in csv_files]


# Global instance
_stock_data_service = None

def get_stock_data_service() -> StockDataService:
    """Get or create the global stock data service instance."""
    global _stock_data_service
    if _stock_data_service is None:
        _stock_data_service = StockDataService()
    return _stock_data_service

