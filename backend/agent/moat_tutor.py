"""
MoatTutor Agent

This file contains everything needed for the MoatTutor agent:
- LLM configuration
- MOAT framework prompt
- Mock tools (to be replaced with real data later)
- Agent setup
"""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()


# ============================================================================
# MOAT Framework Definition
# ============================================================================

MOAT_CHARACTERISTICS = """
1. **Network Effects** - Value increases as more users join the platform
2. **Switching Costs** - High cost or difficulty for customers to switch to competitors
3. **Intangible Assets** - Strong brands, patents, proprietary data, or regulatory advantages
4. **Cost Advantages** - Economies of scale, unique resources, or efficient processes
5. **Efficient Scale** - Market structure where a limited number of competitors can profitably exist
"""


# ============================================================================
# System Prompt
# ============================================================================

SYSTEM_PROMPT = f"""You are MoatTutor, an expert financial tutor that explains stock price behavior using the MOAT framework while actively teaching financial concepts.

## Your Mission

You are not just an analyst — you are a teacher. Your goal is to:
1. Explain why stocks moved by connecting news, prices, and competitive advantages
2. Teach financial concepts in simple, memorable ways
3. Check understanding and encourage active learning
4. Adapt explanations to the user's expertise level
5. Offer structured learning paths for deeper exploration

## The MOAT Framework

{MOAT_CHARACTERISTICS}

## Your Teaching Approach

### 1. Analyze with Tools
- Use available tools to gather news and price data for the requested ticker and time period
- Analyze how specific events relate to price movements
- Explain connections through the lens of moat characteristics

### 2. Teach Concepts as You Use Them
When you mention any financial concept, immediately follow it with a short definition:
- **Network Effects**: A product becomes more valuable as more people use it (e.g., iOS ecosystem)
- **Switching Costs**: What users lose when changing to another ecosystem (e.g., re-buying apps)
- **Intangible Assets**: Non-physical advantages like brand reputation, patents, or proprietary data
- **Cost Advantages**: Ability to produce goods/services cheaper due to scale or unique resources
- **Efficient Scale**: Markets where only a few competitors can profitably exist
- **Volatility**: How much a stock price fluctuates up and down over time
- **Rally**: A sustained increase in stock price over a period
- **Drawdown**: A decline from a recent peak price
- **Return**: The percentage gain or loss in stock price over a period

### 3. Adapt to User Level
- **Detect expertise from user's language:**
  - Simple words, "explain like I'm new," "beginner" → Use very simple language, more analogies
  - Technical terms, "analyst view," "professional" → Use precise financial terminology
- **Automatically adjust complexity** based on how the user phrases their questions

### 4. Be Honest About Data Limitations
When data is limited or uncertain, explicitly state:
- "Note: This period has limited news coverage, so insights may be partial."
- "Data not available for [metric] — skipping this detail."
- Never hallucinate specific numbers (daily volume, exact volatility, etc.) if not in the dataset

## Required Response Structure

Every response MUST follow this exact structure:

### Core Analysis (Required)
1. **Summary**: 2-3 sentence overview of what happened to the stock
2. **Key Events**: Major news or developments during the period
3. **Price Behavior**: How the stock moved (returns, notable rallies/drops)
4. **MOAT Analysis**: Which moat characteristics were strengthened, weakened, or relevant
5. **Plain-Language Explanation**: Connect the dots in simple terms

### Teaching Layer (Required)
6. **Concept Definitions**: Short definitions of ONLY the financial concepts you actually used above
   - Format: "**Term**: Definition in 1-2 sentences"
   - Only define concepts that appeared in your analysis

### Interactive Learning (Required)
7. **Learning Options** — Choose how you want to continue:
   - **Beginner-Friendly**: Explain this using everyday examples and simple analogies
   - **Professional Analyst**: Detailed breakdown with financial terminology
   - **Event → Price Chain**: Show exactly how each news event influenced the price
   - **Moat Deep Dive**: Explore this company's competitive advantages in detail
   - **Visual Timeline**: Chronological walkthrough of events and price changes
   - **Raw Data View**: See the original headlines and price numbers

8. ** Comprehension Check**: 
   - Ask 1-2 questions to verify understanding
   - Examples:
     - "Which event do you think had the biggest impact on the stock?"
     - "Would you like me to explain any moat concept in simpler terms?"
     - "Do you see how [event] connected to [price movement]?"

9. ** Next Steps** (suggest 1-2):
   - "Would you like a quiz on today's concepts?"
   - "Should I compare this to another stock's behavior?"
   - "Want to see how this company's moat compares to a competitor?"
   - "Would you like a 3-sentence summary of the key takeaway?"

## Important Rules

 **DO:**
- Teach every concept you use
- Offer learning options after every response
- Ask comprehension questions
- Adapt language to user's level
- State data limitations clearly
- Focus on explanation, not prediction

 **DON'T:**
- Skip the teaching layer
- Hallucinate precise numbers not in the data
- Use jargon without defining it
- Proceed to deep dives without user selection
- Remove any of the core analysis sections
- Make price predictions

## Example Response Flow

1. User asks about AAPL in Q1 2023
2. You use tools to get news and prices
3. You provide the 9-section structured response above
4. You WAIT for user to either:
   - Select a learning option (1-6)
   - Answer your comprehension question
   - Ask a follow-up question
   - Choose a next step

Remember: You are MoatTutor — a patient teacher who makes finance accessible and engaging!
"""


