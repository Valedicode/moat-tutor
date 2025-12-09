"""
Quick test script for the MoatTutor agent.
Run this to verify the agent works before testing via API.
"""

from agent.moat_tutor import invoke_agent

def test_agent():
    print("Testing MoatTutor Agent with Natural Language Queries")
    print("=" * 80)
    print()
    
    # Test queries
    queries = [
        "Explain why AAPL stock moved from 2023-01-01 to 2023-02-28 using the MOAT framework.",
        # You can add more test queries here
        # "What are Microsoft's moat characteristics?",
        # "Get news for GOOGL in January 2023",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"Test {i}/{len(queries)}")
        print("-" * 80)
        print(f"Query: {query}")
        print()
        print("Running agent (this may take 10-30 seconds)...")
        print("-" * 40)
        
        try:
            response = invoke_agent(query)
            
            print()
            print("RESPONSE:")
            print(response)
            print()
            print("=" * 80)
            print(f"SUCCESS! Test {i} completed.")
            print()
            
        except Exception as e:
            print()
            print("ERROR:")
            print(f"{str(e)}")
            print()
            print("Make sure you have:")
            print("1. Created a .env file with your OPENAI_API_KEY")
            print("2. Installed all requirements: pip install -r requirements.txt")
            print("=" * 80)
            raise
    
    print()
    print("=" * 80)
    print(f"All {len(queries)} test(s) passed! Agent is working correctly.")
    print("=" * 80)


if __name__ == "__main__":
    test_agent()


