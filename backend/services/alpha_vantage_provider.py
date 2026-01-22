"""
Alpha Vantage News Provider

Fetches financial news articles from Alpha Vantage NEWS_SENTIMENT endpoint.
Used to fill the 2024-2025 news gap between FNSPID (2015-2023) and yfinance (last ~30 days).

Supports disk caching to minimize API calls (free tier: 5 req/min, 500 req/day).
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Alpha Vantage configuration
ALPHA_VANTAGE_BASE_URL = os.getenv(
    "ALPHA_VANTAGE_BASE_URL", 
    "https://www.alphavantage.co/query"
)

# Cache directory (reuse news cache)
NEWS_CACHE_DIR = Path(__file__).parent.parent / "data" / "news"

# Cache validity period (7 days - historical news doesn't change)
CACHE_VALIDITY_HOURS = 168  # 7 days


def _ymd_to_av_time(date_str: str, end_of_day: bool = False) -> str:
    """
    Convert YYYY-MM-DD to Alpha Vantage time format (YYYYMMDDTHHMM).
    
    Args:
        date_str: Date in YYYY-MM-DD format
        end_of_day: If True, use 23:59; otherwise use 00:00
        
    Returns:
        Timestamp in YYYYMMDDTHHMM format
    """
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        time_suffix = "T2359" if end_of_day else "T0000"
        return dt.strftime(f"%Y%m%d{time_suffix}")
    except ValueError as e:
        logger.warning(f"Invalid date format {date_str}: {e}")
        return ""


def _av_time_to_ymd(av_timestamp: str) -> str:
    """
    Convert Alpha Vantage timestamp (YYYYMMDDTHHMMSS) to YYYY-MM-DD.
    
    Args:
        av_timestamp: Timestamp from Alpha Vantage (e.g., '20240315T153000')
        
    Returns:
        Date in YYYY-MM-DD format
    """
    if not av_timestamp or len(av_timestamp) < 8:
        return ""
    
    try:
        # Extract YYYYMMDD part
        date_part = av_timestamp[:8]
        return f"{date_part[0:4]}-{date_part[4:6]}-{date_part[6:8]}"
    except Exception as e:
        logger.warning(f"Failed to parse Alpha Vantage timestamp {av_timestamp}: {e}")
        return ""


def _get_cache_path(ticker: str, start_date: str, end_date: str) -> Path:
    """Get the cache file path for Alpha Vantage news."""
    NEWS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{ticker.upper()}_alphavantage_{start_date}_{end_date}.json"
    return NEWS_CACHE_DIR / filename


def _is_cache_valid(cache_path: Path) -> bool:
    """Check if cache file exists and is still valid."""
    if not cache_path.exists():
        return False
    
    mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
    age = datetime.now() - mtime
    
    return age < timedelta(hours=CACHE_VALIDITY_HOURS)


def _normalize_alpha_vantage_item(ticker: str, item: dict) -> dict:
    """
    Normalize Alpha Vantage news item to our standard format.
    
    Args:
        ticker: Stock ticker symbol
        item: Raw news item from Alpha Vantage
        
    Returns:
        Normalized dictionary matching our news schema
    """
    # Parse timestamp
    time_published = item.get("time_published", "")
    date = _av_time_to_ymd(time_published)
    
    # Extract topics (optional metadata)
    topics = []
    for topic_obj in item.get("topics", []):
        if isinstance(topic_obj, dict) and "topic" in topic_obj:
            topics.append(topic_obj["topic"])
    
    return {
        "ticker": ticker.upper(),
        "date": date,
        "title": item.get("title", ""),
        "publisher": item.get("source", "") or item.get("source_domain", ""),
        "summary": item.get("summary", ""),
        "url": item.get("url", ""),
        "uuid": item.get("url", ""),  # Use URL as stable identifier
        "type": "alpha_vantage_news",
        "providerPublishTime": 0,
        "pubDate": time_published,
        "topics": topics,  # Optional: useful for 2024-2025 filtering
        # Intentionally NOT storing sentiment fields
    }


def fetch_alpha_vantage_news(
    ticker: str,
    start_date: str,
    end_date: str,
    use_cache: bool = True,
    limit: int = 1000,
) -> list[dict]:
    """
    Fetch news articles from Alpha Vantage NEWS_SENTIMENT endpoint.
    
    Args:
        ticker: Stock ticker symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        use_cache: Whether to use cached data (default: True)
        limit: Maximum number of articles to retrieve (default: 1000)
        
    Returns:
        List of normalized news article dictionaries
        
    Raises:
        ValueError: If ALPHA_VANTAGE_API_KEY is not set
        RuntimeError: If API returns an error
    """
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        raise ValueError(
            "ALPHA_VANTAGE_API_KEY environment variable not set. "
            "Get your free key at: https://www.alphavantage.co/support/#api-key"
        )
    
    ticker_upper = ticker.upper()
    
    # Check cache first
    cache_path = _get_cache_path(ticker_upper, start_date, end_date)
    if use_cache and _is_cache_valid(cache_path):
        try:
            cached_data = json.loads(cache_path.read_text(encoding="utf-8"))
            logger.info(f"[CACHE] Loaded {len(cached_data)} Alpha Vantage articles for {ticker_upper}")
            return cached_data
        except Exception as e:
            logger.warning(f"Failed to load cache {cache_path}: {e}")
    
    # Fetch from Alpha Vantage
    logger.info(f"[FETCH] Fetching Alpha Vantage news for {ticker_upper} ({start_date} to {end_date})...")
    
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker_upper,
        "time_from": _ymd_to_av_time(start_date, end_of_day=False),
        "time_to": _ymd_to_av_time(end_date, end_of_day=True),
        "limit": str(limit),
        "sort": "EARLIEST",  # Chronological order
        "apikey": api_key,
    }
    
    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        
        # Check for API errors
        if "Information" in payload:
            # Rate limit or other informational message
            raise RuntimeError(f"Alpha Vantage API: {payload['Information']}")
        
        if "Error Message" in payload:
            raise RuntimeError(f"Alpha Vantage API Error: {payload['Error Message']}")
        
        if "Note" in payload:
            # Often rate limit message
            raise RuntimeError(f"Alpha Vantage API: {payload['Note']}")
        
        # Extract feed
        feed = payload.get("feed", [])
        if not feed:
            logger.warning(f"No news articles returned for {ticker_upper}")
            return []
        
        logger.info(f"[ALPHA VANTAGE] Retrieved {len(feed)} raw articles for {ticker_upper}")
        
        # Normalize articles
        normalized = []
        for item in feed:
            try:
                norm_item = _normalize_alpha_vantage_item(ticker_upper, item)
                if norm_item["title"]:  # Only include items with titles
                    normalized.append(norm_item)
            except Exception as e:
                logger.warning(f"Failed to normalize Alpha Vantage item: {e}")
                continue
        
        # Save to cache
        if use_cache and normalized:
            try:
                cache_path.write_text(
                    json.dumps(normalized, indent=2, ensure_ascii=False),
                    encoding="utf-8"
                )
                logger.info(f"Saved {len(normalized)} articles to cache")
            except Exception as e:
                logger.warning(f"Failed to save cache: {e}")
        
        logger.info(f"[SUCCESS] {ticker_upper}: {len(normalized)} articles from Alpha Vantage")
        return normalized
        
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed: {e}")
        
        # Try to return cached data if available (even if expired)
        if cache_path.exists():
            try:
                cached_data = json.loads(cache_path.read_text(encoding="utf-8"))
                logger.warning(f"[FALLBACK] Using expired cache: {len(cached_data)} articles")
                return cached_data
            except Exception:
                pass
        
        raise RuntimeError(f"Failed to fetch Alpha Vantage news for {ticker_upper}: {e}")


def get_supported_tickers() -> list[str]:
    """
    Get list of supported tickers.
    
    Alpha Vantage supports a wide range of tickers, but we limit to the same
    whitelist used by other providers for consistency.
    
    Returns:
        List of supported ticker symbols
    """
    # Import from news_provider to maintain consistency
    from services.news_provider import SUPPORTED_TICKERS
    return list(SUPPORTED_TICKERS.keys())


def is_ticker_supported(ticker: str) -> bool:
    """Check if a ticker is supported."""
    return ticker.upper() in get_supported_tickers()


def clear_alpha_vantage_cache(ticker: Optional[str] = None) -> int:
    """
    Clear Alpha Vantage news cache.
    
    Args:
        ticker: Optional ticker to clear cache for (if None, clears all)
        
    Returns:
        Number of cache files deleted
    """
    if not NEWS_CACHE_DIR.exists():
        return 0
    
    count = 0
    if ticker:
        # Clear specific ticker
        pattern = f"{ticker.upper()}_alphavantage_*.json"
        for cache_file in NEWS_CACHE_DIR.glob(pattern):
            cache_file.unlink()
            count += 1
    else:
        # Clear all Alpha Vantage cache
        for cache_file in NEWS_CACHE_DIR.glob("*_alphavantage_*.json"):
            cache_file.unlink()
            count += 1
    
    return count