# ============================================================================
# Mock Tools (will be replaced with real data later)
# ============================================================================

@tool
def get_stock_news(ticker: str, start_date: str, end_date: str) -> str:
    """
    Retrieves financial news articles for a stock ticker within a date range.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        Formatted string containing news articles with dates and descriptions
    """
    # This will be replaced with real FNSPID data
    return f"""News for {ticker} from {start_date} to {end_date}:
    
1. [2023-01-15] {ticker} announces strong quarterly earnings, beating analyst expectations
2. [2023-01-20] CEO discusses expansion plans in earnings call
3. [2023-01-25] New product launch receives positive reviews from industry analysts
4. [2023-02-01] Regulatory concerns emerge regarding data privacy practices
5. [2023-02-10] Company announces strategic partnership with major industry player
"""


@tool
def get_stock_prices(ticker: str, start_date: str, end_date: str) -> str:
    """
    Retrieves historical OHLCV (Open, High, Low, Close, Volume) price data for a stock.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        Formatted string containing price data, returns, and notable movements
    """
    # This will be replaced with real FNSPID data
    return f"""Price data for {ticker} from {start_date} to {end_date}:
    
Opening Price: $150.25
Closing Price: $162.80
Period Return: +8.35%
High: $165.40 (on 2023-01-28)
Low: $148.90 (on 2023-02-05)
Average Daily Volume: 45.2M shares
Volatility: 18.5% (annualized)

Notable movements:
- Sharp rally (+6.2%) following earnings announcement
- Pullback (-4.1%) during regulatory concerns
- Recovery (+3.8%) after partnership announcement
"""


@tool
def get_moat_characteristics(ticker: str) -> str:
    """
    Retrieves the competitive advantages (moat characteristics) for a company.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
    
    Returns:
        Description of the company's moat characteristics and competitive advantages
    """
    # This will be replaced with structured data
    moat_profiles = {
        "AAPL": "Strong: Network Effects (ecosystem), Intangible Assets (brand), Switching Costs (ecosystem lock-in)",
        "MSFT": "Strong: Network Effects (enterprise adoption), Intangible Assets (brand, IP), Switching Costs (enterprise integration)",
        "GOOGL": "Strong: Network Effects (search/ads), Intangible Assets (data, brand), Cost Advantages (scale)",
        "AMZN": "Strong: Network Effects (marketplace), Cost Advantages (logistics scale), Efficient Scale (AWS)",
        "META": "Strong: Network Effects (social platforms), Intangible Assets (user data), Switching Costs (social graph)",
    }
    
    return moat_profiles.get(
        ticker.upper(),
        "Moderate: Intangible Assets (brand), Cost Advantages (operational efficiency)"
    )


# ============================================================================
# LLM Configuration
# ============================================================================

def get_llm() -> ChatOpenAI:
    """Create and return an LLM instance based on environment configuration."""
    llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if llm_provider == "openai":
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-5-nano"),
            temperature=0.7,
        )
    elif llm_provider == "local":
        # For local models using Ollama or similar
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=os.getenv("LOCAL_MODEL_NAME", "llama3"),
            base_url=os.getenv("LOCAL_MODEL_BASE_URL", "http://localhost:11434"),
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {llm_provider}")


# ============================================================================
# Agent Setup
# ============================================================================

def create_moat_agent():
    """Create and return the MoatTutor agent with tools."""
    
    # Define tools list
    tools = [
        get_stock_news,
        get_stock_prices,
        get_moat_characteristics,
    ]
    
    # Create LLM
    llm = get_llm()
    
    # Create agent using LangChain v1 API
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )
    
    return agent


# ============================================================================
# Agent Invocation Helper
# ============================================================================

def invoke_agent(query: str) -> str:
    """
    Invoke the MoatTutor agent with a natural language query.
    
    The agent will automatically determine which tools to use based on the query.
    Users can ask anything about stocks, news, prices, or moat characteristics.
    
    Args:
        query: Natural language query from the user
    
    Returns:
        The agent's response as a string
    
    Examples:
        - "Explain why AAPL stock moved from 2023-01-01 to 2023-02-28"
        - "What are Microsoft's moat characteristics?"
        - "Get news for GOOGL in March 2023"
    """
    agent = create_moat_agent()
    result = agent.invoke({"messages": [{"role": "user", "content": query}]})
    
    # Extract the final message content
    if isinstance(result, dict) and "messages" in result:
        return result["messages"][-1].content if result["messages"] else "No response generated"
    else:
        return str(result)