"""
FNSPID News Pipeline

Streams and processes financial news from the Hugging Face FNSPID dataset:
https://huggingface.co/datasets/Zihan1004/FNSPID/resolve/main/Stock_news/nasdaq_exteral_data.csv

Features:
- Streaming CSV ingestion (no full download to disk)
- Filtering by ticker and date range
- Article chunking into passages (~200-400 tokens)
- OpenAI embedding generation with batching
- Per-ticker local storage (JSONL + numpy embeddings)
- Retrieval API for the MoatTutor agent
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import logging
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

import numpy as np
import requests
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

# FNSPID dataset URL
FNSPID_CSV_URL = "https://huggingface.co/datasets/Zihan1004/FNSPID/resolve/main/Stock_news/nasdaq_exteral_data.csv"

# Supported tickers (same as news_provider.py)
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
    "GOOG": "Alphabet Inc. (Google)",  # Alternative ticker
}

# Date range for historical data
MIN_DATE = "2015-01-01"
MAX_DATE = "2023-12-31"

# Chunking configuration
MIN_CHUNK_WORDS = 150   # Minimum words per chunk
MAX_CHUNK_WORDS = 350   # Maximum words per chunk (~200-400 tokens)
OVERLAP_WORDS = 50      # Overlap between chunks for context

# Embedding configuration
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536  # Default for text-embedding-3-small
EMBEDDING_BATCH_SIZE = 64    # Batch size for API calls

# Storage paths
DATA_DIR = Path(__file__).parent.parent / "data"
CACHE_DIR = DATA_DIR / "fnspid_cache"
EMBEDDINGS_DIR = DATA_DIR / "fnspid_embeddings"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class NewsArticle:
    """Represents a raw news article from the FNSPID dataset."""
    ticker: str
    date: str
    headline: str
    url: str
    content: str
    article_id: str


@dataclass
class NewsPassage:
    """Represents a chunked passage from an article."""
    passage_id: str
    ticker: str
    date: str
    headline: str
    url: str
    passage_text: str
    article_id: str
    chunk_index: int
    total_chunks: int


# ============================================================================
# CSV Column Detection
# ============================================================================

def detect_csv_columns(header_line: str) -> dict[str, int]:
    """
    Detect CSV column indices from header line.
    
    Returns a mapping of logical field names to column indices.
    """
    # Clean and parse header
    columns = [col.strip().strip('"').lower() for col in header_line.split(',')]
    
    # Known column name variations in FNSPID dataset
    column_mappings = {
        'ticker': ['ticker', 'symbol', 'stock', 'stock_symbol'],
        'date': ['date', 'published_date', 'publish_date', 'pub_date', 'timestamp'],
        'headline': ['headline', 'title', 'head', 'heading', 'article_title'],
        'url': ['url', 'link', 'source_url', 'article_url'],
        'content': ['content', 'article', 'text', 'body', 'article_content', 'article_text'],
    }
    
    detected = {}
    for field, variations in column_mappings.items():
        for i, col in enumerate(columns):
            if col in variations:
                detected[field] = i
                break
    
    logger.info(f"Detected columns: {detected}")
    logger.info(f"Raw header columns: {columns}")
    
    return detected


# ============================================================================
# Streaming CSV Parser
# ============================================================================

def stream_fnspid_csv(
    url: str = FNSPID_CSV_URL,
    chunk_size: int = 8192,
    max_rows: Optional[int] = None,
    max_retries: int = 3,
    retry_delay: int = 5
) -> Generator[list[str], None, None]:
    """
    Stream the FNSPID CSV file from Hugging Face.
    
    Yields rows as lists of strings.
    Does not download the entire file to disk.
    Uses Python's csv module to properly handle multi-line quoted fields.
    Includes retry logic for network failures.
    
    Args:
        url: URL of the CSV file
        chunk_size: Size of chunks to read
        max_rows: Maximum rows to process (None for all)
        max_retries: Maximum number of retry attempts on connection failure
        retry_delay: Seconds to wait between retries
        
    Yields:
        List of field values for each row
    """
    logger.info(f"Streaming CSV from {url}")
    
    # Increase CSV field size limit for large article content
    csv.field_size_limit(10 * 1024 * 1024)  # 10MB limit
    
    row_count = 0
    is_header = True
    columns = None
    
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                logger.warning(f"Retry attempt {attempt}/{max_retries} after {retry_delay}s delay...")
                import time
                time.sleep(retry_delay)
            
            # Use longer timeout for large files (10 minutes)
            # Also set read timeout separately
            response = requests.get(
                url, 
                stream=True, 
                timeout=(30, 600)  # (connect timeout, read timeout) - 10 min read timeout
            )
            response.raise_for_status()
            
            # Wrap the streaming response in a text iterator
            lines_iterator = response.iter_lines(decode_unicode=True)
            
            # Use csv.reader to properly handle quoted fields with newlines
            csv_reader = csv.reader(lines_iterator)
            
            for fields in csv_reader:
                if not fields or all(f == '' for f in fields):
                    continue
                
                if is_header:
                    is_header = False
                    # Parse header to get column indices
                    header_line = ','.join(fields)
                    columns = detect_csv_columns(header_line)
                    yield ['__header__', json.dumps(columns)]
                    continue
                
                yield fields
                
                row_count += 1
                if max_rows and row_count >= max_rows:
                    logger.info(f"Reached max_rows limit: {max_rows}")
                    return
                
                if row_count % 10000 == 0:
                    logger.info(f"Processed {row_count:,} rows...")
            
            # Successfully completed
            logger.info(f"Finished streaming. Total rows: {row_count:,}")
            return
            
        except (requests.exceptions.ChunkedEncodingError, 
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException) as e:
            if attempt < max_retries:
                logger.warning(f"Connection error at row {row_count:,}: {e}")
                logger.info(f"Will retry... (attempt {attempt + 1}/{max_retries})")
                # Reset header flag for retry (we'll get header again)
                is_header = True
                continue
            else:
                logger.error(f"Failed after {max_retries} retries. Last error: {e}")
                logger.error(f"Processed {row_count:,} rows before failure.")
                raise


def parse_csv_line(line: str) -> list[str]:
    """
    Parse a CSV line handling quoted fields with commas.
    
    Args:
        line: A single CSV line
        
    Returns:
        List of field values
    """
    fields = []
    current_field = ""
    in_quotes = False
    
    for char in line:
        if char == '"':
            in_quotes = not in_quotes
        elif char == ',' and not in_quotes:
            fields.append(current_field.strip().strip('"'))
            current_field = ""
        else:
            current_field += char
    
    # Don't forget the last field
    fields.append(current_field.strip().strip('"'))
    
    return fields


# ============================================================================
# Filtering and Deduplication
# ============================================================================

def filter_articles(
    rows: Generator[list[str], None, None],
    tickers: set[str],
    start_date: str = MIN_DATE,
    end_date: str = MAX_DATE
) -> Generator[NewsArticle, None, None]:
    """
    Filter articles by ticker and date range.
    Deduplicates by URL.
    Skips stock price rows early (only processes news rows).
    
    Args:
        rows: Generator of CSV rows
        tickers: Set of uppercase ticker symbols to keep
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Yields:
        NewsArticle objects for matching rows
    """
    seen_urls = set()
    columns = None
    kept = 0
    skipped = 0
    skip_reasons = {
        'no_columns': 0,
        'row_too_short': 0,
        'not_news_row': 0,
        'date_parse_failed': 0,
        'ticker_not_match': 0,
        'date_out_of_range': 0,
        'duplicate_url': 0,
        'parse_error': 0,
    }
    
    for row in rows:
        # Handle header row
        if row[0] == '__header__':
            columns = json.loads(row[1])
            continue
        
        if columns is None:
            skip_reasons['no_columns'] += 1
            skipped += 1
            continue
        
        try:
            # Extract field indices
            ticker_idx = columns.get('ticker')
            date_idx = columns.get('date')
            headline_idx = columns.get('headline')
            url_idx = columns.get('url')
            content_idx = columns.get('content')
            
            # Check if required columns are detected
            if ticker_idx is None or date_idx is None or url_idx is None:
                skip_reasons['no_columns'] += 1
                skipped += 1
                continue
            
            # Use detected indices or fallback
            if headline_idx is None:
                headline_idx = 2  # Fallback based on known structure
            
            if len(row) <= max(ticker_idx, date_idx, headline_idx, url_idx, content_idx or 0):
                skip_reasons['row_too_short'] += 1
                skipped += 1
                continue
            
            # EARLY CHECK: Skip stock price rows (they don't have URL/headline/content)
            # This is the most important optimization - skips ~29.7M stock price rows
            url = row[url_idx].strip() if url_idx < len(row) else ""
            headline = row[headline_idx].strip() if headline_idx < len(row) else ""
            content = row[content_idx].strip() if content_idx and content_idx < len(row) else ""
            
            # If no URL and no content/headline, it's likely a stock price row - skip early
            if not url and (not content or not headline):
                skip_reasons['not_news_row'] += 1
                skipped += 1
                continue
            
            # Now process as news row
            ticker = row[ticker_idx].upper().strip()
            date_raw = row[date_idx].strip()
            
            # Normalize date to YYYY-MM-DD
            date = normalize_date(date_raw)
            if not date:
                skip_reasons['date_parse_failed'] += 1
                skipped += 1
                continue
            
            # Filter by ticker
            if ticker not in tickers:
                skip_reasons['ticker_not_match'] += 1
                skipped += 1
                continue
            
            # Filter by date range
            if not (start_date <= date <= end_date):
                skip_reasons['date_out_of_range'] += 1
                skipped += 1
                continue
            
            # Deduplicate by URL
            if url in seen_urls:
                skip_reasons['duplicate_url'] += 1
                skipped += 1
                continue
            seen_urls.add(url)
            
            # Generate article ID
            article_id = generate_article_id(ticker, date, url)
            
            # Yield article
            article = NewsArticle(
                ticker=ticker,
                date=date,
                headline=headline,
                url=url,
                content=content,
                article_id=article_id
            )
            
            kept += 1
            
            # Log progress periodically
            if kept % 100 == 0 and kept > 0:
                logger.info(f"Progress: Kept {kept} articles so far...")
            
            yield article
            
        except Exception as e:
            skip_reasons['parse_error'] += 1
            logger.warning(f"Error parsing row: {e}")
            skipped += 1
            continue
    
    logger.info(f"Filtering complete. Kept: {kept:,}, Skipped: {skipped:,}")
    logger.info(f"Skip reasons breakdown: {skip_reasons}")


def normalize_date(date_str: str) -> Optional[str]:
    """
    Normalize date string to YYYY-MM-DD format.
    
    Args:
        date_str: Date in various formats
        
    Returns:
        Date in YYYY-MM-DD format, or None if unparseable
    """
    if not date_str:
        return None
    
    # Remove UTC suffix if present (common in FNSPID dataset)
    date_str = date_str.replace(' UTC', '').strip()
    
    # Common date formats in financial news
    formats = [
        "%Y-%m-%d",           # 2023-01-15
        "%Y/%m/%d",           # 2023/01/15
        "%m/%d/%Y",           # 01/15/2023
        "%d/%m/%Y",           # 15/01/2023
        "%B %d, %Y",          # January 15, 2023
        "%b %d, %Y",          # Jan 15, 2023
        "%Y-%m-%dT%H:%M:%S",  # ISO format
        "%Y-%m-%d %H:%M:%S",  # SQL format (handles "2023-12-16 23:00:00")
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # Try to extract date from beginning
    match = re.match(r'(\d{4})-(\d{2})-(\d{2})', date_str)
    if match:
        return match.group(0)
    
    return None


def generate_article_id(ticker: str, date: str, url: str) -> str:
    """Generate a unique article ID."""
    content = f"{ticker}:{date}:{url}"
    return hashlib.md5(content.encode()).hexdigest()[:16]


# ============================================================================
# Chunking
# ============================================================================

def chunk_article(article: NewsArticle) -> list[NewsPassage]:
    """
    Break an article into passages of approximately 200-400 tokens.
    
    Uses word count as a proxy for token count (roughly 1.3 tokens per word).
    
    Args:
        article: NewsArticle to chunk
        
    Returns:
        List of NewsPassage objects
    """
    # Combine headline and content for chunking
    full_text = f"{article.headline}\n\n{article.content}".strip()
    
    if not full_text:
        return []
    
    words = full_text.split()
    total_words = len(words)
    
    # If article is short enough, return as single passage
    if total_words <= MAX_CHUNK_WORDS:
        return [NewsPassage(
            passage_id=f"{article.article_id}_0",
            ticker=article.ticker,
            date=article.date,
            headline=article.headline,
            url=article.url,
            passage_text=full_text,
            article_id=article.article_id,
            chunk_index=0,
            total_chunks=1
        )]
    
    # Split into overlapping chunks
    passages = []
    chunk_index = 0
    start = 0
    
    while start < total_words:
        # Calculate end position
        end = min(start + MAX_CHUNK_WORDS, total_words)
        
        # Try to break at sentence boundary
        chunk_words = words[start:end]
        chunk_text = ' '.join(chunk_words)
        
        # Find last sentence boundary in chunk
        if end < total_words:
            # Look for sentence-ending punctuation
            for i in range(len(chunk_text) - 1, max(0, len(chunk_text) - 100), -1):
                if chunk_text[i] in '.!?' and i + 1 < len(chunk_text) and chunk_text[i + 1] == ' ':
                    chunk_text = chunk_text[:i + 1]
                    break
        
        passages.append(NewsPassage(
            passage_id=f"{article.article_id}_{chunk_index}",
            ticker=article.ticker,
            date=article.date,
            headline=article.headline,
            url=article.url,
            passage_text=chunk_text.strip(),
            article_id=article.article_id,
            chunk_index=chunk_index,
            total_chunks=0  # Will be updated later
        ))
        
        chunk_index += 1
        
        # Move start with overlap
        words_used = len(chunk_text.split())
        start += max(words_used - OVERLAP_WORDS, MIN_CHUNK_WORDS)
    
    # Update total_chunks
    total_chunks = len(passages)
    for p in passages:
        p.total_chunks = total_chunks
    
    return passages


def process_articles_to_passages(
    articles: Generator[NewsArticle, None, None]
) -> Generator[NewsPassage, None, None]:
    """
    Process articles into passages.
    
    Args:
        articles: Generator of NewsArticle objects
        
    Yields:
        NewsPassage objects
    """
    for article in articles:
        passages = chunk_article(article)
        for passage in passages:
            yield passage


# ============================================================================
# OpenAI Embeddings
# ============================================================================

def get_openai_client() -> OpenAI:
    """Get OpenAI client with API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=api_key)


