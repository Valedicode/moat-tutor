"""
MoatTutor Agent

This file contains everything needed for the MoatTutor agent:
- LLM configuration
- MOAT framework prompt
- Real data tools (stock prices, time series, moat characteristics)
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

from services.stock_data import get_stock_data_service
from services.news_provider import get_news_for_agent

# Import FNSPID retrieval for historical semantic search
try:
    from services.fnspid_retrieval import (
        search_historical_news,
        is_fnspid_data_available,
        get_fnspid_status,
    )
    FNSPID_AVAILABLE = True
except ImportError:
    FNSPID_AVAILABLE = False

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
- For historical queries (2015-2023):
  - If the user asks about a SPECIFIC topic or event (e.g., "AI chip demand", "earnings", "product launch"), 
    provide a query parameter to get_stock_news for semantic search with embeddings
  - If the user asks for GENERAL analysis (e.g., "why did the stock move"), omit the query for chronological summary
- For recent queries (2024+), the tool automatically uses yfinance
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

## Response Style (Adaptive — avoid too long response for simple queries)

Choose the response style based on the user's request. The goal is to be helpful, not verbose.

### A) Quick Clarification Mode (default for general questions)
Use this when the user asks a general definition/clarification without a specific ticker + time window (e.g., "Explain moat evolution", "What is switching cost?", "Define network effects").

Hard rule:
- If the user did **NOT** provide (or clearly imply) a **ticker** AND a **time window**, you MUST use Quick Clarification Mode,
  unless the user explicitly asks for "full analysis", "full report", "9-section", or "structured analysis".

Requirements:
- Answer in **4–10 sentences total** (concise).
- Include, if helpful, **1 short example** (1–2 sentences).
- Include **one** follow-up question that helps move toward a concrete analysis (e.g., ask for ticker + time window) OR checks understanding.
- **Do NOT** output the 9-section template, checkboxes, or "Required" labels in this mode.

### B) Full Stock/Period Analysis Mode (use only when warranted)
Use this when the user asks to explain **why a stock moved** or provides a **ticker and time period**, or explicitly requests a structured moat/price analysis.

In this mode, use the 9-section structure below, but keep it tight:
- Each numbered section should be **2–5 bullet points max** (or a short paragraph if bullets aren't natural).
- Avoid repeating template words like "(Required)".

#### 9-Section Structure (for Full Analysis Mode)
### Core Analysis
1. **Summary**: 2-3 sentence overview of what happened to the stock
2. **Key Events**: Major news or developments during the period
3. **Price Behavior**: How the stock moved (returns, notable rallies/drops)
4. **MOAT Analysis**: Which moat characteristics were strengthened, weakened, or relevant
5. **Plain-Language Explanation**: Connect the dots in simple terms

### Teaching Layer
6. **Concept Definitions**: Define ONLY the concepts you used above
   - Format: "**Term**: Definition in 1-2 sentences"

### Interactive Learning
7. **Learning Options**: Offer 3–6 options (not all, unless relevant)
8. **Comprehension Check**: Ask 1–2 questions
9. **Next Steps**: Suggest 1–2 next actions

## Important Rules

 **DO:**
- Teach every concept you use
- Match format to the question (Quick Clarification vs Full Analysis)
- Be concise by default; expand only when the user asks or when analysis truly requires it
- Offer learning options and comprehension checks when doing deeper analysis
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

1. User asks a general question (e.g., "Explain moat evolution") → you respond in **Quick Clarification Mode**
2. User then provides ticker + time window (or asks "why did it move") → you switch to **Full Analysis Mode**
3. In Full Analysis Mode, you use tools to get news and prices and provide the 9-section response
4. You WAIT for the user to either:
   - Select a learning option (1-6)
   - Answer your comprehension question
   - Ask a follow-up question
   - Choose a next step

Remember: You are MoatTutor — a patient teacher who makes finance accessible and engaging!
"""


# ============================================================================
# Agent Tools
# ============================================================================

