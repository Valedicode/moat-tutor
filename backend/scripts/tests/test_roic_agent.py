"""
Test ROIC features through the MoatTutor agent.

This script tests the new ROIC functionality end-to-end by prompting the agent
with natural language queries that should trigger ROIC analysis.

Run this after starting the server:
    uvicorn main:app --reload

Then test via agent:
    python scripts/tests/test_roic_agent.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.moat_tutor import invoke_agent


def test_roic_direct_query():
    """Test direct ROIC query."""
    print("\n" + "="*80)
    print("TEST 1: Direct ROIC Query")
    print("="*80)
    print("Query: 'What is NVDA's ROIC over the last 10 years?'")
    print("-"*80)
    
    try:
        response = invoke_agent("What is NVDA's ROIC over the last 10 years?")
        print("\nRESPONSE:")
        print(response)
        print("\n" + "="*80)
        
        # Check if ROIC data is mentioned
        if "ROIC" in response.upper() or "return on invested capital" in response.lower():
            print("[PASS] ROIC analysis was included in response")
            return True
        else:
            print("[WARN] ROIC analysis may not have been triggered")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_roic_moat_analysis():
    """Test ROIC as part of moat analysis."""
    print("\n" + "="*80)
    print("TEST 2: ROIC in Moat Analysis")
    print("="*80)
    print("Query: 'Does NVDA have an economic moat? Analyze using ROIC.'")
    print("-"*80)
    
    try:
        response = invoke_agent("Does NVDA have an economic moat? Analyze using ROIC.")
        print("\nRESPONSE:")
        print(response)
        print("\n" + "="*80)
        
        # Check if ROIC and moat are both mentioned
        has_roic = "ROIC" in response.upper() or "return on invested capital" in response.lower()
        has_moat = "moat" in response.lower()
        
        if has_roic and has_moat:
            print("[PASS] ROIC was used in moat analysis")
            return True
        else:
            print(f"[WARN] ROIC: {has_roic}, Moat: {has_moat}")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_roic_peer_comparison():
    """Test ROIC peer comparison."""
    print("\n" + "="*80)
    print("TEST 3: ROIC Peer Comparison")
    print("="*80)
    print("Query: 'Compare NVDA's ROIC to AMD and INTC'")
    print("-"*80)
    
    try:
        response = invoke_agent("Compare NVDA's ROIC to AMD and INTC")
        print("\nRESPONSE:")
        print(response)
        print("\n" + "="*80)
        
        # Check if comparison was made
        has_comparison = any(word in response.lower() for word in ["compare", "vs", "versus", "higher", "lower", "advantage"])
        has_roic = "ROIC" in response.upper()
        
        if has_comparison and has_roic:
            print("[PASS] ROIC peer comparison was performed")
            return True
        else:
            print(f"[WARN] Comparison: {has_comparison}, ROIC: {has_roic}")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_roic_integrated_analysis():
    """Test ROIC integrated with price/news analysis."""
    print("\n" + "="*80)
    print("TEST 4: ROIC Integrated Analysis")
    print("="*80)
    print("Query: 'Analyze AAPL's moat using price data, news, and ROIC'")
    print("-"*80)
    
    try:
        response = invoke_agent("Analyze AAPL's moat using price data, news, and ROIC")
        print("\nRESPONSE:")
        print(response)
        print("\n" + "="*80)
        
        # Check if multiple data sources were used
        has_roic = "ROIC" in response.upper()
        has_price = any(word in response.lower() for word in ["price", "stock", "movement", "return"])
        has_news = any(word in response.lower() for word in ["news", "announcement", "reported", "earnings"])
        
        if has_roic and (has_price or has_news):
            print("[PASS] ROIC was integrated with other data sources")
            return True
        else:
            print(f"[WARN] ROIC: {has_roic}, Price: {has_price}, News: {has_news}")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_roic_hurdle_explanation():
    """Test ROIC hurdle explanation."""
    print("\n" + "="*80)
    print("TEST 5: ROIC Hurdle Explanation")
    print("="*80)
    print("Query: 'Explain what ROIC hurdle means and check if MSFT passes it'")
    print("-"*80)
    
    try:
        response = invoke_agent("Explain what ROIC hurdle means and check if MSFT passes it")
        print("\nRESPONSE:")
        print(response)
        print("\n" + "="*80)
        
        # Check if explanation and hurdle check were provided
        has_explanation = any(word in response.lower() for word in ["hurdle", "wacc", "cost of capital", "threshold"])
        has_check = any(word in response.lower() for word in ["pass", "fail", "above", "below", "exceed"])
        
        if has_explanation and has_check:
            print("[PASS] ROIC hurdle was explained and checked")
            return True
        else:
            print(f"[WARN] Explanation: {has_explanation}, Check: {has_check}")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all ROIC agent tests."""
    print("="*80)
    print("ROIC AGENT INTEGRATION TESTS")
    print("="*80)
    print("\nTesting ROIC features through the MoatTutor agent")
    print("Make sure the server is running: uvicorn main:app --reload")
    print("\n" + "="*80)
    
    tests = [
        ("Direct ROIC Query", test_roic_direct_query),
        ("ROIC in Moat Analysis", test_roic_moat_analysis),
        ("ROIC Peer Comparison", test_roic_peer_comparison),
        ("ROIC Integrated Analysis", test_roic_integrated_analysis),
        ("ROIC Hurdle Explanation", test_roic_hurdle_explanation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n[ERROR] Test '{name}' failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All ROIC agent tests passed!")
        print("ROIC features are working correctly through the agent.")
        return 0
    else:
        print("\n[WARNING] Some tests failed. Review the output above.")
        return 1


if __name__ == "__main__":
    exit(main())
