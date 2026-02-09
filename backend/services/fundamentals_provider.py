"""
Alpha Vantage Fundamental Data Provider

Fetches financial statements (income statement, balance sheet, cash flow) from Alpha Vantage.
Used to calculate ROIC, NOPAT, Invested Capital, and other fundamental metrics.

Supports disk caching to minimize API calls (free tier: 500 req/day, 5 req/min).
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
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
ALPHA_VANTAGE_BASE_URL = os.getenv(
    "ALPHA_VANTAGE_BASE_URL",
    "https://www.alphavantage.co/query"
)

# Cache directory
FUNDAMENTALS_CACHE_DIR = Path(__file__).parent.parent / "data" / "fundamentals"

# Cache validity period (90 days - fundamentals change quarterly)
CACHE_VALIDITY_DAYS = 90


def _get_cache_path(ticker: str, statement_type: str) -> Path:
    """Get the cache file path for a specific financial statement."""
    ticker_dir = FUNDAMENTALS_CACHE_DIR / ticker.upper()
    ticker_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{statement_type}.json"
    return ticker_dir / filename


def _is_cache_valid(cache_path: Path) -> bool:
    """Check if cache file exists and is still valid."""
    if not cache_path.exists():
        return False
    
    mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
    age = datetime.now() - mtime
    
    return age < timedelta(days=CACHE_VALIDITY_DAYS)


def _fetch_from_api(ticker: str, function: str) -> dict:
    """
    Fetch financial statement from Alpha Vantage API.
    
    Args:
        ticker: Stock ticker symbol
        function: Alpha Vantage function name (INCOME_STATEMENT, BALANCE_SHEET, CASH_FLOW)
        
    Returns:
        Raw API response as dictionary
        
    Raises:
        requests.RequestException: If API request fails
        ValueError: If API key is not configured
    """
    if not ALPHA_VANTAGE_API_KEY:
        raise ValueError(
            "ALPHA_VANTAGE_API_KEY not found in environment. "
            "Add it to backend/.env file."
        )
    
    params = {
        "function": function,
        "symbol": ticker.upper(),
        "apikey": ALPHA_VANTAGE_API_KEY
    }
    
    logger.info(f"Fetching {function} for {ticker.upper()} from Alpha Vantage")
    
    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if "Error Message" in data:
            raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
        
        if "Note" in data:
            # Rate limit hit
            raise ValueError(f"Alpha Vantage rate limit: {data['Note']}")
        
        if "Information" in data:
            # Typically means invalid API key or other info message
            logger.warning(f"Alpha Vantage info: {data['Information']}")
        
        logger.info(f"Successfully fetched {function} for {ticker.upper()}")
        return data
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching {function} for {ticker}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        raise


def fetch_income_statement(ticker: str, use_cache: bool = True) -> dict:
    """
    Fetch income statement data from Alpha Vantage.
    
    Args:
        ticker: Stock ticker symbol
        use_cache: Whether to use cached data (default: True)
        
    Returns:
        Income statement data dictionary with annual and quarterly reports
        
    Example response structure:
        {
            "symbol": "MU",
            "annualReports": [
                {
                    "fiscalDateEnding": "2023-08-31",
                    "reportedCurrency": "USD",
                    "totalRevenue": "27160000000",
                    "operatingIncome": "5430000000",
                    "netIncome": "4320000000",
                    "interestExpense": "320000000",
                    "incomeTaxExpense": "890000000"
                }
            ],
            "quarterlyReports": [...]
        }
    """
    cache_path = _get_cache_path(ticker, "income-statement")
    
    # Try cache first
    if use_cache and _is_cache_valid(cache_path):
        logger.info(f"Loading income statement for {ticker} from cache")
        with open(cache_path, "r") as f:
            return json.load(f)
    
    # Fetch from API
    data = _fetch_from_api(ticker, "INCOME_STATEMENT")
    
    # Save to cache
    with open(cache_path, "w") as f:
        json.dump(data, f, indent=2)
    
    return data


def fetch_balance_sheet(ticker: str, use_cache: bool = True) -> dict:
    """
    Fetch balance sheet data from Alpha Vantage.
    
    Args:
        ticker: Stock ticker symbol
        use_cache: Whether to use cached data (default: True)
        
    Returns:
        Balance sheet data dictionary with annual and quarterly reports
        
    Example response structure:
        {
            "symbol": "MU",
            "annualReports": [
                {
                    "fiscalDateEnding": "2023-08-31",
                    "reportedCurrency": "USD",
                    "totalAssets": "62000000000",
                    "totalShareholderEquity": "41000000000",
                    "totalLiabilities": "21000000000",
                    "currentLiabilities": "7000000000",
                    "cashAndCashEquivalentsAtCarryingValue": "8500000000",
                    "longTermDebt": "6000000000",
                    "shortTermDebt": "2000000000"
                }
            ],
            "quarterlyReports": [...]
        }
    """
    cache_path = _get_cache_path(ticker, "balance-sheet")
    
    # Try cache first
    if use_cache and _is_cache_valid(cache_path):
        logger.info(f"Loading balance sheet for {ticker} from cache")
        with open(cache_path, "r") as f:
            return json.load(f)
    
    # Fetch from API
    data = _fetch_from_api(ticker, "BALANCE_SHEET")
    
    # Save to cache
    with open(cache_path, "w") as f:
        json.dump(data, f, indent=2)
    
    return data


def fetch_cash_flow(ticker: str, use_cache: bool = True) -> dict:
    """
    Fetch cash flow statement data from Alpha Vantage.
    
    Args:
        ticker: Stock ticker symbol
        use_cache: Whether to use cached data (default: True)
        
    Returns:
        Cash flow statement data dictionary with annual and quarterly reports
        
    Example response structure:
        {
            "symbol": "MU",
            "annualReports": [
                {
                    "fiscalDateEnding": "2023-08-31",
                    "reportedCurrency": "USD",
                    "operatingCashflow": "9200000000",
                    "capitalExpenditures": "6500000000",
                    "cashflowFromInvestment": "-6500000000",
                    "cashflowFromFinancing": "-2300000000"
                }
            ],
            "quarterlyReports": [...]
        }
    """
    cache_path = _get_cache_path(ticker, "cash-flow")
    
    # Try cache first
    if use_cache and _is_cache_valid(cache_path):
        logger.info(f"Loading cash flow for {ticker} from cache")
        with open(cache_path, "r") as f:
            return json.load(f)
    
    # Fetch from API
    data = _fetch_from_api(ticker, "CASH_FLOW")
    
    # Save to cache
    with open(cache_path, "w") as f:
        json.dump(data, f, indent=2)
    
    return data


def get_fundamental_data(ticker: str, use_cache: bool = True) -> dict:
    """
    Fetch all fundamental data (income statement, balance sheet, cash flow) for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        use_cache: Whether to use cached data (default: True)
        
    Returns:
        Dictionary containing all three financial statements
        
    Example:
        {
            "ticker": "MU",
            "income_statement": {...},
            "balance_sheet": {...},
            "cash_flow": {...},
            "fetched_at": "2025-02-06T10:30:00"
        }
    """
    logger.info(f"Fetching all fundamental data for {ticker}")
    
    try:
        income_statement = fetch_income_statement(ticker, use_cache)
        balance_sheet = fetch_balance_sheet(ticker, use_cache)
        cash_flow = fetch_cash_flow(ticker, use_cache)
        
        return {
            "ticker": ticker.upper(),
            "income_statement": income_statement,
            "balance_sheet": balance_sheet,
            "cash_flow": cash_flow,
            "fetched_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch fundamental data for {ticker}: {e}")
        raise


def clear_cache(ticker: Optional[str] = None) -> None:
    """
    Clear cached fundamental data.
    
    Args:
        ticker: If provided, clear cache for specific ticker only.
                If None, clear all cached data.
    """
    if ticker:
        ticker_dir = FUNDAMENTALS_CACHE_DIR / ticker.upper()
        if ticker_dir.exists():
            for file in ticker_dir.glob("*.json"):
                file.unlink()
            logger.info(f"Cleared cache for {ticker}")
    else:
        if FUNDAMENTALS_CACHE_DIR.exists():
            for ticker_dir in FUNDAMENTALS_CACHE_DIR.iterdir():
                if ticker_dir.is_dir():
                    for file in ticker_dir.glob("*.json"):
                        file.unlink()
            logger.info("Cleared all fundamental data cache")


def is_ticker_supported(ticker: str) -> bool:
    """
    Check if a ticker is likely supported (US companies).
    
    Note: This is a heuristic check. The definitive way is to try fetching data.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        True if likely supported, False otherwise
    """
    # Alpha Vantage supports US-listed stocks
    # These are major tech tickers known to be available
    known_supported = {
        "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "AMD",
        "INTC", "CSCO", "ORCL", "AVGO", "MU", "QCOM", "TXN", "ADBE",
        "CRM", "IBM", "PLTR", "SNOW", "NET"
    }
    
    return ticker.upper() in known_supported