def generate_embeddings(
    texts: list[str],
    model: str = EMBEDDING_MODEL,
    batch_size: int = EMBEDDING_BATCH_SIZE
) -> np.ndarray:
    """
    Generate embeddings for a list of texts using OpenAI.
    
    Includes rate limiting to avoid 429 errors by adding delays between batches.
    
    Args:
        texts: List of text strings to embed
        model: Embedding model name
        batch_size: Batch size for API calls
        
    Returns:
        Numpy array of embeddings (n_texts x dimensions)
    """
    import time
    
    client = get_openai_client()
    embeddings = []
    total_batches = (len(texts) + batch_size - 1) // batch_size
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_num = i // batch_size + 1
        
        logger.info(f"Generating embeddings for batch {batch_num}/{total_batches} "
                   f"({len(batch)} texts)")
        
        response = client.embeddings.create(
            model=model,
            input=batch
        )
        
        batch_embeddings = [item.embedding for item in response.data]
        embeddings.extend(batch_embeddings)
        
        # Add small delay between batches to avoid hitting rate limits
        # This reduces 429 errors significantly
        if i + batch_size < len(texts):  # Don't delay after last batch
            time.sleep(0.2)  # 200ms delay between batches
    
    return np.array(embeddings, dtype=np.float32)


# ============================================================================
# Storage
# ============================================================================

