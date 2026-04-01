"""
Interactive MoatTutor Agent - Terminal Mode

Run conversational sessions with the MoatTutor agent for local testing.

Supports two interaction modes:
  --mode analyst   Direct answers (default)
  --mode tutor     Socratic engagement with comprehension checks
"""

import sys
from agent.moat_tutor import create_moat_agent


def run_interactive_tutor(initial_input: str = None, mode: str = "analyst"):
    """
    Run MoatTutor with interactive user conversation via terminal.
    
    The agent can:
    1. Explain stock movements using the MOAT framework
    2. Teach financial concepts with clear causal reasoning
    3. Compare companies and identify moat sources
    
    In Tutor Mode (--mode tutor) the agent additionally:
    - Uses Socratic questioning instead of direct answers
    - Withholds final moat ratings for the student to derive
    - Produces comprehension checks and next-step suggestions
    
    Args:
        initial_input: Optional starting query
        mode: "analyst" or "tutor"
    """
    mode_label = "Tutor" if mode == "tutor" else "Analyst"
    print("=" * 80)
    print(f"MOATTUTOR - Interactive Mode ({mode_label})")
    print("=" * 80)
    print("\nI can help you understand stock movements using the MOAT framework.")
    if mode == "tutor":
        print("Tutor Mode is active -- I'll guide you with questions instead of answers.")
    print("\nExamples:")
    print("  - 'Explain why AAPL moved from 2023-01-01 to 2023-02-28'")
    print("  - 'What are network effects?'")
    print("  - 'Compare AAPL and MSFT moats'")
    print("\nType 'quit', 'exit', or 'q' to exit at any time.")
    print("=" * 80)
    print()
    
    # Create agent once
    print(f"Initializing MoatTutor agent ({mode_label} mode)...")
    try:
        agent = create_moat_agent(mode=mode)
        print("Agent ready!\n")
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
    print("  python interactive_tutor.py                          # Analyst mode (default)")
    print("  python interactive_tutor.py --mode tutor             # Tutor (Socratic) mode")
    print("  python interactive_tutor.py 'Your question'          # Start with a question")
    print("  python interactive_tutor.py --mode tutor 'Question'  # Tutor + initial query")
    print("\nModes:")
    print("  analyst  Direct answers with clear explanations (default)")
    print("  tutor    Socratic engagement -- the agent asks questions instead of")
    print("           giving answers, withholds moat ratings, and produces")
    print("           comprehension checks so you learn by reasoning.")
    print("\nExample Questions:")
    print("  - Explain why AAPL moved from 2023-01-01 to 2023-02-28")
    print("  - What are network effects in simple terms?")
    print("  - Compare Apple and Microsoft's moats")
    print("\nTips:")
    print("  - Say 'beginner' or 'simple' for easier explanations")
    print("  - Say 'analyst view' or 'technical' for advanced explanations")
    print("  - Type 'quit' to exit anytime")
    print("="*80 + "\n")


# CLI for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="MoatTutor Interactive CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["analyst", "tutor"],
        default="analyst",
        help="Interaction mode (default: analyst)",
    )
    parser.add_argument(
        "query",
        nargs="*",
        help="Optional initial question",
    )
    args = parser.parse_args()

    initial_input = " ".join(args.query) if args.query else None

    print("\n" + "=" * 80)
    print("MOATTUTOR - Your Interactive Financial Tutor")
    print("=" * 80 + "\n")

    try:
        run_interactive_tutor(initial_input, mode=args.mode)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Thanks for learning with MoatTutor!")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check that .env file exists with OPENAI_API_KEY")
        print("  2. Verify requirements are installed: pip install -r requirements.txt")
        print("  3. Run 'python test_agent.py' for basic functionality test")
        import traceback
        traceback.print_exc()

