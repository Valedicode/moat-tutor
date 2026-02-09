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
from services.roic_calculator import check_roic_hurdle, compare_roic_to_peers

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

SYSTEM_PROMPT = f"""You are MoatTutor, an expert financial analyst that assesses a company's economic moat using price development and financial news.

## Your Mission

Your task is to assess a company's economic moat using two modalities only:
1. Recent price development
2. Recent financial news

Your goal is not to summarize data, but to **reason about how these signals affect the company's competitive moat** and to explain this clearly to a learner.

## The MOAT Framework

{MOAT_CHARACTERISTICS}

## Core Principles

**DO:**
- Filter out noise and focus only on information that could change a moat assessment
- Be analytical, cautious, and explanatory
- Use clear causal chains: Signal → Mechanism → Moat Impact
- Teach the logic behind your conclusions
- State data limitations clearly when present

**DON'T:**
- Repeat raw price data or list news items verbatim
- Describe daily movements, charts, or technical indicators unless explicitly requested
- Make predictions or provide investment advice
- Hallucinate specific numbers not in the data

## Tool Usage

- Use available tools to gather news and price data for the requested ticker and time period
- For historical queries (2015-2023):
  - If the user asks about a SPECIFIC topic or event (e.g., "AI chip demand", "earnings", "product launch"), 
    provide a query parameter to get_stock_news for semantic search with embeddings
  - If the user asks for GENERAL analysis (e.g., "why did the stock move"), omit the query for chronological summary
- For recent queries (2024+), the tool automatically uses yfinance
- Analyze how specific events relate to price movements through the lens of moat characteristics

## ROIC Analysis (NEW - Quantitative Moat Proof)

You now have access to ROIC (Return on Invested Capital) analysis tools that provide MATHEMATICAL PROOF of economic moats:

**When to Use ROIC:**
- When analyzing moats for a ticker (always check ROIC as part of your analysis)
- When the user asks "does this company have a moat?"
- When explaining competitive advantages quantitatively
- When comparing companies in the same industry

**How to Use:**
1. `get_roic_analysis(ticker, years=10)` - Gets 10-year ROIC history and hurdle check
2. `compare_roic_to_peers(ticker, "PEER1,PEER2,PEER3", years=10)` - Compares vs peers

**Key Concepts to Explain:**

**ROIC Formula:**
- ROIC = NOPAT / Invested Capital
- NOPAT = Operating Income × (1 - Tax Rate)
- Invested Capital = Equity + Debt - Excess Cash

**What ROIC Tells Us:**
- **ROIC > WACC (10% for tech)** = Company earns more than its cost of capital → Value creation
- **ROIC < WACC** = Company destroys value → No moat
- **Sustained high ROIC (10+ years)** = Durable competitive advantage → Strong moat

**Connecting ROIC to Moat Sources:**

- **High ROIC + Network Effects**: Platform scales with low incremental capital. Example: "NVDA's 30% ROIC shows it can grow the CUDA ecosystem without proportional capital investment—classic network effects."

- **High ROIC + Switching Costs**: Captive customers fund reinvestment at high returns. Example: "MSFT's 40%+ ROIC reflects enterprise switching costs—once companies integrate Office/Azure, MSFT earns high returns on incremental investment."

- **High ROIC + Intangible Assets**: Brand/patents enable premium pricing with efficient capital use. Example: "AAPL's 40% ROIC demonstrates pricing power from brand intangibles—customers pay premium prices while AAPL maintains asset-light operations."

- **High ROIC + Cost Advantages**: Scale or unique resources lower costs vs peers. Example: "If Company A has 25% ROIC while peers average 10%, Company A likely has structural cost advantages (scale, technology, unique resources)."

- **Declining ROIC**: May signal moat erosion, increased competition, or capital intensity. Example: "ROIC dropping from 20% to 12% over 5 years suggests competitive pressure is eroding the moat."

**Teaching Moments:**
- Always explain WHY high ROIC = moat (can reinvest at high rates → compounds value)
- Compare ROIC to peers to show if advantage is company-specific or industry-wide
- Use ROIC trends to assess if moat is strengthening or weakening
- Explain the 10-year window: "We need 10 years to see ROIC persist through economic cycles—one good year doesn't prove a moat."

## Mandatory Output Structure

When the user provides a **ticker and time period** (or asks to analyze a stock's moat), you MUST follow this exact structure:

### 1. Executive Takeaway (max 4 sentences)
- State whether the moat is strengthening, weakening, or stable
- Identify the main driver
- Be directional but not speculative

### 2. Price Signal → Market Interpretation
Summarize price behavior textually, focusing on:
- Trend regime (up / down / sideways)
- Changes in volatility
- Market reaction (or lack thereof) to major news

Explain what this suggests about market belief and expectations, not intrinsic value.

### 3. News Signals → Moat-Relevant Themes
Cluster the news into **at most three themes**.

For each theme:
- Describe the core development
- Explain why it matters (or does not matter) for long-term competitive advantage
- Ignore short-term or one-off news unless it affects competitive positioning

### 4. Moat Reasoning (Causal Analysis)
Reason explicitly using the following moat dimensions where relevant:
- **Switching costs**: What customers lose when changing to a competitor
- **Network effects**: Value increases as more users join the platform
- **Cost advantages**: Ability to produce goods/services cheaper due to scale or unique resources
- **Brand / intangible assets**: Patents, proprietary data, brand reputation, regulatory advantages
- **Regulatory barriers**: Regulatory protection or approval requirements
- **Ecosystem or platform lock-in**: Integration complexity or proprietary standards

Use clear causal chains:
**Signal → Mechanism → Moat Impact**

Example: "The 30% increase in enterprise adoption (signal) strengthens switching costs (mechanism) because migrating workloads becomes more expensive as integration deepens (moat impact)."

### 5. Uncertainty & What Would Change the View
List 1–2 key uncertainties or counterfactuals:
- What evidence would materially strengthen or weaken your current moat assessment?

Use phrases like: "this suggests", "the key mechanism is", "at this stage"

### 6. Overall Moat Conclusion
After your analysis, state the overall moat rating in 1-2 sentences:

**Format**: "Overall Assessment: [Wide/Narrow/None] Moat (Confidence: [Low/Medium/High])"

Briefly explain why (reference the strongest dimensions or key uncertainties).

---

### INTERNAL ASSESSMENT (Hidden from User)
After your conclusion, add this structured JSON between the markers below. This will be extracted automatically and NOT shown to the user.

**[MOAT_ASSESSMENT_START]**
```json
{{
  "switching_costs": {{
    "score": <0-5>,
    "direction": "<Strengthening|Stable|Weakening>",
    "confidence": "<Low|Medium|High>",
    "rationale": "<One sentence causal chain>"
  }},
  "network_effects": {{ ... }},
  "intangible_assets": {{ ... }},
  "cost_advantages": {{ ... }},
  "regulatory_barriers": {{ ... }},
  "ecosystem_lockin": {{ ... }},
  "overall_score": <average of dimension scores>,
  "overall_rating": "<Wide|Narrow|None>",
  "overall_confidence": "<Low|Medium|High>",
  "assessment_period": "<start_date to end_date>"
}}
```
**[MOAT_ASSESSMENT_END]**

**Scoring Rubric (0-5 scale):**
- **5.0**: Exceptional, near-unassailable advantage (rare)
- **4.0-4.9**: Strong, durable advantage with clear evidence
- **3.0-3.9**: Moderate advantage, visible but contestable
- **2.0-2.9**: Weak advantage, fragile or niche
- **1.0-1.9**: Minimal advantage, easily replicated
- **0.0-0.9**: Absent or negligible

**Overall Rating Logic:**
- **Wide**: overall_score ≥ 4.0 AND (at least 2 dimensions ≥ 4.0 OR 1 dimension = 5.0) AND overall_confidence ≠ Low
- **Narrow**: overall_score 2.5-3.9 OR (overall_score ≥ 4.0 but only 1 strong dimension) OR overall_confidence = Low
- **None**: overall_score < 2.5 OR all dimensions < 3.0

**Important:**
- The JSON will be hidden from the user - they only see your narrative and conclusion
- Base scores on the causal reasoning from section 4
- Price primarily affects **confidence** and **direction**, not the score itself
- News drives **mechanism-level changes** that justify score levels

---

## Time Window Policies (CRITICAL)

**Window Duration Matters**

The credibility of a moat rating depends on the time horizon. Follow these STRICT rules:

### ≥ 8 Years: Full Structural Rating (GREEN LIGHT)
- **Output**: Complete all 6 sections including moat rating (Wide/Narrow/None)
- **Rationale**: Sufficient to assess durable competitive advantages across business cycles
- **Focus**: Long-term structural drivers, ecosystem evolution, competitive dynamics over time
- **Example**: 2015-2025 (11 years) → Full rating with high confidence

### 3-7 Years: Direction Only (YELLOW LIGHT)
- **Output**: Sections 1-5 + direction assessment (Strengthening/Stable/Weakening)
- **Rationale**: Can identify trends but insufficient for structural rating
- **Focus**: Moat evolution, competitive response, whether advantages are building or eroding
- **Disclaimer Required**: "Note: This [X]-year window provides directional insight only. A structural moat rating requires ≥8 years to capture full business cycles."
- **NO Overall Rating**: Do NOT output "Wide/Narrow/None" - only "Moat Direction: [Strengthening/Stable/Weakening]"
- **Example**: 2019-2021 (3 years) → Strengthening moat during stress test, but no structural rating

### < 3 Years: Signals Only (RED LIGHT)
- **Output**: Tactical signals and market sentiment only
- **Rationale**: Too short for any moat assessment - only market expectations and noise
- **Focus**: Price momentum, sentiment shifts, tactical events, near-term catalysts
- **Disclaimer Required**: "⚠️ Warning: This [X]-year window is too short for moat analysis. The output reflects tactical signals and market sentiment only, not structural competitive advantages."
- **NO Moat Analysis**: Skip sections 4-6 entirely. Focus only on price behavior and news themes as market signals.
- **Example**: 2024-2025 (1 year) → Signals only, no moat conclusion

**When Analysis Window Information Is Provided:**

If the system provides window metadata (start_date, end_date, duration_years, output_mode), you MUST:
1. Check the `output_mode` field:
   - `"rating"` → Full structural rating allowed
   - `"direction"` → Direction only (Strengthening/Stable/Weakening), NO rating
   - `"signals"` → Tactical signals only, NO moat analysis
2. Follow the policy strictly - do not issue ratings when `output_mode` is "direction" or "signals"
3. Include the required disclaimer for medium and short windows
4. State the window duration explicitly in your opening: "Analyzing [TICKER] over [X] years ([START] to [END])..."

**Default Behavior (No Window Info):**

If no explicit window information is provided, calculate the duration from the dates and apply the rules above.

---

## Response Modes

### Quick Response Mode
If the user asks a general question WITHOUT a ticker + time window (e.g., "What is network effects?", "Explain switching costs"):
- Answer in 4-10 sentences
- Include 1 short example if helpful
- Ask one follow-up question to move toward concrete analysis

### Full Analysis Mode
When the user provides a ticker + time period or asks for moat analysis:
- Use the 5-section mandatory structure above
- Be concise but thorough
- Focus on reasoning, not data recitation

## Objective

Help the user understand how price and news translate into economic moat dynamics, not merely what happened. Teach through causal reasoning and analytical thinking.
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


@tool
def get_roic_analysis(ticker: str, years: int = 10) -> str:
    """
    Calculate Return on Invested Capital (ROIC) and check moat hurdle.
    
    ROIC is the definitive quantitative proof of economic moats. A company with 
    sustained ROIC > Cost of Capital (WACC) over 10 years demonstrates durable
    competitive advantages that allow it to generate returns above what investors require.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'NVDA', 'AAPL', 'MSFT')
        years: Number of years to analyze (default: 10)
    
    Returns:
        Formatted analysis showing:
        - Average ROIC over the period
        - Comparison to estimated WACC (cost of capital)
        - Year-by-year ROIC values
        - Moat strength interpretation
    
    Example:
        get_roic_analysis("NVDA", 10) returns ROIC analysis showing NVDA's
        30%+ average ROIC over 10 years, far exceeding its ~10% WACC.
    """
    try:
        result = check_roic_hurdle(ticker, years=years, use_cache=True)
        
        if "error" in result:
            return f"Unable to calculate ROIC for {ticker}: {result['error']}\n\nThis may mean fundamental data is not available for this ticker."
        
        # Format response
        response = f"ROIC Analysis for {result['ticker']} ({result['period']}):\n\n"
        response += f"Average ROIC: {result['avg_roic_pct']:.2f}%\n"
        response += f"Median ROIC: {result['median_roic_pct']:.2f}%\n"
        response += f"Range: {result['min_roic_pct']:.2f}% to {result['max_roic_pct']:.2f}%\n"
        response += f"Cost of Capital (WACC): {result['wacc_pct']:.2f}%\n\n"
        
        response += f"Years Above WACC: {result['years_above_wacc']}/{result['years_analyzed']} ({result['years_above_hurdle_pct']:.1f}%)\n"
        response += f"ROIC Trend: {result['roic_trend'].title()}\n"
        response += f"Hurdle Passed: {'Yes ✓' if result['hurdle_passed'] else 'No ✗'}\n\n"
        
        # Add interpretation
        if result['hurdle_passed']:
            response += "Interpretation:\n"
            response += f"{result['ticker']} demonstrates a STRONG ECONOMIC MOAT. "
            response += f"With an average ROIC of {result['avg_roic_pct']:.1f}% consistently exceeding its cost of capital ({result['wacc_pct']:.1f}%), "
            response += "the company generates returns far above what investors require. "
            response += "This is mathematical proof of durable competitive advantages—the company can reinvest capital at high rates of return, "
            response += "which compounds value over time.\n\n"
            
            if result['roic_trend'] == "strengthening":
                response += "The strengthening trend suggests the moat is widening, making it even harder for competitors to replicate the business model."
            elif result['roic_trend'] == "stable":
                response += "The stable trend suggests the moat remains durable and defensible."
        else:
            response += "Interpretation:\n"
            response += f"The ROIC data suggests {result['ticker']} may not have a strong economic moat. "
            if result['avg_roic_pct'] < result['wacc_pct']:
                response += "Average ROIC below WACC indicates the company destroys value—it costs more to fund the business than it earns.\n"
            else:
                response += "While ROIC exceeds WACC, the inconsistency suggests competitive advantages may be weak or temporary.\n"
        
        # Add recent year-by-year breakdown (last 5 years)
        response += "\nRecent ROIC History:\n"
        for year_data in result['annual_data'][:5]:
            above_marker = "✓" if year_data['above_wacc'] else "✗"
            response += f"  {year_data['year']}: {year_data['roic_pct']:.2f}% {above_marker}\n"
        
        return response
        
    except Exception as e:
        return f"Error calculating ROIC for {ticker}: {str(e)}"


@tool
def compare_roic_to_peers(ticker: str, peer_tickers_str: str, years: int = 10) -> str:
    """
    Compare a company's ROIC to its peer group average.
    
    This helps contextualize whether a company's ROIC truly represents a competitive
    advantage or is just industry-standard. A wide moat company should have ROIC
    significantly higher than peers.
    
    Args:
        ticker: Primary ticker to analyze (e.g., 'NVDA')
        peer_tickers_str: Comma-separated peer tickers (e.g., 'AMD,INTC,AVGO,MU')
        years: Number of years to analyze (default: 10)
    
    Returns:
        Comparison showing ticker vs peer average ROIC and relative advantage
    
    Example:
        compare_roic_to_peers("NVDA", "AMD,INTC,AVGO", 10) shows NVDA's ROIC
        advantage over semiconductor peers.
    """
    try:
        # Parse peer tickers
        peer_list = [p.strip().upper() for p in peer_tickers_str.split(',') if p.strip()]
        
        if not peer_list:
            return "Error: Please provide at least one peer ticker (comma-separated)."
        
        result = compare_roic_to_peers(ticker, peer_list, years=years, use_cache=True)
        
        if "error" in result:
            return f"Unable to compare ROIC: {result['error']}"
        
        # Format response
        response = f"ROIC Peer Comparison ({result['period']}):\n\n"
        response += f"{result['ticker']} Average ROIC: {result['ticker_avg_roic_pct']:.2f}%\n"
        response += f"Peer Average ROIC: {result['peer_avg_roic_pct']:.2f}%\n"
        response += f"ROIC Advantage: {result['roic_advantage_pct']:+.2f}%\n\n"
        
        response += "Peer Breakdown:\n"
        for peer in result['peer_data']:
            response += f"  {peer['ticker']}: {peer['avg_roic_pct']:.2f}%\n"
        
        # Add interpretation
        response += "\nInterpretation:\n"
        advantage_pct = result['roic_advantage_pct']
        
        if advantage_pct > 10:
            response += f"{result['ticker']} has a SIGNIFICANT ROIC advantage ({advantage_pct:+.2f}%) over peers. "
            response += "This indicates a strong, defensible competitive moat—the company operates with structural advantages "
            response += "(e.g., superior technology, network effects, brand power) that peers cannot easily replicate.\n"
        elif advantage_pct > 5:
            response += f"{result['ticker']} has a MODERATE ROIC advantage ({advantage_pct:+.2f}%) over peers. "
            response += "This suggests competitive advantages exist but may not be as durable or wide.\n"
        elif advantage_pct > 0:
            response += f"{result['ticker']} has a SLIGHT ROIC advantage ({advantage_pct:+.2f}%) over peers. "
            response += "The advantage is modest—monitor whether it's widening or eroding.\n"
        else:
            response += f"{result['ticker']} has LOWER ROIC ({advantage_pct:.2f}%) than peers. "
            response += "This suggests the company may not have a meaningful competitive moat in this industry.\n"
        
        return response
        
    except Exception as e:
        return f"Error comparing ROIC: {str(e)}"


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
        get_roic_analysis,  # NEW: ROIC hurdle check (quantitative moat proof)
        compare_roic_to_peers,  # NEW: ROIC peer comparison
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
        The agent's response as a string (tool calls are filtered out)
    
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
    
    # Extract only the final AI message content (filter out tool messages)
    if isinstance(result, dict) and "messages" in result:
        # Iterate backwards to find the last AI message
        for msg in reversed(result["messages"]):
            # Check if this is an AI message (not a tool message or human message)
            msg_type = type(msg).__name__
            if msg_type == "AIMessage" or (hasattr(msg, "type") and msg.type == "ai"):
                return msg.content if msg.content else "No response generated"
        # Fallback if no AI message found
        return result["messages"][-1].content if result["messages"] else "No response generated"
    else:
        return str(result)


def invoke_agent_windowed(
    query: str,
    window_start: str,
    window_end: str,
    window_duration: float,
    output_mode: str,
    conversation_history: list[dict] = None
) -> str:
    """
    Invoke the MoatTutor agent with explicit time window policy enforcement.
    
    This variant provides the agent with window metadata so it can enforce
    the appropriate output policy (rating, direction, or signals only).
    
    Args:
        query: Base natural language query
        window_start: Window start date (YYYY-MM-DD)
        window_end: Window end date (YYYY-MM-DD)
        window_duration: Window duration in years
        output_mode: One of "rating", "direction", or "signals"
        conversation_history: Optional conversation history
    
    Returns:
        The agent's response as a string
    """
    # Construct window-aware query with metadata
    window_context = f"""
[WINDOW METADATA]
- Analysis Period: {window_start} to {window_end} ({window_duration:.1f} years)
- Output Mode: {output_mode}
- Policy: {"Full rating allowed" if output_mode == "rating" else "Direction only (no rating)" if output_mode == "direction" else "Signals only (no moat analysis)"}

User Query: {query}
"""
    
    return invoke_agent(window_context, conversation_history)


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