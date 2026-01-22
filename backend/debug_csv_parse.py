"""
Debug CSV parsing to see why rows are too short.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.fnspid_news_pipeline import stream_fnspid_csv

def debug_csv():
    print("=== Debugging CSV Parsing ===\n")
    
    rows = list(stream_fnspid_csv(max_rows=50))
    
    # Get header
    header_row = rows[0]
    print(f"Header row: {header_row}\n")
    
    # Get data rows
    data_rows = [r for r in rows if r[0] != '__header__']
    
    print(f"Sample of {len(data_rows)} data rows:\n")
    
    # Show field counts
    field_counts = {}
    for row in data_rows:
        count = len(row)
        field_counts[count] = field_counts.get(count, 0) + 1
    
    print("Field count distribution:")
    for count, freq in sorted(field_counts.items()):
        print(f"  {count} fields: {freq} rows")
    
    # Show sample rows
    print("\n\nFirst 5 rows (showing first 8 fields):")
    for i, row in enumerate(data_rows[:5]):
        print(f"\nRow {i+1} ({len(row)} fields):")
        for j, field in enumerate(row[:8]):
            print(f"  [{j}] {repr(field[:60] if len(field) > 60 else field)}")

if __name__ == "__main__":
    debug_csv()
