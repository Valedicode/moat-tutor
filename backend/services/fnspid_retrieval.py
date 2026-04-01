"""
FNSPID Retrieval Service

Provides a high-level interface for retrieving historical news passages
from the FNSPID dataset for use by the MoatTutor agent.

This module bridges the gap between the raw FNSPID pipeline and the
agent's need for context-aware news retrieval.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from services.fnspid_news_pipeline import (
    CACHE_DIR,
    EMBEDDINGS_DIR,
    SUPPORTED_TICKERS,
    load_passages_jsonl,
    load_embeddings,
    retrieve_passages,
)

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Data Availability Checks
# ============================================================================

def is_fnspid_data_available(ticker: str) -> bool:
    """
    Check if FNSPID data is available for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        True if both passages and embeddings exist
    """
    ticker = ticker.upper()
    
    passages_file = CACHE_DIR / f"{ticker}.jsonl.gz"
    embeddings_file = EMBEDDINGS_DIR / f"{ticker}.npy"
    ids_file = EMBEDDINGS_DIR / f"{ticker}.ids"
    
    return (
        passages_file.exists() and 
        embeddings_file.exists() and 
        ids_file.exists()
    )


def get_available_tickers() -> list[str]:
    """
    Get list of tickers with available FNSPID data.
    
    Returns:
        List of ticker symbols
    """
    available = []
    for ticker in SUPPORTED_TICKERS:
        if is_fnspid_data_available(ticker):
            available.append(ticker)
    return sorted(available)


def get_date_range(ticker: str) -> tuple[Optional[str], Optional[str]]:
    """
    Get the date range of available data for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Tuple of (min_date, max_date) or (None, None) if no data
    """
    ticker = ticker.upper()
    passages = load_passages_jsonl(ticker)
    
    if not passages:
        return None, None
    
    dates = [p.date for p in passages if p.date]
    if not dates:
        return None, None
    
    return min(dates), max(dates)


def get_passage_count(ticker: str) -> int:
    """
    Get the number of passages available for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Number of passages
    """
    passages = load_passages_jsonl(ticker.upper())
    return len(passages)


# ============================================================================
# Retrieval for Agent
# ============================================================================

def get_relevant_news_passages(
    query: str,
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    top_k: int = 5
) -> str:
    """
    Retrieve relevant historical news passages for the agent.
    
    This is the primary function for the MoatTutor agent to use
    when it needs historical news context.
    
    Args:
        query: Search query (e.g., "earnings report", "AI chip demand")
        ticker: Stock ticker symbol
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        top_k: Number of passages to return
        
    Returns:
        Formatted string with relevant passages and structured sources block
    """
    ticker = ticker.upper()
    
    # Check if data is available
    if not is_fnspid_data_available(ticker):
        return (f"No historical news data available for {ticker}. "
                f"Run the FNSPID pipeline first: python -m services.fnspid_news_pipeline --tickers {ticker}")
    
    try:
        results = retrieve_passages(
            query=query,
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            top_k=top_k
        )
    except Exception as e:
        logger.error(f"Error retrieving passages: {e}")
        return f"Error retrieving news passages: {e}"
    
    if not results:
        date_range = ""
        if start_date and end_date:
            date_range = f" between {start_date} and {end_date}"
        elif start_date:
            date_range = f" after {start_date}"
        elif end_date:
            date_range = f" before {end_date}"
        
        return f"No relevant news passages found for {ticker}{date_range} matching query: '{query}'"
    
    def _one_line(s: str) -> str:
        """Convert text to single line for display."""
        return (s or "").replace("\n", " ").replace("\r", " ").strip()
    
    SNIPPET_CHARS = 240
    
    # Format compact results with snippets
    lines = [f"Historical news signals for {ticker} (query: '{query}'):"]
    lines.append("")
    lines.append("Top matches (brief):")
    
    for i, result in enumerate(results, 1):
        snippet = _one_line(result.get("passage_text", ""))
        if len(snippet) > SNIPPET_CHARS:
            snippet = snippet[:SNIPPET_CHARS].rstrip() + "…"
        
        lines.append(f"- ({result['similarity']:.3f}) {result['date']}: {result['headline']}")
        if snippet:
            lines.append(f"  {snippet}")
        lines.append(f"  Source: {result['url']}")
        lines.append("")
    
    # Add machine-parsable sources block for frontend toggle
    lines.append("[SOURCES_START]")
    # Format: idx|date|headline|url|similarity|passage_id
    for i, result in enumerate(results, 1):
        headline = _one_line(result.get("headline", "")).replace("|", " ")
        url = _one_line(result.get("url", "")).replace("|", "%7C")
        lines.append(
            f"{i}|{result.get('date', '')}|{headline}|{url}|{result.get('similarity', 0.0):.3f}|{result.get('passage_id', '')}"
        )
    lines.append("[SOURCES_END]")
    
    return "\n".join(lines)


def get_news_summary(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_articles: int = 20
) -> str:
    """
    Get a summary of news articles for a ticker in a date range.
    
    Unlike retrieve_passages which uses semantic search, this returns
    a chronological list of headlines.
    
    Args:
        ticker: Stock ticker symbol
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        max_articles: Maximum articles to include
        
    Returns:
        Formatted string with article headlines
    """
    ticker = ticker.upper()
    
    if not is_fnspid_data_available(ticker):
        return f"No historical news data available for {ticker}."
    
    passages = load_passages_jsonl(ticker)
    
    # Filter by date and deduplicate by article
    seen_articles = set()
    filtered = []
    
    for p in passages:
        # Only include first chunk of each article
        if p.chunk_index != 0:
            continue
        
        if p.article_id in seen_articles:
            continue
        
        if start_date and p.date < start_date:
            continue
        if end_date and p.date > end_date:
            continue
        
        seen_articles.add(p.article_id)
        filtered.append(p)
    
    # Sort by date
    filtered.sort(key=lambda x: x.date, reverse=True)
    
    # Limit
    filtered = filtered[:max_articles]
    
    if not filtered:
        date_range = ""
        if start_date and end_date:
            date_range = f" between {start_date} and {end_date}"
        return f"No articles found for {ticker}{date_range}."
    
    # Format human-readable list
    lines = [f"News headlines for {ticker}:"]
    lines.append("")
    
    current_month = ""
    for p in filtered:
        month = p.date[:7]
        if month != current_month:
            current_month = month
            lines.append(f"\n## {month}")
        
        lines.append(f"- [{p.date}] {p.headline}")
    
    lines.append(f"\nTotal articles: {len(filtered)}")
    
    # Machine-parsable sources block for frontend
    lines.append("\n[SOURCES_START]")
    for i, p in enumerate(filtered, 1):
        headline = (p.headline or "").replace("|", " ").replace("\n", " ").strip()
        url = (p.url or "").replace("|", "%7C")
        lines.append(f"{i}|{p.date}|{headline}|{url}||{p.passage_id}")
    lines.append("[SOURCES_END]")
    
    return "\n".join(lines)


# ============================================================================
# Agent Tool Wrapper
# ============================================================================

def search_historical_news(
    ticker: str,
    query: str,
    start_date: str,
    end_date: str,
    top_k: int = 5
) -> str:
    """
    Search historical news for a ticker using semantic similarity.
    
    This function is designed to be used as an agent tool.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'NVDA')
        query: Search query describing what you're looking for
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        top_k: Number of results to return
        
    Returns:
        Formatted string containing relevant news passages
    """
    return get_relevant_news_passages(
        query=query,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        top_k=top_k
    )


def get_fnspid_status() -> str:
    """
    Get status of FNSPID data availability.
    
    Returns:
        Formatted status string
    """
    lines = ["FNSPID Historical News Data Status:"]
    lines.append("")
    
    for ticker, name in sorted(SUPPORTED_TICKERS.items()):
        if is_fnspid_data_available(ticker):
            min_date, max_date = get_date_range(ticker)
            count = get_passage_count(ticker)
            lines.append(f"  {ticker}: {count:,} passages ({min_date} to {max_date})")
        else:
            lines.append(f"  {ticker}: No data (run pipeline to download)")
    
    lines.append("")
    lines.append("Run pipeline with: python -m services.fnspid_news_pipeline")
    
    return "\n".join(lines)