@tool
def get_stock_news(ticker: str, start_date: str, end_date: str, query: str = None) -> str:
    """
    Retrieves financial news articles for a stock ticker within a date range.
    
    This tool intelligently routes between data sources:
    - Historical dates (2015-2023): Uses FNSPID dataset with 142K+ curated news passages
    - Recent dates (2024+): Uses yfinance (typically last 30 days)
    
    For historical queries, you can optionally provide a search query to use semantic
    search with embeddings. This finds the most relevant news passages for specific
    topics or events.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'NVDA')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        query: Optional search query for semantic retrieval (e.g., "AI chip demand", 
               "earnings report", "supply chain issues"). If provided for historical 
               dates, uses embeddings to find most relevant passages. If omitted, 
               returns chronological summary.
    
    Returns:
        Formatted string containing news articles with dates and descriptions
    
    Examples:
        - get_stock_news("NVDA", "2023-01-01", "2023-06-30")  # Chronological summary
        - get_stock_news("NVDA", "2023-01-01", "2023-06-30", "AI chip demand")  # Semantic search
    """
    return get_news_for_agent(ticker, start_date, end_date, query=query)


@tool
def get_stock_prices(ticker: str, start_date: str, end_date: str) -> str:
    """
    Retrieves historical OHLCV (Open, High, Low, Close, Volume) price data for a stock.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'GOOGL', 'NVDA')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        Formatted string containing price data, returns, and notable movements
    """
    try:
        service = get_stock_data_service()
        
        # Get return statistics
        stats = service.calculate_returns(ticker, start_date, end_date)
        
        if "error" in stats:
            return f"Error: {stats['error']}"
        
        # Get notable movements
        movements = service.find_notable_movements(ticker, start_date, end_date, threshold_pct=3.0)
        
        # Format response
        response = f"""Price data for {stats['ticker']} from {stats['start_date']} to {stats['end_date']}:

Opening Price: ${stats['opening_price']}
Closing Price: ${stats['closing_price']}
Period Return: {stats['period_return_pct']:+.2f}%
High: ${stats['high_price']} (on {stats['high_date']})
Low: ${stats['low_price']} (on {stats['low_date']})
Average Daily Volume: {stats['avg_daily_volume']:,.0f} shares
Volatility: {stats['volatility_annualized_pct']:.2f}% (annualized)
Total Trading Days: {stats['total_days']}
"""
        
        if movements:
            response += "\nNotable movements (>3% daily change):\n"
            for m in movements[:10]:  # Limit to top 10
                sign = "+" if m['pct_change'] > 0 else ""
                response += f"- {m['date']}: {sign}{m['pct_change']}% (${m['open']} -> ${m['close']})\n"
        else:
            response += "\nNo notable single-day movements (>3%) during this period.\n"
        
        return response
        
    except FileNotFoundError:
        available = service.available_tickers()
        return f"Error: No data available for ticker {ticker}. Available tickers: {', '.join(available)}"
    except Exception as e:
        return f"Error retrieving price data: {str(e)}"


@tool
def get_stock_time_series(ticker: str, start_date: str, end_date: str, columns: str = "close,volume") -> str:
    """
    Retrieves detailed time series data for a stock (daily prices and volumes).
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'GOOGL', 'NVDA')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        columns: Comma-separated list of columns to include (e.g., 'open,high,low,close,volume')
    
    Returns:
        Formatted string with daily time series data
    """
    try:
        service = get_stock_data_service()
        
        # Parse columns
        column_list = [c.strip() for c in columns.split(',')]
        
        # Get time series data
        data = service.get_time_series(ticker, start_date, end_date, column_list)
        
        if "error" in data:
            return f"Error: {data['error']}"
        
        # Format as a table
        dates = data['dates']
        response = f"Time series data for {data['ticker']}:\n\n"
        
        # Create header
        header = "Date       "
        for col in column_list:
            if col in data:
                header += f" {col.capitalize():>12}"
        response += header + "\n"
        response += "-" * len(header) + "\n"
        
        # Add rows (limit to sample if too many)
        max_rows = 50
        if len(dates) > max_rows:
            # Show first 25 and last 25
            indices = list(range(25)) + list(range(len(dates) - 25, len(dates)))
            response += "# Showing first 25 and last 25 days\n"
        else:
            indices = range(len(dates))
        
        prev_idx = -2
        for i in indices:
            if i - prev_idx > 1:
                response += "...\n"
            
            row = f"{dates[i]} "
            for col in column_list:
                if col in data:
                    value = data[col][i]
                    if col == 'volume':
                        row += f" {value:>12,.0f}"
                    else:
                        row += f" {value:>12.2f}"
            response += row + "\n"
            prev_idx = i
        
        response += f"\nTotal data points: {len(dates)}"
        
        return response
        
    except FileNotFoundError:
        service = get_stock_data_service()
        available = service.available_tickers()
        return f"Error: No data available for ticker {ticker}. Available tickers: {', '.join(available)}"
    except Exception as e:
        return f"Error retrieving time series data: {str(e)}"


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
        "NVDA": "Strong: Intangible Assets (IP, CUDA platform), Network Effects (developer ecosystem), Cost Advantages (scale, R&D efficiency)",
        "AMZN": "Strong: Network Effects (marketplace), Cost Advantages (logistics scale), Efficient Scale (AWS)",
        "META": "Strong: Network Effects (social platforms), Intangible Assets (user data), Switching Costs (social graph)",
    }
    
    return moat_profiles.get(
        ticker.upper(),
        "Moderate: Intangible Assets (brand), Cost Advantages (operational efficiency)"
    )