def ensure_directories():
    """Create storage directories if they don't exist."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)


def save_passages_jsonl(ticker: str, passages: list[NewsPassage]):
    """
    Save passages to a gzipped JSONL file.
    
    Args:
        ticker: Ticker symbol
        passages: List of NewsPassage objects
    """
    ensure_directories()
    file_path = CACHE_DIR / f"{ticker}.jsonl.gz"
    
    with gzip.open(file_path, 'wt', encoding='utf-8') as f:
        for passage in passages:
            f.write(json.dumps(asdict(passage)) + '\n')
    
    logger.info(f"Saved {len(passages)} passages to {file_path}")


def load_passages_jsonl(ticker: str) -> list[NewsPassage]:
    """
    Load passages from a gzipped JSONL file.
    
    Args:
        ticker: Ticker symbol
        
    Returns:
        List of NewsPassage objects
    """
    file_path = CACHE_DIR / f"{ticker}.jsonl.gz"
    
    if not file_path.exists():
        return []
    
    passages = []
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            passages.append(NewsPassage(**data))
    
    return passages


def save_embeddings(ticker: str, embeddings: np.ndarray, passage_ids: list[str]):
    """
    Save embeddings and passage IDs for a ticker.
    
    Args:
        ticker: Ticker symbol
        embeddings: Numpy array of embeddings
        passage_ids: List of passage IDs corresponding to embeddings
    """
    ensure_directories()
    
    # Save embeddings as .npy
    npy_path = EMBEDDINGS_DIR / f"{ticker}.npy"
    np.save(npy_path, embeddings)
    
    # Save passage IDs as .ids (JSON)
    ids_path = EMBEDDINGS_DIR / f"{ticker}.ids"
    with open(ids_path, 'w') as f:
        json.dump(passage_ids, f)
    
    logger.info(f"Saved {len(passage_ids)} embeddings to {npy_path}")


def load_embeddings(ticker: str) -> tuple[np.ndarray, list[str]]:
    """
    Load embeddings and passage IDs for a ticker.
    
    Args:
        ticker: Ticker symbol
        
    Returns:
        Tuple of (embeddings array, passage_ids list)
    """
    npy_path = EMBEDDINGS_DIR / f"{ticker}.npy"
    ids_path = EMBEDDINGS_DIR / f"{ticker}.ids"
    
    if not npy_path.exists() or not ids_path.exists():
        return np.array([]), []
    
    embeddings = np.load(npy_path)
    with open(ids_path, 'r') as f:
        passage_ids = json.load(f)
    
    return embeddings, passage_ids


# ============================================================================
# Retrieval
# ============================================================================

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between a query vector and multiple vectors.
    
    Args:
        a: Query vector (d,)
        b: Matrix of vectors (n, d)
        
    Returns:
        Array of similarity scores (n,)
    """
    # Normalize
    a_norm = a / np.linalg.norm(a)
    b_norm = b / np.linalg.norm(b, axis=1, keepdims=True)
    
    return np.dot(b_norm, a_norm)


