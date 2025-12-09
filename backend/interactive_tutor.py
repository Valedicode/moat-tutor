"""
Interactive MoatTutor Agent - Terminal Mode

Run conversational sessions with the MoatTutor agent for local testing.
Perfect for testing tutoring features, learning paths, and comprehension checks.
"""

import sys
from agent.moat_tutor import create_moat_agent


def run_interactive_tutor(initial_input: str = None):
    """
    Run MoatTutor with interactive user conversation via terminal.
    
    The agent can:
    1. Explain stock movements using the MOAT framework
    2. Teach financial concepts
    3. Offer learning paths (Beginner, Analyst, Event-Chain, etc.)
    4. Answer comprehension check questions
    5. Provide quizzes and comparisons
    
    Args:
        initial_input: Optional starting query
    """
    print("=" * 80)
    print("MOATTUTOR - Interactive Tutoring Mode")
    print("=" * 80)
    print("\nI'm your financial tutor! I can help you understand stock movements")
    print("using the MOAT framework while teaching you financial concepts.")
    print("\nExamples:")
    print("  - 'Explain why AAPL moved from 2023-01-01 to 2023-02-28'")
    print("  - 'What are network effects?'")
    print("  - 'Give me the Beginner-Friendly explanation'")
    print("  - 'Quiz me on moat concepts'")
    print("  - 'Compare AAPL and MSFT moats'")
    print("\nType 'quit', 'exit', or 'q' to exit at any time.")
    print("=" * 80)
    print()
    
    # Create agent once
    print("🔧 Initializing MoatTutor agent...")
    try:
        agent = create_moat_agent()
        print("✅ Agent ready!\n")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        print("Make sure you have:")
        print("  1. Created a .env file with OPENAI_API_KEY")
        print("  2. Installed requirements: pip install -r requirements.txt")
        return
    
    # Initialize conversation
    if initial_input:
        messages = [{"role": "user", "content": initial_input}]
        print(f"📝 Starting with: {initial_input}\n")
    else:
        user_input = input("You: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Thanks for learning with MoatTutor! Goodbye!")
            return
        messages = [{"role": "user", "content": user_input}]
    
    # Conversation loop
    max_turns = 20  # Generous for learning sessions
    turn = 0
    
    while turn < max_turns:
        turn += 1
        print(f"\n{'='*80}")
        print(f"Turn {turn}")
        print(f"{'='*80}")
        
        # Agent's turn
        print("\n🤖 MoatTutor is thinking...\n")
        try:
            result = agent.invoke({"messages": messages})
            agent_response = result["messages"][-1].content
            
            # Add agent's response to history
            messages.append({"role": "assistant", "content": agent_response})
            
            # Display agent's response
            print(f"MoatTutor:\n{'-'*80}")
            print(agent_response)
            print(f"{'-'*80}\n")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again with a different question.\n")
            print("Tip: Make sure your .env file has a valid OPENAI_API_KEY")
            break
        
        # User's turn
        print(f"{'='*80}")
        user_input = input("You: ").strip()
        
        # Allow user to quit
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Great learning session! Come back anytime!")
            break
        
        # Empty input handling
        if not user_input:
            print("⚠️  Please enter a question or command.")
            continue
        
        # Add user's response to history
        messages.append({"role": "user", "content": user_input})
    
    if turn >= max_turns:
        print(f"\n⚠️  Reached maximum turns ({max_turns}). Ending conversation.")
        print("Feel free to start a new session to continue learning!")
    
    # Session summary
    print("\n" + "="*80)
    print("SESSION SUMMARY")
    print("="*80)
    print(f"Total turns: {turn}")
    print(f"Topics covered: Check the conversation above")
    print("\nTip: Run 'python interactive_tutor.py' anytime to start a new session!")
    print("="*80)
    
    return {
        "messages": messages,
        "turns": turn
    }


def print_help():
    """Print help information."""
    print("\n" + "="*80)
    print("MOATTUTOR - Interactive Mode Help")
    print("="*80)
    print("\nUsage:")
    print("  python interactive_tutor.py                    # Start interactive session")
    print("  python interactive_tutor.py 'Your question'    # Start with a question")
    print("\nExample Questions:")
    print("  - Explain why AAPL moved from 2023-01-01 to 2023-02-28")
    print("  - What are network effects in simple terms?")
    print("  - Give me the Beginner-Friendly explanation")
    print("  - I want the Moat Deep Dive")
    print("  - Quiz me on the concepts we just covered")
    print("  - Compare Apple and Microsoft's moats")
    print("\nLearning Paths (you can request these):")
    print("  1. Beginner-Friendly - Simple analogies and everyday examples")
    print("  2. Professional Analyst - Technical financial terminology")
    print("  3. Event → Price Chain - Causal links between news and price")
    print("  4. Moat Deep Dive - Detailed competitive advantage analysis")
    print("  5. Visual Timeline - Chronological walkthrough")
    print("  6. Raw Data View - Original headlines and numbers")
    print("\nThe agent will:")
    print("  ✓ Explain stock movements using the MOAT framework")
    print("  ✓ Define every financial concept it uses")
    print("  ✓ Offer 6 learning paths after each explanation")
    print("  ✓ Ask comprehension check questions")
    print("  ✓ Suggest next steps for active learning")
    print("  ✓ Adapt language to your expertise level")
    print("\nTips:")
    print("  - Say 'beginner' or 'simple' for easier explanations")
    print("  - Say 'analyst view' or 'technical' for advanced explanations")
    print("  - Type 'quit' to exit anytime")
    print("="*80 + "\n")


# CLI for testing
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🎓 MOATTUTOR - Your Interactive Financial Tutor")
    print("="*80 + "\n")
    
    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print_help()
        sys.exit(0)
    
    # Get initial input from command line or prompt user
    if len(sys.argv) > 1:
        initial_input = " ".join(sys.argv[1:])
    else:
        initial_input = None
    
    # Run interactive tutor
    try:
        run_interactive_tutor(initial_input)
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Thanks for learning with MoatTutor!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check that .env file exists with OPENAI_API_KEY")
        print("  2. Verify requirements are installed: pip install -r requirements.txt")
        print("  3. Run 'python test_agent.py' for basic functionality test")
        import traceback
        traceback.print_exc()

