"""
News Data Provider

Fetches financial news articles from multiple sources:
1. yfinance (Yahoo Finance) - for recent news (last 30 days)
2. FNSPID dataset - for historical news (2015-2023)

Stores data as JSON files for reproducibility in research experiments.
Supports the same whitelist of tech companies as the price provider.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import yfinance as yf

# Import FNSPID retrieval for historical data
try:
    from services.fnspid_retrieval import (
        is_fnspid_data_available,
        get_relevant_news_passages,
        get_news_summary,
    )
    FNSPID_AVAILABLE = True
except ImportError:
    FNSPID_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# News storage directory
NEWS_DIR = Path(__file__).parent.parent / "data" / "news"

# Reuse the same whitelist from price provider for consistency
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
    "GOOGL": "Alphabet Inc. (Google)",
}

# Date range constraints
# Note: yfinance only provides recent news (typically last 30 days)
# Historical news from 2020-2024 is NOT available through yfinance
MIN_DATE = "2020-01-01"
MAX_DATE = "2026-12-31"  # Extended to capture current news

# Cache validity period (24 hours - news updates frequently)
CACHE_VALIDITY_HOURS = 24


def _get_news_file_path(ticker: str) -> Path:
    """Get the JSON file path for a ticker's news."""
    NEWS_DIR.mkdir(parents=True, exist_ok=True)
    return NEWS_DIR / f"{ticker.upper()}_news.json"


def _is_cache_valid(file_path: Path) -> bool:
    """Check if news file exists and is still valid (within cache period)."""
    if not file_path.exists():
        return False
    
    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    age = datetime.now() - mtime
    
    return age < timedelta(hours=CACHE_VALIDITY_HOURS)


def _load_news_from_file(file_path: Path) -> Optional[list[dict]]:
    """Load news articles from JSON file."""
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load news file {file_path}: {e}")
        return None


def _save_news_to_file(articles: list[dict], file_path: Path) -> None:
    """Save news articles to JSON file."""
    try:
        NEWS_DIR.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(articles)} articles to {file_path}")
    except Exception as e:
        logger.warning(f"Failed to save news file {file_path}: {e}")


def _parse_iso_date(iso_string: str) -> str:
    """Convert ISO date string to YYYY-MM-DD format."""
    if not iso_string:
        return ""
    try:
        # Handle ISO format like '2026-01-08T14:33:43Z'
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        try:
            # Fallback: try to parse just the date part
            return iso_string[:10] if len(iso_string) >= 10 else ""
        except Exception:
            return ""


def _unix_to_date(timestamp: int) -> str:
    """Convert UNIX timestamp to YYYY-MM-DD format."""
    try:
        return datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
    except Exception:
        return ""


def _normalize_news_item(ticker: str, item: dict) -> dict:
    """
    Normalize a yfinance news item to our standard format.
    
    Handles the nested structure where data is inside item['content'].
    
    Args:
        ticker: Stock ticker symbol
        item: Raw news item from yfinance (may have nested 'content' dict)
        
    Returns:
        Normalized dictionary with standard fields
    """
    # yfinance now returns nested structure: {'id': '...', 'content': {...}}
    # Extract the content dict if it exists
    content = item.get('content', item)  # Fallback to item itself if no 'content' key
    
    # Extract date - try multiple formats
    date = ""
    publish_time = 0
    
    # Try ISO date string first (new format)
    if 'pubDate' in content and content['pubDate']:
        date = _parse_iso_date(content['pubDate'])
    elif 'displayTime' in content and content['displayTime']:
        date = _parse_iso_date(content['displayTime'])
    # Fallback to UNIX timestamp (old format)
    elif 'providerPublishTime' in content:
        publish_time = content.get('providerPublishTime', 0)
        date = _unix_to_date(publish_time) if publish_time else ""
    elif 'providerPublishTime' in item:
        publish_time = item.get('providerPublishTime', 0)
        date = _unix_to_date(publish_time) if publish_time else ""
    
    # Extract summary
    summary = ""
    if content.get('summary'):
        summary = content['summary']
    elif content.get('description'):
        summary = content['description']
    
    # Extract publisher - may be nested
    publisher = ""
    if isinstance(content.get('provider'), dict):
        publisher = content['provider'].get('displayName', '')
    elif content.get('publisher'):
        publisher = content['publisher']
    
    # Extract URL - may be nested in canonicalUrl or clickThroughUrl
    url = ""
    if isinstance(content.get('canonicalUrl'), dict):
        url = content['canonicalUrl'].get('url', '')
    elif isinstance(content.get('clickThroughUrl'), dict):
        url = content['clickThroughUrl'].get('url', '')
    elif content.get('link'):
        url = content['link']
    elif content.get('url'):
        url = content['url']
    
    # Extract other fields
    title = content.get('title', '') or item.get('title', '')
    article_id = content.get('id', '') or item.get('id', '')
    content_type = content.get('contentType', '') or content.get('type', '')
    
    return {
        "ticker": ticker.upper(),
        "date": date,
        "title": title,
        "publisher": publisher,
        "summary": summary,
        "url": url,
        "uuid": article_id,
        "type": content_type,
        "providerPublishTime": publish_time,
        "pubDate": content.get('pubDate', ''),  # Keep original ISO date
    }