def retrieve_passages(
    query: str,
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    top_k: int = 5
) -> list[dict]:
    """
    Retrieve top-k relevant passages for a query.
    
    Args:
        query: Search query text
        ticker: Ticker symbol to search
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        top_k: Number of passages to return
        
    Returns:
        List of passage dictionaries with similarity scores
    """
    ticker = ticker.upper()
    
    # Load passages and embeddings
    passages = load_passages_jsonl(ticker)
    embeddings, passage_ids = load_embeddings(ticker)
    
    if not passages or len(embeddings) == 0:
        logger.warning(f"No data available for ticker {ticker}")
        return []
    
    # Create passage lookup
    passage_map = {p.passage_id: p for p in passages}
    
    # Filter by date range if specified
    valid_indices = []
    for i, pid in enumerate(passage_ids):
        if pid not in passage_map:
            continue
        passage = passage_map[pid]
        
        if start_date and passage.date < start_date:
            continue
        if end_date and passage.date > end_date:
            continue
        
        valid_indices.append(i)
    
    if not valid_indices:
        logger.warning(f"No passages found in date range for {ticker}")
        return []
    
    # Filter embeddings
    filtered_embeddings = embeddings[valid_indices]
    filtered_ids = [passage_ids[i] for i in valid_indices]
    
    # Generate query embedding
    client = get_openai_client()
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[query]
    )
    query_embedding = np.array(response.data[0].embedding, dtype=np.float32)
    
    # Compute similarities
    similarities = cosine_similarity(query_embedding, filtered_embeddings)
    
    # Get top-k indices
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    # Build results
    results = []
    for idx in top_indices:
        pid = filtered_ids[idx]
        passage = passage_map[pid]
        results.append({
            "passage_id": passage.passage_id,
            "ticker": passage.ticker,
            "date": passage.date,
            "headline": passage.headline,
            "url": passage.url,
            "passage_text": passage.passage_text,
            "similarity": float(similarities[idx])
        })
    
    return results


