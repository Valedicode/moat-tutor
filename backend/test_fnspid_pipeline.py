"""
Test script for the FNSPID news pipeline.

This script tests the pipeline with a small subset of data to verify:
1. CSV streaming works
2. Filtering by ticker and date
3. Article chunking
4. Passage storage (without embeddings for quick testing)

To run a full test with embeddings, set OPENAI_API_KEY and use --full flag.
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.fnspid_news_pipeline import (
    stream_fnspid_csv,
    filter_articles,
    chunk_article,
    save_passages_jsonl,
    load_passages_jsonl,
    SUPPORTED_TICKERS,
    run_pipeline,
)


def test_csv_streaming(max_rows: int = 100):
    """Test that CSV streaming works."""
    print("\n=== Testing CSV Streaming ===")
    
    rows = list(stream_fnspid_csv(max_rows=max_rows))
    
    # First row should be header
    assert rows[0][0] == '__header__', "First row should be header"
    print(f"Header detected: {rows[0][1]}")
    
    # Check we got some data rows
    data_rows = [r for r in rows if r[0] != '__header__']
    print(f"Retrieved {len(data_rows)} data rows")
    
    if data_rows:
        print(f"Sample row (first 3 fields): {data_rows[0][:3]}")
    
    return len(data_rows) > 0


def test_filtering(max_rows: int = 1000):
    """Test filtering by ticker and date."""
    print("\n=== Testing Filtering ===")
    
    # Just test with a couple tickers
    test_tickers = {"AAPL", "NVDA", "MSFT"}
    
    rows = stream_fnspid_csv(max_rows=max_rows)
    articles = list(filter_articles(
        rows,
        tickers=test_tickers,
        start_date="2020-01-01",
        end_date="2023-12-31"
    ))
    
    print(f"Found {len(articles)} articles matching filters")
    
    if articles:
        print(f"\nSample article:")
        print(f"  Ticker: {articles[0].ticker}")
        print(f"  Date: {articles[0].date}")
        print(f"  Headline: {articles[0].headline[:80]}...")
    
    return True


def test_chunking():
    """Test article chunking."""
    print("\n=== Testing Chunking ===")
    
    from services.fnspid_news_pipeline import NewsArticle
    
    # Create a test article with long content
    long_content = " ".join(["This is a test sentence."] * 100)  # ~500 words
    
    article = NewsArticle(
        ticker="TEST",
        date="2023-01-01",
        headline="Test Headline",
        url="https://example.com/test",
        content=long_content,
        article_id="test123"
    )
    
    passages = chunk_article(article)
    
    print(f"Long article split into {len(passages)} passages")
    
    for i, p in enumerate(passages):
        words = len(p.passage_text.split())
        print(f"  Passage {i}: {words} words")
    
    # Test short article
    short_article = NewsArticle(
        ticker="TEST",
        date="2023-01-01",
        headline="Short Headline",
        url="https://example.com/short",
        content="This is a short article.",
        article_id="short123"
    )
    
    short_passages = chunk_article(short_article)
    print(f"Short article: {len(short_passages)} passage(s)")
    
    return len(passages) > 1 and len(short_passages) == 1


def test_storage():
    """Test passage storage."""
    print("\n=== Testing Storage ===")
    
    from services.fnspid_news_pipeline import NewsPassage, CACHE_DIR
    
    test_passages = [
        NewsPassage(
            passage_id="test_0",
            ticker="TEST",
            date="2023-01-01",
            headline="Test Headline",
            url="https://example.com",
            passage_text="This is test passage content.",
            article_id="test",
            chunk_index=0,
            total_chunks=1
        )
    ]
    
    # Save
    save_passages_jsonl("TEST", test_passages)
    
    # Load
    loaded = load_passages_jsonl("TEST")
    
    print(f"Saved {len(test_passages)} passages, loaded {len(loaded)}")
    
    # Verify
    assert len(loaded) == len(test_passages), "Count mismatch"
    assert loaded[0].passage_id == test_passages[0].passage_id, "ID mismatch"
    
    # Cleanup
    test_file = CACHE_DIR / "TEST.jsonl.gz"
    if test_file.exists():
        test_file.unlink()
        print("Cleaned up test file")
    
    return True


def test_full_pipeline(tickers: list, max_rows: int = 5000):
    """Test the full pipeline (requires OPENAI_API_KEY)."""
    print("\n=== Testing Full Pipeline ===")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set, skipping embedding test")
        print("Running pipeline without embeddings...")
        
        run_pipeline(
            tickers=tickers,
            start_date="2023-01-01",
            end_date="2023-12-31",
            generate_embeddings_flag=False,
            max_rows=max_rows
        )
    else:
        print("OPENAI_API_KEY found, running with embeddings...")
        
        run_pipeline(
            tickers=tickers,
            start_date="2023-01-01",
            end_date="2023-12-31",
            generate_embeddings_flag=True,
            max_rows=max_rows
        )
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Test FNSPID pipeline")
    parser.add_argument("--full", action="store_true", help="Run full pipeline test")
    parser.add_argument("--tickers", type=str, default="AAPL,NVDA", help="Tickers for full test")
    parser.add_argument("--max-rows", type=int, default=5000, help="Max rows for full test")
    
    args = parser.parse_args()
    
    print("FNSPID Pipeline Test Suite")
    print("=" * 50)
    
    # Basic tests
    tests = [
        ("CSV Streaming", lambda: test_csv_streaming()),
        ("Filtering", lambda: test_filtering()),
        ("Chunking", lambda: test_chunking()),
        ("Storage", lambda: test_storage()),
    ]
    
    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((name, passed))
            print(f"\n[{'PASS' if passed else 'FAIL'}] {name}")
        except Exception as e:
            results.append((name, False))
            print(f"\n[FAIL] {name}: {e}")
    
    # Full pipeline test if requested
    if args.full:
        tickers = [t.strip().upper() for t in args.tickers.split(',')]
        try:
            passed = test_full_pipeline(tickers, args.max_rows)
            results.append(("Full Pipeline", passed))
            print(f"\n[{'PASS' if passed else 'FAIL'}] Full Pipeline")
        except Exception as e:
            results.append(("Full Pipeline", False))
            print(f"\n[FAIL] Full Pipeline: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("Summary:")
    passed = sum(1 for _, p in results if p)
    total = len(results)
    print(f"  {passed}/{total} tests passed")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
