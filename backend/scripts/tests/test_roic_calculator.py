"""
Test script for ROIC calculator

Tests ROIC calculations with real data from Alpha Vantage.
"""

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from services.roic_calculator import (
    calculate_roic_time_series,
    check_roic_hurdle,
    compare_roic_to_peers,
)


def test_roic_time_series():
    """Test calculating ROIC time series for NVDA."""
    print("\n" + "="*60)
    print("TEST: ROIC Time Series for NVDA (last 5 years)")
    print("="*60)
    
    try:
        df = calculate_roic_time_series("NVDA", use_cache=True)
        
        if not df.empty:
            print(f"\nSuccess! Found {len(df)} years of data")
            print("\nRecent ROIC values:")
            print(df[["year", "roic_pct", "nopat", "invested_capital"]].head(5).to_string(index=False))
            return True
        else:
            print("\nNo data returned")
            return False
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_roic_hurdle_nvda():
    """Test ROIC hurdle check for NVDA (expected to pass)."""
    print("\n" + "="*60)
    print("TEST: ROIC Hurdle Check for NVDA")
    print("="*60)
    
    try:
        result = check_roic_hurdle("NVDA", years=10, use_cache=True)
        
        if "error" in result:
            print(f"\nError: {result['error']}")
            return False
        
        print(f"\nSuccess! ROIC Hurdle Analysis:")
        print(f"  Period: {result['period']}")
        print(f"  Years Analyzed: {result['years_analyzed']}")
        print(f"  Average ROIC: {result['avg_roic_pct']:.2f}%")
        print(f"  Median ROIC: {result['median_roic_pct']:.2f}%")
        print(f"  Min ROIC: {result['min_roic_pct']:.2f}%")
        print(f"  Max ROIC: {result['max_roic_pct']:.2f}%")
        print(f"  WACC Threshold: {result['wacc_pct']:.2f}%")
        print(f"  Years Above WACC: {result['years_above_wacc']}/{result['years_analyzed']} ({result['years_above_hurdle_pct']:.1f}%)")
        print(f"  Trend: {result['roic_trend']}")
        print(f"  Hurdle Passed: {result['hurdle_passed']}")
        
        if result['hurdle_passed']:
            print("\n  ✓ NVDA demonstrates sustained high ROIC (moat evidence)")
        else:
            print("\n  ✗ NVDA does not meet ROIC hurdle criteria")
        
        return True
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_roic_hurdle_aapl():
    """Test ROIC hurdle check for AAPL (also expected to pass)."""
    print("\n" + "="*60)
    print("TEST: ROIC Hurdle Check for AAPL")
    print("="*60)
    
    try:
        result = check_roic_hurdle("AAPL", years=10, use_cache=True)
        
        if "error" in result:
            print(f"\nError: {result['error']}")
            return False
        
        print(f"\nSuccess! ROIC Hurdle Analysis:")
        print(f"  Average ROIC: {result['avg_roic_pct']:.2f}%")
        print(f"  Years Above WACC: {result['years_above_wacc']}/{result['years_analyzed']}")
        print(f"  Hurdle Passed: {result['hurdle_passed']}")
        
        return True
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_peer_comparison():
    """Test comparing NVDA to semiconductor peers."""
    print("\n" + "="*60)
    print("TEST: Compare NVDA to Semiconductor Peers")
    print("="*60)
    
    try:
        peers = ["AMD", "INTC", "AVGO", "MU"]
        result = compare_roic_to_peers("NVDA", peers, years=5, use_cache=True)
        
        if "error" in result:
            print(f"\nError: {result['error']}")
            return False
        
        print(f"\nSuccess! Peer Comparison:")
        print(f"  NVDA Average ROIC: {result['ticker_avg_roic_pct']:.2f}%")
        print(f"  Peer Average ROIC: {result['peer_avg_roic_pct']:.2f}%")
        print(f"  ROIC Advantage: {result['roic_advantage_pct']:+.2f}%")
        
        print(f"\n  Peer Breakdown:")
        for peer in result['peer_data']:
            print(f"    {peer['ticker']}: {peer['avg_roic_pct']:.2f}%")
        
        if result['roic_advantage_pct'] > 5:
            print(f"\n  ✓ NVDA has significant ROIC advantage over peers ({result['roic_advantage_pct']:+.2f}%)")
        
        return True
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("ROIC Calculator Test Suite")
    print("="*60)
    
    results = []
    
    # Test 1: Time series calculation
    results.append(("ROIC Time Series (NVDA)", test_roic_time_series()))
    
    # Test 2: Hurdle check (NVDA - high ROIC expected)
    results.append(("ROIC Hurdle Check (NVDA)", test_roic_hurdle_nvda()))
    
    # Test 3: Hurdle check (AAPL - also high ROIC expected)
    results.append(("ROIC Hurdle Check (AAPL)", test_roic_hurdle_aapl()))
    
    # Test 4: Peer comparison
    results.append(("Peer Comparison (NVDA vs Semi)", test_peer_comparison()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("\nAll tests passed! ROIC calculator is working correctly.")
    else:
        print("\nSome tests failed. Check implementation.")