# ============================================================================
# Pipeline Execution
# ============================================================================

def run_pipeline(
    tickers: Optional[list[str]] = None,
    start_date: str = MIN_DATE,
    end_date: str = MAX_DATE,
    generate_embeddings_flag: bool = True,
    max_rows: Optional[int] = None
):
    """
    Run the full FNSPID news pipeline.
    
    Args:
        tickers: List of tickers to process (default: all supported)
        start_date: Start date for filtering
        end_date: End date for filtering
        generate_embeddings_flag: Whether to generate embeddings
        max_rows: Maximum rows to process from CSV (for testing)
    """
    if tickers is None:
        tickers = list(SUPPORTED_TICKERS.keys())
    
    ticker_set = {t.upper() for t in tickers}
    
    logger.info(f"Starting FNSPID pipeline")
    logger.info(f"Tickers: {', '.join(sorted(ticker_set))}")
    logger.info(f"Date range: {start_date} to {end_date}")
    
    # Collect passages by ticker
    passages_by_ticker: dict[str, list[NewsPassage]] = {t: [] for t in ticker_set}
    
    # Stream and process
    rows = stream_fnspid_csv(max_rows=max_rows)
    articles = filter_articles(rows, ticker_set, start_date, end_date)
    
    article_count = 0
    for article in articles:
        passages = chunk_article(article)
        passages_by_ticker[article.ticker].extend(passages)
        article_count += 1
        
        if article_count % 1000 == 0:
            logger.info(f"Processed {article_count:,} articles...")
    
    logger.info(f"Total articles processed: {article_count:,}")
    
    # Save passages and generate embeddings
    for ticker, passages in passages_by_ticker.items():
        if not passages:
            logger.info(f"No passages for {ticker}")
            continue
        
        logger.info(f"{ticker}: {len(passages)} passages")
        
        # Save passages
        save_passages_jsonl(ticker, passages)
        
        # Generate embeddings
        if generate_embeddings_flag:
            # Check if embeddings already exist
            npy_path = EMBEDDINGS_DIR / f"{ticker}.npy"
            ids_path = EMBEDDINGS_DIR / f"{ticker}.ids"
            
            if npy_path.exists() and ids_path.exists():
                logger.info(f"{ticker}: Embeddings already exist, skipping generation")
                logger.info(f"  To regenerate, delete: {npy_path} and {ids_path}")
                continue
            
            texts = [p.passage_text for p in passages]
            passage_ids = [p.passage_id for p in passages]
            
            logger.info(f"Generating embeddings for {ticker}...")
            embeddings = generate_embeddings(texts)
            save_embeddings(ticker, embeddings, passage_ids)
    
    logger.info("Pipeline complete!")