@tool
def search_news_by_topic(ticker: str, query: str, start_date: str, end_date: str) -> str:
    """
    Search historical news for a specific topic using semantic similarity.
    
    This tool uses embeddings to find news passages that are semantically
    similar to your query. It's best for finding specific events, themes,
    or topics in historical news data (2015-2023).
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'NVDA')
        query: What you're looking for (e.g., "earnings report", "AI chip demand", "supply chain issues")
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        Relevant news passages ranked by similarity to your query
    
    Examples:
        - search_news_by_topic("NVDA", "data center AI growth", "2023-01-01", "2023-06-30")
        - search_news_by_topic("AAPL", "iPhone sales decline", "2022-06-01", "2022-12-31")
    """
    if not FNSPID_AVAILABLE:
        return ("Historical news search is not available. "
                "The FNSPID module could not be imported.")
    
    if not is_fnspid_data_available(ticker.upper()):
        return (f"No historical news data available for {ticker}. "
                f"Run the FNSPID pipeline first:\n"
                f"  python -m services.fnspid_news_pipeline --tickers {ticker}")
    
    return search_historical_news(
        ticker=ticker,
        query=query,
        start_date=start_date,
        end_date=end_date,
        top_k=5
    )


# ============================================================================
# LLM Configuration
# ============================================================================

def get_llm() -> ChatOpenAI:
    """Create and return an LLM instance based on environment configuration."""
    llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
    llm_streaming = os.getenv("LLM_STREAMING", "true").lower() in ("1", "true", "yes", "y", "on")
    
    if llm_provider == "openai":
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-5-nano"),
            temperature=0.7,
            streaming=llm_streaming,
        )
    elif llm_provider == "local":
        # For local models using Ollama or similar
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=os.getenv("LOCAL_MODEL_NAME", "llama3"),
            base_url=os.getenv("LOCAL_MODEL_BASE_URL", "http://localhost:11434"),
            streaming=llm_streaming,
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
        get_stock_time_series,
        get_moat_characteristics,
        search_news_by_topic,  # Semantic search in historical news
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

def invoke_agent(query: str, conversation_history: list[dict] = None) -> str:
    """
    Invoke the MoatTutor agent with a natural language query.
    
    The agent will automatically determine which tools to use based on the query.
    Users can ask anything about stocks, news, prices, or moat characteristics.
    
    Args:
        query: Natural language query from the user
        conversation_history: Optional list of previous messages in format
                            [{"role": "user/assistant", "content": "..."}]
    
    Returns:
        The agent's response as a string
    
    Examples:
        - "Explain why AAPL stock moved from 2023-01-01 to 2023-02-28"
        - "What are Microsoft's moat characteristics?"
        - "Get news for GOOGL in March 2023"
    """
    agent = create_moat_agent()
    
    # Build message list with conversation history
    messages = []
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": query})
    
    result = agent.invoke({"messages": messages})
    
    # Extract the final message content
    if isinstance(result, dict) and "messages" in result:
        return result["messages"][-1].content if result["messages"] else "No response generated"
    else:
        return str(result)


def stream_agent_messages(query: str, conversation_history: list[dict] = None):
    """
    Stream token/message chunks from the agent using LangChain streaming.

    Args:
        query: User's question or request
        conversation_history: Optional list of previous messages in format
                            [{"role": "user/assistant", "content": "..."}]

    Yields (token, metadata) tuples as produced by agent.stream/agent.astream
    with stream_mode="messages".
    """
    agent = create_moat_agent()
    
    # Build message list with conversation history
    messages = []
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": query})
    

    if hasattr(agent, "astream"):
        async def _agen():
            async for token, metadata in agent.astream(
                {"messages": messages},
                stream_mode="messages",
            ):
                yield token, metadata
        return _agen()

    # Fallback to sync streaming
    def _gen():
        for token, metadata in agent.stream(
            {"messages": messages},
            stream_mode="messages",
        ):
            yield token, metadata
    return _gen()