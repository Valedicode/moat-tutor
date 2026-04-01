"""
Verify data availability for MOAT ETF technology sector tickers.

Checks:
1. Alpha Vantage fundamentals (INCOME_STATEMENT) -- fetches & caches if available
2. FNSPID historical news cache (local .jsonl.gz + .npy)
3. yfinance price data (quick 5-day download)

Usage (from backend/):
    python -m scripts.utils.verify_etf_tickers
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Ensure backend is on the path
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

from services.etf_holdings import MOAT_TECH_SECTORS, get_all_tech_tickers

# Tickers that already existed before the ETF expansion
PREVIOUSLY_SUPPORTED = {"NVDA", "AAPL", "MSFT", "AVGO", "ORCL", "AMD", "CSCO", "PLTR", "MU", "GOOGL"}


def check_alpha_vantage(ticker: str, fetch_all: bool = False) -> dict:
    """Check Alpha Vantage availability and optionally fetch+cache fundamentals."""
    from services.fundamentals_provider import (
        fetch_income_statement,
        _get_cache_path,
        _is_cache_valid,
    )

    result = {"ticker": ticker, "alpha_vantage": "unknown"}

    cache_path = _get_cache_path(ticker, "income-statement")
    if _is_cache_valid(cache_path):
        result["alpha_vantage"] = "cached"
        return result

    if not fetch_all:
        result["alpha_vantage"] = "not_cached"
        return result

    try:
        data = fetch_income_statement(ticker, use_cache=False)
        annual = data.get("annualReports", [])
        if annual:
            result["alpha_vantage"] = f"ok ({len(annual)} annual reports)"
        else:
            result["alpha_vantage"] = "empty_response"
    except Exception as e:
        result["alpha_vantage"] = f"error: {e}"

    return result


def check_fnspid(ticker: str) -> str:
    """Check if FNSPID cache files exist locally."""
    fnspid_cache = BACKEND_DIR / "data" / "fnspid_cache"
    fnspid_emb = BACKEND_DIR / "data" / "fnspid_embeddings"

    passages = fnspid_cache / f"{ticker.upper()}.jsonl.gz"
    embeddings = fnspid_emb / f"{ticker.upper()}.npy"
    ids_file = fnspid_emb / f"{ticker.upper()}.ids"

    if passages.exists() and embeddings.exists() and ids_file.exists():
        return "available"
    elif passages.exists():
        return "passages_only (no embeddings)"
    else:
        return "not_available"


def check_yfinance(ticker: str) -> str:
    """Quick check: can yfinance download recent data for this ticker?"""
    try:
        import yfinance as yf
        df = yf.download(ticker, period="5d", progress=False)
        if df.empty:
            return "no_data"
        return f"ok ({len(df)} rows)"
    except Exception as e:
        return f"error: {e}"


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Verify MOAT ETF ticker data availability")
    parser.add_argument("--fetch", action="store_true",
                        help="Actually fetch & cache Alpha Vantage fundamentals for new tickers")
    parser.add_argument("--only-new", action="store_true",
                        help="Only check tickers not previously in the system")
    args = parser.parse_args()

    all_tickers = get_all_tech_tickers()
    if args.only_new:
        all_tickers = [t for t in all_tickers if t not in PREVIOUSLY_SUPPORTED]

    print(f"\n{'='*70}")
    print(f"MOAT ETF Technology Sector -- Data Availability Check")
    print(f"Tickers to check: {len(all_tickers)}")
    print(f"Alpha Vantage fetch mode: {'ENABLED' if args.fetch else 'cache-only'}")
    print(f"{'='*70}\n")

    # Group by sub-sector for display
    ticker_to_sector = {}
    for sector, tickers in MOAT_TECH_SECTORS.items():
        for t in tickers:
            ticker_to_sector[t] = sector

    results = []

    for ticker in all_tickers:
        sector = ticker_to_sector.get(ticker, "?")
        is_new = ticker not in PREVIOUSLY_SUPPORTED

        print(f"  Checking {ticker:6s} ({'NEW' if is_new else 'existing':8s}) [{sector}]...")

        yf_status = check_yfinance(ticker)
        fnspid_status = check_fnspid(ticker)
        av_result = check_alpha_vantage(ticker, fetch_all=args.fetch and is_new)

        results.append({
            "ticker": ticker,
            "sector": sector,
            "new": is_new,
            "yfinance": yf_status,
            "fnspid": fnspid_status,
            "alpha_vantage": av_result["alpha_vantage"],
        })

        # Rate-limit Alpha Vantage (5 req/min on free tier)
        if args.fetch and is_new and "ok" in av_result["alpha_vantage"]:
            time.sleep(13)

    # Summary
    print(f"\n{'='*70}")
    print(f"{'TICKER':8s} {'NEW':5s} {'YFINANCE':18s} {'FNSPID':28s} {'ALPHA VANTAGE':30s}")
    print(f"{'-'*70}")
    for r in results:
        print(f"{r['ticker']:8s} {'Y' if r['new'] else 'N':5s} {r['yfinance']:18s} {r['fnspid']:28s} {r['alpha_vantage']:30s}")

    # Counts
    yf_ok = sum(1 for r in results if "ok" in r["yfinance"])
    fnspid_ok = sum(1 for r in results if r["fnspid"] == "available")
    av_ok = sum(1 for r in results if "ok" in r["alpha_vantage"] or r["alpha_vantage"] == "cached")

    print(f"\nSummary:")
    print(f"  yfinance:      {yf_ok}/{len(results)} available")
    print(f"  FNSPID:        {fnspid_ok}/{len(results)} available (NASDAQ-focused, NYSE tickers may be missing)")
    print(f"  Alpha Vantage: {av_ok}/{len(results)} available/cached")
    print()


if __name__ == "__main__":
    main()