def run_pipeline_incremental(
    since_date: str,
    tickers: Optional[list[str]] = None
):
    """
    Run an incremental update, fetching only articles since a given date.
    
    Args:
        since_date: Fetch articles from this date onwards (YYYY-MM-DD)
        tickers: List of tickers to update (default: all supported)
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    logger.info(f"Incremental update from {since_date} to {today}")
    
    run_pipeline(
        tickers=tickers,
        start_date=since_date,
        end_date=today,
        generate_embeddings_flag=True
    )


# ============================================================================
# CLI Entry Point
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="FNSPID News Pipeline")
    parser.add_argument(
        "--tickers",
        type=str,
        help="Comma-separated list of tickers (default: all supported)"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=MIN_DATE,
        help=f"Start date (default: {MIN_DATE})"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=MAX_DATE,
        help=f"End date (default: {MAX_DATE})"
    )
    parser.add_argument(
        "--no-embeddings",
        action="store_true",
        help="Skip embedding generation"
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        help="Maximum rows to process (for testing)"
    )
    parser.add_argument(
        "--incremental",
        type=str,
        help="Run incremental update from this date"
    )
    
    args = parser.parse_args()
    
    tickers = None
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(',')]
    
    if args.incremental:
        run_pipeline_incremental(args.incremental, tickers)
    else:
        run_pipeline(
            tickers=tickers,
            start_date=args.start_date,
            end_date=args.end_date,
            generate_embeddings_flag=not args.no_embeddings,
            max_rows=args.max_rows
        )
