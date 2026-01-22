"""Quick script to check FNSPID cache files."""

import gzip
import json
from pathlib import Path

cache_dir = Path("data/fnspid_cache")
tickers = ['AAPL', 'NVDA', 'MSFT', 'AMD', 'GOOGL', 'AVGO', 'ORCL', 'CSCO', 'MU', 'PLTR']

print("=" * 50)
print("FNSPID Cache Files Summary")
print("=" * 50)
print(f"{'Ticker':<8} | {'Passages':>10} | {'File Size':>12}")
print("-" * 50)

total_passages = 0
total_size = 0

for ticker in tickers:
    file_path = cache_dir / f"{ticker}.jsonl.gz"
    
    if file_path.exists():
        # Count passages
        count = 0
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            for line in f:
                count += 1
        
        size_mb = file_path.stat().st_size / (1024 * 1024)
        total_passages += count
        total_size += file_path.stat().st_size
        
        print(f"{ticker:<8} | {count:>10,} | {size_mb:>11.2f} MB")
    else:
        print(f"{ticker:<8} | {'MISSING':>10} | {'N/A':>12}")

print("-" * 50)
print(f"{'TOTAL':<8} | {total_passages:>10,} | {total_size/(1024*1024):>11.2f} MB")
print("=" * 50)

# Check a sample passage
print("\nSample passage from AAPL:")
if (cache_dir / "AAPL.jsonl.gz").exists():
    with gzip.open(cache_dir / "AAPL.jsonl.gz", 'rt', encoding='utf-8') as f:
        first_line = f.readline()
        if first_line:
            sample = json.loads(first_line)
            print(f"  Date: {sample.get('date')}")
            print(f"  Headline: {sample.get('headline', '')[:60]}...")
            print(f"  Passage text: {sample.get('passage_text', '')[:100]}...")
