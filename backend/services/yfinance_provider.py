"""
YFinance Data Provider

Fetches stock price data from Yahoo Finance with disk caching for performance.
Supports a whitelist of tech companies with date range 2020-2025.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf

# Cache directory
CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"

# Whitelist of supported tickers
SUPPORTED_TICKERS = {
    "NVDA": "NVIDIA Corporation",
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "AVGO": "Broadcom Inc.",
    "ORCL": "Oracle Corporation",
    "AMD": "Advanced Micro Devices, Inc.",
    "CSCO": "Cisco Systems, Inc.",
    "PLTR": "Palantir Technologies Inc.",
    "MU": "Micron Technology",
    "GOOGL": "Alphabet Inc. (Google)",  # Keep existing ones from CSV
}

# Date range constraints
MIN_DATE = "2020-01-01"
MAX_DATE = "2025-12-31"

# Cache validity period (24 hours)
CACHE_VALIDITY_HOURS = 24


def _get_cache_path(ticker: str, start_date: str, end_date: str) -> Path:
    """Get the cache file path for a ticker and date range."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{ticker.upper()}_{start_date}_{end_date}.parquet"
    return CACHE_DIR / filename


def _is_cache_valid(cache_path: Path) -> bool:
    """Check if cache file exists and is still valid."""
    if not cache_path.exists():
        return False
    
    # Check file modification time
    mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
    age = datetime.now() - mtime
    
    return age < timedelta(hours=CACHE_VALIDITY_HOURS)


def _load_from_cache(cache_path: Path) -> Optional[pd.DataFrame]:
    """Load data from cache if valid."""
    if _is_cache_valid(cache_path):
        try:
            df = pd.read_parquet(cache_path)
            df.index = pd.to_datetime(df.index)
            return df
        except Exception as e:
            print(f"Warning: Failed to load cache {cache_path}: {e}")
            return None
    return None


def _save_to_cache(df: pd.DataFrame, cache_path: Path) -> None:
    """Save data to cache."""
    try:
        df.to_parquet(cache_path)
    except Exception as e:
        print(f"Warning: Failed to save cache {cache_path}: {e}")


def fetch_price_data(
    ticker: str,
    start_date: str = MIN_DATE,
    end_date: str = MAX_DATE,
    interval: str = "1d",
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Fetch adjusted OHLCV price data from yfinance with disk caching.
    
    Args:
        ticker: Stock ticker symbol (must be in whitelist)
        start_date: Start date in YYYY-MM-DD format (default: 2020-01-01)
        end_date: End date in YYYY-MM-DD format (default: 2025-12-31)
        interval: Data interval (default: 1d for daily)
        use_cache: Whether to use cached data (default: True)
        
    Returns:
        DataFrame with columns: open, high, low, close, adj_close, volume
        Index: datetime (date)
        
    Raises:
        ValueError: If ticker is not in whitelist or date range is invalid
        Exception: If data fetch fails
    """
    ticker_upper = ticker.upper()
    
    # Validate ticker
    if ticker_upper not in SUPPORTED_TICKERS:
        available = ", ".join(sorted(SUPPORTED_TICKERS.keys()))
        raise ValueError(
            f"Ticker '{ticker}' not supported. Available tickers: {available}"
        )
    
    # Validate and constrain date range
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    min_date = pd.to_datetime(MIN_DATE)
    max_date = pd.to_datetime(MAX_DATE)
    
    if start < min_date:
        start = min_date
        start_date = MIN_DATE
    if end > max_date:
        end = max_date
        end_date = MAX_DATE
    
    if start >= end:
        raise ValueError(f"Start date {start_date} must be before end date {end_date}")
    
    # Check cache first
    cache_path = _get_cache_path(ticker_upper, start_date, end_date)
    if use_cache:
        cached_df = _load_from_cache(cache_path)
        if cached_df is not None:
            print(f"[CACHE] Loaded {ticker_upper} from cache ({len(cached_df)} rows)")
            return cached_df
    
    # Fetch from yfinance
    print(f"[FETCH] Fetching {ticker_upper} from yfinance ({start_date} to {end_date})...")
    
    try:
        # Download data
        df = yf.download(
            ticker_upper,
            start=start_date,
            end=end_date,
            interval=interval,
            progress=False,
            auto_adjust=False  # We want both Close and Adj Close
        )
        
        if df.empty:
            raise ValueError(f"No data returned from yfinance for {ticker_upper}")
        
        # Handle MultiIndex columns (yfinance sometimes returns MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Standardize column names (yfinance uses title case)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Ensure we have the required columns
        required_cols = ['open', 'high', 'low', 'close', 'adj_close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing columns from yfinance: {missing_cols}")
        
        # Keep only required columns
        df = df[required_cols]
        
        # Remove any rows with NaN values
        df = df.dropna()
        
        # Ensure index is datetime
        df.index = pd.to_datetime(df.index)
        df.index.name = 'date'
        
        # Sort by date
        df = df.sort_index()
        
        # Save to cache
        if use_cache:
            _save_to_cache(df, cache_path)
        
        print(f"[SUCCESS] Fetched {ticker_upper}: {len(df)} rows from {df.index[0].date()} to {df.index[-1].date()}")
        
        return df
        
    except Exception as e:
        raise Exception(f"Failed to fetch data for {ticker_upper}: {str(e)}")


def get_supported_tickers() -> dict[str, str]:
    """Get dictionary of supported tickers and company names."""
    return SUPPORTED_TICKERS.copy()


def is_ticker_supported(ticker: str) -> bool:
    """Check if a ticker is in the whitelist."""
    return ticker.upper() in SUPPORTED_TICKERS


def clear_cache(ticker: Optional[str] = None) -> int:
    """
    Clear cached data.
    
    Args:
        ticker: Optional ticker to clear cache for (if None, clears all)
        
    Returns:
        Number of cache files deleted
    """
    if not CACHE_DIR.exists():
        return 0
    
    count = 0
    if ticker:
        # Clear specific ticker
        pattern = f"{ticker.upper()}_*.parquet"
        for cache_file in CACHE_DIR.glob(pattern):
            cache_file.unlink()
            count += 1
    else:
        # Clear all cache
        for cache_file in CACHE_DIR.glob("*.parquet"):
            cache_file.unlink()
            count += 1
    
    return count


def get_cache_info() -> dict:
    """Get information about cached files."""
    if not CACHE_DIR.exists():
        return {"cache_dir": str(CACHE_DIR), "files": [], "total_size_mb": 0}
    
    files = []
    total_size = 0
    
    for cache_file in CACHE_DIR.glob("*.parquet"):
        size = cache_file.stat().st_size
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        age = datetime.now() - mtime
        
        files.append({
            "filename": cache_file.name,
            "size_kb": round(size / 1024, 2),
            "modified": mtime.isoformat(),
            "age_hours": round(age.total_seconds() / 3600, 1),
            "valid": age < timedelta(hours=CACHE_VALIDITY_HOURS)
        })
        total_size += size
    
    return {
        "cache_dir": str(CACHE_DIR),
        "files": sorted(files, key=lambda x: x["modified"], reverse=True),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "validity_hours": CACHE_VALIDITY_HOURS
    }