def _filter_by_date_range(
    articles: list[dict],
    start_date: str,
    end_date: str
) -> list[dict]:
    """
    Filter articles by date range.
    
    Args:
        articles: List of normalized news articles
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        Filtered list of articles within the date range
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        logger.warning(f"Invalid date format: {start_date} or {end_date}")
        return articles
    
    filtered = []
    for article in articles:
        if not article.get('date'):
            continue
        try:
            article_date = datetime.strptime(article['date'], "%Y-%m-%d")
            if start <= article_date <= end:
                filtered.append(article)
        except ValueError:
            continue
    
    return filtered


def fetch_company_news(
    ticker: str,
    start_date: str = MIN_DATE,
    end_date: str = MAX_DATE,
    use_cache: bool = True
) -> list[dict]:
    """
    Fetch financial news articles for a company from yfinance.
    
    Args:
        ticker: Stock ticker symbol (must be in whitelist)
        start_date: Start date in YYYY-MM-DD format (default: 2020-01-01)
        end_date: End date in YYYY-MM-DD format (default: 2025-12-31)
        use_cache: Whether to use cached data (default: True)
        
    Returns:
        List of normalized news article dictionaries with fields:
        - ticker: Stock ticker symbol
        - date: Publication date (YYYY-MM-DD)
        - title: Article headline
        - publisher: News source
        - summary: Article summary or content
        - url: Link to full article
        - uuid: Unique identifier
        - type: Article type
        - providerPublishTime: Original UNIX timestamp
        
    Raises:
        ValueError: If ticker is not in whitelist
    """
    ticker_upper = ticker.upper()
    
    # Validate ticker
    if ticker_upper not in SUPPORTED_TICKERS:
        available = ", ".join(sorted(SUPPORTED_TICKERS.keys()))
        raise ValueError(
            f"Ticker '{ticker}' not supported. Available tickers: {available}"
        )
    
    # Constrain date range
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        min_dt = datetime.strptime(MIN_DATE, "%Y-%m-%d")
        max_dt = datetime.strptime(MAX_DATE, "%Y-%m-%d")
        
        if start < min_dt:
            start_date = MIN_DATE
        if end > max_dt:
            end_date = MAX_DATE
    except ValueError as e:
        logger.warning(f"Date parsing error: {e}")
    
    file_path = _get_news_file_path(ticker_upper)
    
    # Check cache first
    if use_cache and _is_cache_valid(file_path):
        cached_articles = _load_news_from_file(file_path)
        if cached_articles is not None:
            # Filter by date range
            filtered = _filter_by_date_range(cached_articles, start_date, end_date)
            logger.info(f"[CACHE] Loaded {len(filtered)} articles for {ticker_upper} "
                       f"(from {len(cached_articles)} cached)")
            return filtered
    
    # Fetch from yfinance
    logger.info(f"[FETCH] Fetching news for {ticker_upper} from yfinance...")
    
    try:
        ticker_obj = yf.Ticker(ticker_upper)
        raw_news = ticker_obj.news
        
        if raw_news is None:
            raw_news = []
        
        logger.info(f"[YFINANCE] Retrieved {len(raw_news)} raw articles for {ticker_upper}")
        
        # Normalize all articles
        normalized_articles = []
        for item in raw_news:
            try:
                normalized = _normalize_news_item(ticker_upper, item)
                if normalized['title']:  # Only include articles with titles
                    normalized_articles.append(normalized)
            except Exception as e:
                logger.warning(f"Failed to normalize news item: {e}")
                continue
        
        # Sort by date (newest first)
        normalized_articles.sort(
            key=lambda x: x.get('providerPublishTime', 0),
            reverse=True
        )
        
        # Save all articles to cache (before date filtering)
        if use_cache:
            _save_news_to_file(normalized_articles, file_path)
        
        # Filter by date range for return
        filtered = _filter_by_date_range(normalized_articles, start_date, end_date)
        
        logger.info(f"[SUCCESS] {ticker_upper}: {len(filtered)} articles in date range "
                   f"({start_date} to {end_date})")
        
        return filtered
        
    except Exception as e:
        logger.error(f"Failed to fetch news for {ticker_upper}: {e}")
        
        # Try to return cached data if available (even if expired)
        cached_articles = _load_news_from_file(file_path)
        if cached_articles:
            filtered = _filter_by_date_range(cached_articles, start_date, end_date)
            logger.warning(f"[FALLBACK] Using expired cache: {len(filtered)} articles")
            return filtered
        
        return []


def fetch_all_company_news(
    start_date: str = MIN_DATE,
    end_date: str = MAX_DATE,
    use_cache: bool = True
) -> dict[str, list[dict]]:
    """
    Fetch news for all supported companies.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        use_cache: Whether to use cached data
        
    Returns:
        Dictionary mapping ticker to list of news articles
    """
    results = {}
    
    for ticker in SUPPORTED_TICKERS:
        try:
            articles = fetch_company_news(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                use_cache=use_cache
            )
            results[ticker] = articles
        except Exception as e:
            logger.error(f"Failed to fetch news for {ticker}: {e}")
            results[ticker] = []
    
    # Summary
    total_articles = sum(len(articles) for articles in results.values())
    logger.info(f"[SUMMARY] Fetched {total_articles} total articles for "
               f"{len(results)} companies")
    
    return results


def get_news_for_agent(
    ticker: str,
    start_date: str,
    end_date: str,
    query: Optional[str] = None
) -> str:
    """
    Get formatted news string for the MoatTutor agent.
    
    This function intelligently chooses between:
    - FNSPID historical data (2015-2023) for older date ranges
    - Alpha Vantage (2024-2025) for the gap year period
    - yfinance (recent 30 days) for current news
    
    Args:
        ticker: Stock ticker symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        query: Optional search query for semantic retrieval (FNSPID only)
        
    Returns:
        Formatted string containing news articles
    """
    ticker_upper = ticker.upper()
    
    # Determine which source to use based on date range
    try:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        return f"Error: Invalid date format. Use YYYY-MM-DD."
    
    # FNSPID is best for historical data (2015-2023)
    fnspid_cutoff = datetime(2023, 12, 31)
    alpha_vantage_start = datetime(2024, 1, 1)
    alpha_vantage_end = datetime(2025, 12, 31)
    
    is_historical = end_dt <= fnspid_cutoff
    # Check if date range overlaps with 2024-2025 gap period
    overlaps_gap_period = start_dt <= alpha_vantage_end and end_dt >= alpha_vantage_start
    
    # Try FNSPID for purely historical queries (2015-2023)
    if is_historical and FNSPID_AVAILABLE:
        if is_fnspid_data_available(ticker_upper):
            if query:
                # Semantic search with query
                return get_relevant_news_passages(
                    query=query,
                    ticker=ticker_upper,
                    start_date=start_date,
                    end_date=end_date,
                    top_k=10
                )
            else:
                # Return chronological summary
                return get_news_summary(
                    ticker=ticker_upper,
                    start_date=start_date,
                    end_date=end_date,
                    max_articles=20
                )
        else:
            # FNSPID data not yet downloaded
            logger.info(f"FNSPID data not available for {ticker_upper}, using yfinance")
    
    # Try Alpha Vantage if date range overlaps with 2024-2025
    if overlaps_gap_period and not is_historical:
        try:
            from services.alpha_vantage_provider import fetch_alpha_vantage_news
            
            # Constrain dates to Alpha Vantage coverage (2024-2025)
            av_start = max(start_dt, alpha_vantage_start).strftime("%Y-%m-%d")
            av_end = min(end_dt, alpha_vantage_end).strftime("%Y-%m-%d")
            
            articles = fetch_alpha_vantage_news(
                ticker=ticker_upper,
                start_date=av_start,
                end_date=av_end,
                use_cache=True
            )
            
            if articles:
                # Format articles for agent consumption
                lines = [f"News for {ticker_upper} from {av_start} to {av_end} (Alpha Vantage):\n"]
                
                for i, article in enumerate(articles, 1):
                    date = article.get('date', 'Unknown date')
                    title = article.get('title', 'No title')
                    publisher = article.get('publisher', 'Unknown source')
                    summary = article.get('summary', '')
                    topics = article.get('topics', [])
                    
                    lines.append(f"{i}. [{date}] {title}")
                    lines.append(f"   Source: {publisher}")
                    
                    # Include topics if available (helpful for 2024-2025 filtering)
                    if topics:
                        lines.append(f"   Topics: {', '.join(topics[:5])}")  # Limit to 5 topics
                    
                    if summary:
                        # Truncate long summaries
                        if len(summary) > 200:
                            summary = summary[:200] + "..."
                        lines.append(f"   Summary: {summary}")
                    lines.append("")
                
                return "\n".join(lines)
            
        except ImportError:
            logger.warning("Alpha Vantage provider not available")
        except Exception as e:
            logger.warning(f"Alpha Vantage fetch failed for {ticker_upper}, falling back to yfinance: {e}")
    
    # Fall back to yfinance for recent news or if other sources unavailable
    try:
        articles = fetch_company_news(ticker, start_date, end_date)
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error fetching news for {ticker}: {e}"
    
    if not articles:
        if is_historical and FNSPID_AVAILABLE:
            return (f"No news articles found for {ticker} between {start_date} and {end_date}.\n"
                    f"Historical news is available via FNSPID. Run the pipeline first:\n"
                    f"  python -m services.fnspid_news_pipeline --tickers {ticker}")
        else:
            return (f"No news articles found for {ticker} between {start_date} and {end_date}.\n"
                    f"Note: yfinance only provides recent news (typically last 30 days). "
                    f"Historical news may not be available.")
    
    # Format articles for agent consumption
    lines = [f"News for {ticker} from {start_date} to {end_date}:\n"]
    
    for i, article in enumerate(articles, 1):
        date = article.get('date', 'Unknown date')
        title = article.get('title', 'No title')
        publisher = article.get('publisher', 'Unknown source')
        summary = article.get('summary', '')
        
        lines.append(f"{i}. [{date}] {title}")
        lines.append(f"   Source: {publisher}")
        if summary:
            # Truncate long summaries
            if len(summary) > 200:
                summary = summary[:200] + "..."
            lines.append(f"   Summary: {summary}")
        lines.append("")
    
    return "\n".join(lines)


def get_supported_tickers() -> dict[str, str]:
    """Get dictionary of supported tickers and company names."""
    return SUPPORTED_TICKERS.copy()


def is_ticker_supported(ticker: str) -> bool:
    """Check if a ticker is in the whitelist."""
    return ticker.upper() in SUPPORTED_TICKERS


def clear_news_cache(ticker: Optional[str] = None) -> int:
    """
    Clear cached news data.
    
    Args:
        ticker: Optional ticker to clear cache for (if None, clears all)
        
    Returns:
        Number of cache files deleted
    """
    if not NEWS_DIR.exists():
        return 0
    
    count = 0
    if ticker:
        file_path = _get_news_file_path(ticker)
        if file_path.exists():
            file_path.unlink()
            count = 1
    else:
        for news_file in NEWS_DIR.glob("*_news.json"):
            news_file.unlink()
            count += 1
    
    return count


def get_news_cache_info() -> dict:
    """Get information about cached news files."""
    if not NEWS_DIR.exists():
        return {"news_dir": str(NEWS_DIR), "files": [], "total_articles": 0}
    
    files = []
    total_articles = 0
    
    for news_file in NEWS_DIR.glob("*_news.json"):
        try:
            mtime = datetime.fromtimestamp(news_file.stat().st_mtime)
            age = datetime.now() - mtime
            
            articles = _load_news_from_file(news_file)
            article_count = len(articles) if articles else 0
            total_articles += article_count
            
            files.append({
                "filename": news_file.name,
                "ticker": news_file.stem.replace("_news", ""),
                "article_count": article_count,
                "modified": mtime.isoformat(),
                "age_hours": round(age.total_seconds() / 3600, 1),
                "valid": age < timedelta(hours=CACHE_VALIDITY_HOURS)
            })
        except Exception as e:
            logger.warning(f"Error reading cache info for {news_file}: {e}")
    
    return {
        "news_dir": str(NEWS_DIR),
        "files": sorted(files, key=lambda x: x["modified"], reverse=True),
        "total_articles": total_articles,
        "validity_hours": CACHE_VALIDITY_HOURS
    }
