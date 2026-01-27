"""
Test script for real data-driven moat scores.

Tests the new moat scoring system with various companies.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.data_driven_moat_scorer import DataDrivenMoatScorer

def print_moat_score(ticker: str, score_data: dict):
    """Pretty print moat score results."""
    print(f"\n{'='*80}")
    print(f"MOAT ANALYSIS: {ticker}")
    print(f"{'='*80}")
    print(f"Overall Score: {score_data['overall_score']:.2f}/5.0")
    print(f"Rating: {score_data['rating']}")
    print(f"Confidence: {score_data['confidence']}")
    print(f"Trend: {score_data['trend']}")
    print(f"Time Range: {score_data['time_range']}")
    print(f"\nMoat Factors:")
    print(f"  Network Effects:      {score_data['factors']['network_effects']:.1f}")
    print(f"  Switching Costs:      {score_data['factors']['switching_costs']:.1f}")
    print(f"  Intangible Assets:    {score_data['factors']['intangible_assets']:.1f}")
    print(f"  Cost Advantages:      {score_data['factors']['cost_advantages']:.1f}")
    print(f"  Regulatory Barriers:  {score_data['factors']['regulatory_barriers']:.1f}")
    print(f"\nSummary:")
    print(f"  {score_data['summary']}")
    print(f"{'='*80}\n")


def test_moat_scores():
    """Test moat scoring for various companies."""
    print("=" * 80)
    print("TESTING DATA-DRIVEN MOAT SCORER")
    print("=" * 80)
    
    scorer = DataDrivenMoatScorer()
    
    # Test companies with FNSPID data
    companies_with_news = ['NVDA', 'AAPL', 'MSFT', 'GOOGL', 'AMD']
    
    # Test companies without FNSPID data
    companies_without_news = ['MU', 'AVGO', 'ORCL', 'CSCO', 'PLTR']
    
    print("\n" + "="*80)
    print("TESTING COMPANIES WITH HISTORICAL NEWS DATA (FNSPID)")
    print("="*80)
    
    for ticker in companies_with_news:
        try:
            score_data = scorer.calculate_moat_score(ticker)
            print_moat_score(ticker, score_data)
        except Exception as e:
            print(f"\nERROR testing {ticker}: {e}\n")
    
    print("\n" + "="*80)
    print("TESTING COMPANIES WITHOUT FNSPID (PRICE DATA ONLY)")
    print("="*80)
    
    for ticker in companies_without_news:
        try:
            score_data = scorer.calculate_moat_score(ticker)
            print_moat_score(ticker, score_data)
        except Exception as e:
            print(f"\nERROR testing {ticker}: {e}\n")
    
    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)
    print("\nKey findings:")
    print("- Companies should now have DIFFERENT scores based on real data")
    print("- Scores should reflect actual 2015-2025 performance")
    print("- No more generic '3.0' defaults for all companies")
    print("="*80)


if __name__ == "__main__":
    test_moat_scores()
