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
from services.roic_calculator import (
    check_roic_hurdle,
    compare_roic_to_peers as _compare_roic_to_peers_svc,
    compare_moat_profiles as _compare_moat_profiles_svc,
    estimate_wacc_detailed as _estimate_wacc_detailed_svc,
)
from services.valuation_estimator import (
    estimate_fair_value,
    calculate_uncertainty_rating,
)
from services.data_driven_moat_scorer import DataDrivenMoatScorer
from services.resilience_analyzer import (
    analyze_crisis_resilience,
    compare_resilience,
    CRISIS_PERIODS,
)
from services.moat_news_classifier import (
    classify_passages_by_moat_source,
    detect_moat_milestones as _detect_moat_milestones_svc,
)
from services.capital_allocation import assess_capital_allocation
from services.financial_health import assess_financial_health
from services.etf_holdings import (
    get_etf_tech_holdings as _get_etf_tech_holdings_svc,
    get_sector_for_ticker,
    is_moat_etf_holding,
    get_etf_summary,
    MOAT_TECH_SECTORS,
    ETF_AS_OF_DATE,
)

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
5. **Efficient Scale** - Market only supports limited competitors profitably due to natural size constraints
"""


# ============================================================================
# System Prompt
# ============================================================================

SYSTEM_PROMPT = f"""You are MoatTutor, an expert financial analyst and teacher that helps users understand economic moats -- the durable competitive advantages that protect companies' excess returns.

## Your Mission

Help users understand economic moats through data, reasoning, and clear teaching. You combine:
- **Price data**: 2000-2025 (20+ years via yfinance)
- **Financial news**: 2000-2023 via FNSPID historical archive, 2024+ via yfinance
- **Fundamental data (ROIC, financials)**: Typically 2006-2025 (varies by company, via Alpha Vantage)
- **Quantitative tools**: Valuation, uncertainty, resilience, milestone detection

**Data Coverage Note**: ROIC requires fundamental data (income statements, balance sheets) which typically starts 2006-2008. News and price data go back to 2000, allowing you to analyze early moat formation qualitatively even when quantitative ROIC isn't available for those years.

Your goal is to **reason and teach**, not to recite data. Always explain WHY something matters, not just WHAT the data shows. Adapt your response to what the user actually asks for.

## The MOAT Framework

{MOAT_CHARACTERISTICS}

## Core Principles

**DO:**
- Answer what the user actually asked -- match your response to their intent
- Be analytical, cautious, and explanatory
- Use clear causal chains: Signal -> Mechanism -> Moat Impact
- Teach the logic behind your conclusions -- always explain WHY, not just WHAT
- State data limitations clearly when present

**DON'T:**
- Force a rigid multi-section analysis when the user asks a simple question
- Repeat raw price data or list news items verbatim
- Describe daily movements, charts, or technical indicators unless explicitly requested
- Make predictions or provide investment advice
- Hallucinate specific numbers not in the data

## Teaching Principles (CRITICAL)

You are a teacher first, analyst second. Every response should educate:

**1. Explain WHY it matters**
- Bad: "ROIC is 33%, WACC is 10%"
- Good: "ROIC (33%) exceeds WACC (10%), meaning Apple earns 23% more than investors require. This lets Apple reinvest cash flows at 33% instead of 10%, compounding value 3x faster — the mathematical evidence of durable competitive advantages."

**2. Connect metrics to real-world mechanisms**
- Bad: "Economic profit is $31.8B"
- Good: "Economic profit ($31.8B annually) is the value created ABOVE what investors require. This excess profit funds ecosystem expansion, R&D, and share buybacks without diluting returns — perpetuating the moat."

**3. Use concrete examples**
- Bad: "High switching costs"
- Good: "Switching costs: When iPhone users consider Android, they lose iMessage, FaceTime, AirDrop, purchased apps, and years of iCloud photos. This migration friction is measurable — Apple's services revenue ($85B+) monetizes this lock-in."

**4. Acknowledge what you DON'T know**
- When ROIC data starts in 2006, acknowledge: "ROIC data begins in 2006. For 2000-2006, we can analyze moat formation through news (iPhone launch 2007, iPod era) and price, but lack quantitative proof via ROIC."
- When data is uncertain, say so: "Regulatory outcomes are unpredictable — this is a key uncertainty that could materially affect the moat."

**5. Progressive disclosure**
- Simple queries → concise teaching (2-4 sentences)
- Focused queries → add one teaching moment connecting data to moat logic
- Full analysis → comprehensive teaching throughout

**6. Use comparisons to anchor understanding**
- "NVDA's 30% ROIC vs AMD's 8% ROIC shows a 4x advantage in capital efficiency — NVDA creates $4 of value for every dollar of capital while AMD creates $1."
- "A 20-year fade period means competitors can't replicate these advantages for two decades — longer than most business cycles."

## Tool Usage

- Use available tools to gather data relevant to the user's question
- For historical queries (2000-2023):
  - If the user asks about a SPECIFIC topic or event (e.g., "AI chip demand", "earnings", "product launch"), 
    provide a query parameter to get_stock_news for semantic search with embeddings
  - If the user asks for GENERAL analysis (e.g., "why did the stock move"), omit the query for chronological summary
- For recent queries (2024+), the tool automatically uses yfinance
- Only call tools that are relevant to the question -- do not call every tool for every query

## Source Citation (CRITICAL)

When your response draws on news articles returned by `get_stock_news` or `search_news_by_topic`, you MUST do both of the following:

1. **Inline markers**: Place `[1]`, `[2]`, `[3]` etc. directly in your prose, immediately after the sentence or clause that draws on that article. The number must match the 1-based position of that article in the `[SOURCES_START]` block. Example: "NVIDIA announced its CUDA platform in 2006, cementing developer lock-in early on.[1]"

2. **Sources block**: Copy the `[SOURCES_START]...[SOURCES_END]` block from the tool output verbatim at the very end of your response, after all prose. Do NOT rephrase, reorder, or omit lines.

Additional rules:
- Do not fabricate inline markers or a sources block if the tool returned no `[SOURCES_START]` block.
- If multiple tool calls returned source blocks, keep only the one most relevant to your answer and use its indices for the inline markers.
- Inline markers should appear mid-sentence or at the sentence end — never on a line by themselves.

## Quantitative Moat Analysis Tools

You have access to a comprehensive suite of quantitative tools that provide MATHEMATICAL PROOF of economic moats:

### ROIC Analysis (Return on Invested Capital)

**Tools:**
1. `get_roic_analysis(ticker, years=10)` - Gets ROIC history, hurdle check, excess profit, and fade period
2. `compare_roic_to_peers(ticker, "PEER1,PEER2,PEER3", years=10)` - Single-dimension ROIC comparison vs peers
3. `compare_moat_to_peers(ticker, "PEER1,PEER2,PEER3", years=10)` - Multi-dimensional comparison (ROIC spread, margins, growth, economic profit, fade period)

**ROIC Formula:**
- ROIC = NOPAT / Invested Capital
- NOPAT = Operating Income x (1 - Tax Rate)
- Invested Capital = Equity + Debt - Excess Cash

**What ROIC Tells Us:**
- **ROIC > WACC** = Company earns more than its cost of capital = Value creation
- **ROIC < WACC** = Company destroys value = No moat
- **Sustained high ROIC (10+ years)** = Durable competitive advantage = Strong moat

**WACC Methodology (Morningstar-Style Building Blocks):**
WACC is NOT estimated using market beta or CAPM. It uses Morningstar's building-block approach:
- **Cost of Equity**: Base nominal return (~9.0%) adjusted by a **systematic risk category** (Below Average / Average / Above Average / Very High). The risk category is inferred from business stability (revenue volatility, operating leverage, financial leverage) rather than stock-price covariance.
- **Cost of Debt**: Risk-free base + inflation + a **credit spread category** (Low / Moderate / Elevated / High), tax-adjusted. The credit category is inferred from interest coverage and D/E ratio.
- **Capital Structure**: Uses normalized median historical debt-to-capital rather than today's market cap, avoiding distortion from price momentum or temporary market conditions.

This produces stable, explainable WACC estimates consistent with how Morningstar analysts actually set cost of capital.

**Teaching Guidance for ROIC:**
When presenting ROIC data, always explain:
1. **Why the spread matters**: "33% ROIC vs 10% WACC = 23 percentage point spread. This means every $100 of capital generates $33 of returns instead of the required $10 — enabling 3x faster compounding."
2. **What it enables**: "High ROIC lets companies reinvest profits at superior rates, fund ecosystem expansion, or return cash to shareholders — all without diluting returns."
3. **How it proves moats**: "Sustaining 30%+ ROIC for 20 years proves the company has something competitors can't replicate. If it were easy, competition would drive ROIC down to WACC."
4. **Coverage limitations**: "ROIC data typically starts 2006-2008 when fundamental statements become available. Earlier moat analysis relies on news and price patterns."

### Excess Profit (Economic Profit)

The ROIC analysis includes **excess profit** data:
- **ROIC-WACC Spread**: The percentage points of return above cost of capital (e.g., 30% ROIC - 10% WACC = 20% spread)
- **Economic Profit**: Dollar amount of value created = (ROIC - WACC) x Invested Capital
- **Cumulative Economic Profit**: Total excess value created over the analysis period

**Teaching Guidance for Economic Profit:**
Always explain economic profit in concrete terms:
- "Economic profit is the value created ABOVE what investors require. If a company has $31.8B in annual economic profit, it means the business generates $31.8B more value than if that same capital were deployed at the cost of capital."
- "Cumulative economic profit ($708B over 20 years) is the total excess value created by the moat. This isn't revenue or profit — it's the incremental value from competitive advantages."
- "High economic profit funds three things without reducing returns: (1) ecosystem expansion (App Store, services), (2) R&D and innovation, (3) shareholder returns (buybacks, dividends). This self-reinforcing cycle widens the moat."
- "If economic profit shrinks or turns negative, the moat is eroding — the company no longer creates value above what investors require."

### Fade Period (Moat Durability)

The ROIC analysis includes **fade period estimation**:
- **Stage I (Explicit Forecast)**: Recent actual ROIC data (high confidence)
- **Stage II (Fade Period)**: Estimated years until ROIC converges to WACC
- **Stage III (Terminal)**: ROIC = WACC (no excess returns)

**Classification (linked to 3-stage DCF):**
- Wide Moat: 15+ year fade period -> 20-year Stage II in DCF
- Narrow Moat: 8-14 year fade period -> 10-year Stage II in DCF
- No Moat: <8 years or ROIC already at/below WACC -> 5-year Stage II in DCF

**Teaching Guidance for Fade Period:**
Explain fade period in terms of competitive dynamics:
- "A 20-year fade period means competitors cannot replicate Apple's advantages for two decades. That's longer than the iPhone has existed. This durability comes from reinforcing loops — App Store attracts developers → more apps attract users → larger user base attracts more developers."
- "Fade period estimates are uncertain — they're projections based on ROIC trends. A company with stable/improving ROIC gets a longer fade; declining ROIC shortens it. Regulatory changes, technological disruption, or competitive breakthroughs could accelerate the fade."
- "Compare fade periods: NVDA (20+ years, Wide Moat) vs AMD (8 years, Narrow Moat) shows the difference between structural advantages (CUDA ecosystem, switching costs) vs cyclical success (good chips today, but easily matched tomorrow)."

### Fair Value & Price/Fair Value Ratio (3-Stage DCF)

**Tool:** `get_valuation_analysis(ticker)` - Morningstar-style 3-stage DCF fair value estimate

The DCF uses three stages linked to moat strength:
- **Stage I (Explicit Forecast, years 1-5)**: Full year-by-year FCF projection at estimated growth rate
- **Stage II (Fade, linked to moat rating)**: Growth fades linearly from current rate toward terminal rate. Wide Moat = 20-year fade, Narrow = 10, No Moat = 5
- **Stage III (Perpetuity)**: Gordon Growth Model at terminal growth rate (~3%)

Equity bridge: Enterprise Value = PV(Stage I) + PV(Stage II) + PV(Stage III) + Excess Cash. Then subtract debt to arrive at Equity Value, divide by shares for Fair Value per Share.

**5-Star Rating System (uncertainty-adjusted):**
Star rating cutoffs depend on the uncertainty level. Higher uncertainty requires a deeper discount:
- Low Uncertainty: 5-star at 80% of FV, 4-star at 90%
- Medium: 5-star at 70%, 4-star at 80%
- High: 5-star at 60%, 4-star at 75%
- Very High: 5-star at 50%, 4-star at 65%
- Extreme: 5-star at 25%, 4-star at 50%

**Teaching Moment**: "The 3-stage DCF reflects how moats affect value. A Wide Moat company gets a 20-year fade period because it takes that long for competitors to erode the advantage. This longer period of excess returns translates directly into higher fair value."

**Teaching Moment**: "The Price/Fair Value ratio tells us whether the market has already priced in a company's moat. But the SAME P/FV ratio means different things at different uncertainty levels. A stock at 70% of fair value is 5-star if uncertainty is Medium, but only 4-star if uncertainty is High."

### Uncertainty Rating

**Tool:** `get_uncertainty_analysis(ticker)` - Financial volatility assessment

**Rating Scale:**
- **Low**: Predictable business, stable revenues and margins (20% margin of safety)
- **Medium**: Some variability but fundamentally stable (30% margin of safety)
- **High**: Meaningful volatility in revenue or returns (40% margin of safety)
- **Very High**: Significant unpredictability (50% margin of safety)
- **Extreme**: Highly volatile or unproven business (60% margin of safety)

**Teaching Moment**: "Uncertainty determines HOW MUCH discount you need to buy safely. The star-rating cutoffs are now uncertainty-adjusted: a stock at 70% of fair value earns 5 stars under Medium uncertainty but only 4 stars under High uncertainty. Higher uncertainty = larger margin of safety required."

### Capital Allocation Assessment

**Tool:** `get_capital_allocation_analysis(ticker)` - Assesses management quality

Evaluates management's capital allocation decisions across three pillars:
- **Balance Sheet Management**: Leverage discipline, interest coverage, debt trajectory
- **Investment Strategy**: Whether reinvestment earns ROIC above WACC
- **Shareholder Distributions**: Dividend policy and buyback effectiveness

Ratings: **Exemplary** (score 4.5+/6), **Standard** (2.5-4.5), **Poor** (<2.5)

**Teaching Guidance**: "Capital allocation tells us whether management is a good steward of the moat. A company can have strong competitive advantages but destroy value through excessive debt, wasteful acquisitions, or inadequate shareholder returns. Exemplary allocators widen the moat; Poor allocators erode it."

### Financial Health Assessment

**Tool:** `get_financial_health_analysis(ticker)` - Evaluates value destruction risk

Assesses whether financial distress could destroy cumulative economic profit:
- **Leverage**: Debt/Equity, Debt/EBIT, interest coverage
- **Liquidity**: Current ratio, cash position relative to assets
- **Cash Flow Sufficiency**: FCF consistency, debt repayment capacity

Status: **Healthy**, **Watch**, **Distressed**, or **Critical**

**CRITICAL**: If financial health status is **Critical**, the system forces a **No-Moat** rating regardless of competitive advantages. This is the Morningstar "value destruction override" -- even a company with strong network effects or switching costs gets No Moat if it faces severe financial distress.

**Teaching Guidance**: "Financial health acts as a safety check. A company might have the strongest brand in its industry, but if it's drowning in debt with no cash flow to service it, those advantages don't matter -- the moat can't protect a sinking ship."

### Structural Moat Sources (Data-Driven)

**Tool:** `get_moat_characteristics(ticker)` - Identifies moat sources from financial data

Instead of relying on static profiles, this tool analyzes:
- High gross/operating margin (>35%) -> Intangible Assets / Pricing Power
- Low revenue volatility + positive growth -> Switching Costs
- Revenue growth > peers + consistency -> Network Effects
- ROIC > 25% sustained -> Cost Advantages
- High ROIC + stable trend + revenue stability -> Efficient Scale

**Connecting ROIC to Moat Sources:**
- **High ROIC + Network Effects**: Platform scales with low incremental capital.
- **High ROIC + Switching Costs**: Captive customers fund reinvestment at high returns.
- **High ROIC + Intangible Assets**: Brand/patents enable premium pricing with efficient capital use.
- **High ROIC + Cost Advantages**: Scale or unique resources lower costs vs peers.
- **Declining ROIC**: May signal moat erosion, increased competition, or capital intensity.

### Standardized Global Comparison

**Tool:** `compare_moat_to_peers(ticker, "PEER1,PEER2,PEER3")` - Multi-dimensional comparison

Compares companies across a standardized methodology:
- ROIC-WACC spread (excess return)
- Operating margin
- Revenue growth rate and consistency
- Economic profit (dollar value creation)
- Fade period (moat durability)

**Teaching Moment**: "The standardized comparison ensures objectivity--every company worldwide is measured by the same ruler. When NVDA's ROIC spread is 20% vs AMD's 5%, that's not opinion--it's mathematical evidence of superior value creation."

### News-to-Moat Source Classification

**Tool:** `analyze_moat_news(ticker, start_date, end_date)` - Classify news by moat source

Scans historical news and classifies passages into moat categories:
- Network Effects, Switching Costs, Intangible Assets, Cost Advantages, Efficient Scale
- Uses semantic similarity against a curated query bank per moat source
- Returns evidence passages grouped by source with confidence levels

**Teaching Moment**: "Moat sources leave fingerprints in the news. Patent filings signal intangible assets; enterprise adoption announcements signal switching costs. By classifying years of news, we can trace which moat sources are strengthening over time."

### Moat Milestone Detection

**Tool:** `detect_moat_milestones(ticker)` - Find the most significant moat events

Combines three signals to identify milestones:
1. **Price-anchored**: Notable price moves (>5%) with moat-relevant news within 3 days
2. **Moat-themed**: News that strongly matches moat source patterns
3. **ROIC overlay**: Connection to year-over-year ROIC changes

**Teaching Moment**: "A moat milestone is an event where the competitive landscape materially changed. The 2007 iPhone launch didn't just move Apple's stock--it created switching costs and ecosystem lock-in that still drive ROIC 18 years later."

### Price Resilience Analysis

**Tools:**
- `analyze_resilience(ticker, crisis)` - Drawdown and recovery during market crises
- `compare_resilience_to_peers(ticker, "PEER1,PEER2", crisis)` - Peer comparison during downturns

Available crises: `dot_com_bust`, `financial_crisis`, `covid_crash`, `rate_hike_2022`

Measures for each crisis:
- Peak-to-trough drawdown
- Recovery time (days to regain prior peak)
- Post-crisis 1-year and 3-year returns
- Long-term CAGR, Sharpe ratio, Sortino ratio, max drawdown (20-year metrics)

**Teaching Moment**: "Price resilience during crises is a real-world stress test for moats. A company with a wide moat should have shallower drawdowns and faster recovery because its competitive advantages persist even when the economy contracts. Compare NVDA's recovery to AMD's after 2022 and you'll see the moat in action."

**Teaching Moment (ROIC-Resilience Link)**: "Companies with high pre-crisis ROIC tend to recover faster because their business model generates returns that attract capital back. The moat protects the business; the business protects the stock price."

### MOAT ETF Layer (VanEck Morningstar Wide Moat ETF)

**Tool:** `get_etf_tech_sector_holdings(sub_sector?)` - Returns MOAT ETF technology sector holdings with portfolio weights

The VanEck Morningstar Wide Moat ETF (ticker: MOAT) tracks companies that Morningstar identifies as having sustainable competitive advantages (wide economic moats) trading at attractive valuations. The ETF's methodology directly reflects the moat framework you teach.

**Technology Sector Distribution (as of 2026-03-27, 22 companies across 4 sub-sectors):**

- **Software & SaaS (10):** MSFT, ADBE, CRM, ORCL, NOW, WDAY, VEEV, DDOG, TYL, FICO
- **Semiconductors & Hardware (5):** NVDA, NXPI, AMAT, AVGO, ENTG
- **Cybersecurity (2):** FTNT, PANW
- **Platforms & Data Infrastructure (5):** META, MSI, BR, TRU, CSGP

**Weight data from Excel:** The tool returns per-holding `pct_net_assets` (% of net assets), per-sub-sector `sector_weight_pct`, and `total_tech_weight_pct` for the aggregate technology sector share. Use these weights to:
- Compare how heavily the ETF is invested in each sub-sector (e.g., "Software & SaaS is the largest tech sub-sector at X% of net assets, reflecting Morningstar's view that this area has the deepest concentration of wide-moat companies at attractive valuations").
- Highlight weight differences across sub-sectors -- they reflect where Morningstar's methodology sees the deepest moats AND the best relative valuations converging.
- Contextualize individual holdings: a company with a higher weight signals stronger conviction (wider moat + bigger discount to fair value at rebalance).
- When summarizing the tech sector, always mention the overall tech weight (total_tech_weight_pct) to frame how large a role technology plays in the full MOAT ETF.

**How to use ETF context:**
- When analyzing a company, note if it is a MOAT ETF holding -- this is independent validation that Morningstar's equity research team identified a wide moat.
- ETF inclusion signals two things: (1) the company has durable competitive advantages, and (2) it was trading at an attractive valuation relative to Morningstar's fair value estimate at the time of rebalancing.
- Sub-sector grouping helps contextualize peer comparisons (e.g., comparing FTNT vs PANW within Cybersecurity, or NVDA vs AMAT within Semiconductors).
- If a user asks about the MOAT ETF, its technology holdings, or which companies Morningstar considers wide-moat, use the ETF tool to provide structured data.

**Teaching Guidance**: "Being included in the MOAT ETF means Morningstar's analyst team independently verified a wide economic moat AND the stock was trading below fair value at the last rebalance. This is a real-world validation of the moat framework -- the same methodology you're learning about (ROIC vs WACC, competitive advantages, fade periods) is what drives actual ETF construction. The tech sector represents a significant portion of the MOAT ETF, with Software & SaaS being the largest tech sub-sector -- weight differences across sub-sectors reflect Morningstar's assessment of where the deepest moats and best valuations converge."

## How to Respond (Adapt to User Intent)

**IMPORTANT**: Do NOT force a rigid multi-section structure on every response. Match your response format to what the user actually asked for. Read the user's message carefully and choose the right mode:

### Conversational / Conceptual Questions
When the user asks a general or conceptual question (e.g., "What is ROIC?", "Explain switching costs", "How does the fade period work?"):
- Answer directly and concisely (4-15 sentences)
- **Always explain WHY it matters**, not just what it is
- Include a concrete example from a real company (AAPL, NVDA, MSFT)
- Connect the concept to competitive dynamics or value creation
- Offer a follow-up question to deepen the discussion
- Do NOT produce a multi-section analysis or call unnecessary tools

**Example (Good):**
User: "What is ROIC?"
You: "ROIC (Return on Invested Capital) measures how efficiently a company converts capital into profits. It's calculated as NOPAT / Invested Capital. Why it matters: When ROIC exceeds the cost of capital (WACC, typically 10% for tech), the company creates value. For example, Apple's 33% ROIC vs 10% WACC means it generates $33 of profit for every $100 of capital, compared to the required $10. This 3x advantage lets Apple reinvest at superior rates or return cash without diluting returns. Sustained high ROIC (10+ years) is mathematical proof of a moat — if it were easy, competition would drive ROIC down to WACC. Would you like to see how Apple's ROIC compares to competitors, or understand what drives high ROIC?"

### Focused Data Questions
When the user asks a specific data question (e.g., "What is AAPL's ROIC?", "Compare NVDA to AMD", "How did MSFT perform during COVID?"):
- Call the relevant tool(s) -- only the ones needed
- Present the results clearly with **interpretation, not just numbers**
- **Add a teaching moment** connecting the data to moat logic — explain WHY the numbers matter
- Use comparisons or context to make abstract numbers concrete
- Do NOT force all 7 sections -- just answer the question with depth

**Example (Good):**
User: "What is AAPL's ROIC?"
You: [Call get_roic_analysis("AAPL")]
"Apple's ROIC (2006-2025): average 33.2%, recent years 50-64%, consistently above the 10% WACC hurdle for 20 straight years.

Why this matters: This 23 percentage point spread means Apple creates $31.8B in economic profit annually — value above what investors require. This excess lets Apple reinvest in ecosystem expansion (services, App Store) and shareholder returns without reducing ROIC. Sustaining 30%+ returns for two decades proves durable competitive advantages — if competitors could match this, they would, driving returns down. The 20-year fade period estimate suggests these advantages (ecosystem lock-in, network effects, scale) will persist for decades.

Would you like to see how this compares to Microsoft or Google, or understand which moat sources drive this ROIC?"

### Full Moat Analysis
When the user explicitly asks for a comprehensive moat analysis (e.g., "Analyze NVDA's moat", "Give me a full analysis of AAPL"):
- Use the structured analysis format below
- Call multiple tools to build a complete picture
- This is the ONLY mode where the full structure is expected

### Full Analysis Structure (use ONLY when user asks for comprehensive moat analysis)

When performing a full analysis, cover these elements (in whatever order is natural):

1. **Executive Takeaway** (2-4 sentences): Is the moat strengthening, weakening, or stable? What drives it?

2. **Price Signal**: What does price behavior suggest about market belief? (Trend, volatility, reactions to events)

3. **News Themes**: Cluster into 2-3 moat-relevant themes with causal reasoning.

4. **Moat Reasoning**: Use Signal -> Mechanism -> Moat Impact chains for the relevant dimensions:
   - Switching Costs, Network Effects, Cost Advantages, Intangible Assets, Efficient Scale

5. **Uncertainty**: 1-2 key uncertainties or counterfactuals.

6. **Valuation Context** (if relevant): P/FV ratio, excess profit, fade period, uncertainty rating.

7. **Overall Conclusion**: "Overall Assessment: [Wide/Narrow/None] Moat (Confidence: [Low/Medium/High])"

After the conclusion, append the hidden structured assessment for programmatic extraction:

**[MOAT_ASSESSMENT_START]**
```json
{{
  "switching_costs": {{"score": 0, "direction": "Stable", "confidence": "Low", "rationale": "..."}},
  "network_effects": {{"score": 0, "direction": "Stable", "confidence": "Low", "rationale": "..."}},
  "intangible_assets": {{"score": 0, "direction": "Stable", "confidence": "Low", "rationale": "..."}},
  "cost_advantages": {{"score": 0, "direction": "Stable", "confidence": "Low", "rationale": "..."}},
  "efficient_scale": {{"score": 0, "direction": "Stable", "confidence": "Low", "rationale": "..."}},
  "overall_score": 0,
  "overall_rating": "None",
  "overall_confidence": "Low",
  "capital_allocation_rating": "Standard",
  "financial_health_status": "Watch",
  "assessment_period": "start to end"
}}
```
**[MOAT_ASSESSMENT_END]**

Scoring: 0-5 scale (5 = exceptional, 4+ = strong, 3-3.9 = moderate, 2-2.9 = weak, <2 = minimal).
Wide Moat: score >= 4.0 with at least 2 strong dimensions.
Narrow: 2.5-3.9 or only 1 strong dimension.
None: < 2.5 or all dimensions < 3.0.

---

## Time Window Guidelines

When the user provides a date range, the analysis credibility depends on the window length:

- **8+ years**: Full structural moat rating is appropriate (Wide/Narrow/None).
- **3-7 years**: Provide directional insight (Strengthening/Stable/Weakening) but note that a structural rating requires a longer window.
- **< 3 years**: Focus on tactical signals and market sentiment. Note the limitation briefly -- do not refuse to answer, just be transparent about what a short window can and cannot tell us.

For ROIC-related questions, default to 10 years unless the user specifies otherwise.

---

## Objective

Help the user understand economic moat dynamics through data and reasoning. Teach through causal chains and clear explanations. Adapt to what the user needs -- sometimes that is a full analysis, sometimes it is a single number with context.
"""


# ============================================================================
# Agent Tools
# ============================================================================

@tool
def get_stock_news(ticker: str, start_date: str, end_date: str, query: str = None) -> str:
    """
    Retrieves financial news articles for a stock ticker within a date range.
    
    This tool intelligently routes between data sources:
    - Historical dates (2000-2023): Uses FNSPID dataset with 142K+ curated news passages (20+ years)
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
    Identifies the structural competitive advantages (moat sources) for a company
    using financial data analysis.
    
    Analyzes financial metrics to identify moat sources:
    - Operating margins -> Intangible Assets / Pricing Power
    - Revenue growth consistency -> Network Effects
    - Revenue stability -> Switching Costs
    - ROIC vs WACC -> Cost Advantages
    - Combined indicators -> Efficient Scale
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'NVDA')
    
    Returns:
        Data-driven moat source identification with evidence
    """
    try:
        scorer = DataDrivenMoatScorer()
        result = scorer.identify_moat_sources(ticker, use_cache=True)
        
        if not result.get("sources"):
            return result.get("summary", f"No moat sources identified for {ticker}.")
        
        # Format response
        response = f"Moat Source Analysis for {result['ticker']}:\n\n"
        response += f"Primary Moat: {result['primary_moat']}\n\n"
        
        for source_name, source_data in result["sources"].items():
            display_name = source_name.replace("_", " ").title()
            response += f"  {display_name} ({source_data['strength']}):\n"
            response += f"    Evidence: {source_data['evidence']}\n"
            response += f"    Metric: {source_data['metric']}\n\n"
        
        response += f"Summary: {result['summary']}\n"
        
        return response
        
    except Exception as e:
        return f"Error analyzing moat characteristics for {ticker}: {str(e)}"


@tool
def search_news_by_topic(ticker: str, query: str, start_date: str, end_date: str) -> str:
    """
    Search historical news for a specific topic using semantic similarity.
    
    This tool uses embeddings to find news passages that are semantically
    similar to your query. It's best for finding specific events, themes,
    or topics in historical news data (2000-2023).
    
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
    Calculate Return on Invested Capital (ROIC) with excess profit and fade period.
    
    ROIC is the definitive quantitative proof of economic moats. This tool provides:
    - ROIC history and hurdle check (ROIC vs WACC)
    - Excess Profit: ROIC-WACC spread and dollar economic profit per year
    - Fade Period: Estimated years of excess returns (Stage I/II/III classification)
    
    Args:
        ticker: Stock ticker symbol (e.g., 'NVDA', 'AAPL', 'MSFT')
        years: Number of years to analyze (default: 10)
    
    Returns:
        Comprehensive ROIC analysis with excess profit and fade period
    
    Example:
        get_roic_analysis("NVDA", 10) returns ROIC analysis showing NVDA's
        30%+ average ROIC, $XX billion excess profit, and 20+ year fade.
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
        response += f"Hurdle Passed: {'Yes' if result['hurdle_passed'] else 'No'}\n\n"
        
        # Excess Profit section
        response += "--- Excess Profit (Economic Profit) ---\n"
        response += f"Avg ROIC-WACC Spread: {result.get('avg_roic_wacc_spread_pct', 0):+.2f} percentage points\n"
        avg_ep = result.get('avg_economic_profit', 0)
        cum_ep = result.get('cumulative_economic_profit', 0)
        response += f"Avg Annual Economic Profit: ${avg_ep:,.0f}\n"
        response += f"Cumulative Economic Profit ({result['years_analyzed']}yr): ${cum_ep:,.0f}\n\n"
        
        # Fade Period section
        fade = result.get('fade_period', {})
        if fade:
            response += "--- Fade Period (Moat Durability) ---\n"
            fade_years = fade.get('estimated_fade_years', 'N/A')
            response += f"Estimated Fade Period: {fade_years} years\n"
            response += f"Stage: {fade.get('stage', 'N/A').replace('_', ' ').title()}\n"
            response += f"Durability: {fade.get('durability', 'N/A').title()}\n"
            if fade.get('stage_description'):
                response += f"Stages: {fade['stage_description']}\n"
            if fade.get('explanation'):
                response += f"Analysis: {fade['explanation']}\n"
            response += "\n"
        
        # Interpretation
        if result['hurdle_passed']:
            response += "Interpretation:\n"
            response += f"{result['ticker']} demonstrates a STRONG ECONOMIC MOAT. "
            response += f"With an average ROIC of {result['avg_roic_pct']:.1f}% consistently exceeding its cost of capital ({result['wacc_pct']:.1f}%), "
            response += f"the company creates ${avg_ep:,.0f} in annual economic profit -- value above what investors require. "
            
            if fade and fade.get('estimated_fade_years', 0) >= 15:
                response += f"The estimated {fade_years}-year fade period indicates these advantages are expected to persist for decades."
            elif fade and fade.get('estimated_fade_years', 0) >= 8:
                response += f"The estimated {fade_years}-year fade period suggests durable but not exceptional moat longevity."
            
            response += "\n\n"
            
            if result['roic_trend'] == "strengthening":
                response += "The strengthening trend suggests the moat is widening.\n"
            elif result['roic_trend'] == "stable":
                response += "The stable trend suggests the moat remains durable.\n"
        else:
            response += "Interpretation:\n"
            response += f"The ROIC data suggests {result['ticker']} may not have a strong economic moat. "
            if result['avg_roic_pct'] < result['wacc_pct']:
                response += "Average ROIC below WACC indicates the company destroys value.\n"
            else:
                response += "While ROIC exceeds WACC, the inconsistency suggests competitive advantages may be weak or temporary.\n"
        
        # Year-by-year breakdown with economic profit
        response += "\nRecent ROIC & Economic Profit History:\n"
        for year_data in result['annual_data'][:5]:
            above_marker = "[PASS]" if year_data['above_wacc'] else "[FAIL]"
            ep = year_data.get('economic_profit', 0)
            spread = year_data.get('roic_wacc_spread_pct', 0)
            response += (
                f"  {year_data['year']}: ROIC {year_data['roic_pct']:.2f}% "
                f"(spread: {spread:+.2f}%, EP: ${ep:,.0f}) {above_marker}\n"
            )
        
        return response
        
    except Exception as e:
        return f"Error calculating ROIC for {ticker}: {str(e)}"


@tool
def get_wacc_breakdown(ticker: str) -> str:
    """
    Get a detailed WACC (Weighted Average Cost of Capital) breakdown.

    Uses a Morningstar-style building-block approach -- NOT market beta or CAPM.

    Shows:
    - Cost of Equity: base nominal return +/- systematic risk category
    - Cost of Debt: risk-free + credit spread, tax-adjusted
    - Capital Structure: normalized historical weights (not today's market cap)
    - Final WACC with full explanation of each component

    This is essential for teaching WHY a company has a particular cost of capital
    and how it relates to moat analysis (ROIC vs WACC spread).

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'NVDA')

    Returns:
        Full WACC breakdown with methodology explanation
    """
    try:
        result = _estimate_wacc_detailed_svc(ticker, use_cache=True)

        if "error" in result:
            return f"Unable to estimate WACC for {ticker}: {result['error']}"

        response = f"WACC Analysis for {result['ticker']} (Morningstar-Style Building Blocks):\n\n"
        response += f"WACC: {result['wacc_pct']:.2f}%\n\n"

        coe = result.get("cost_of_equity", {})
        response += f"--- Cost of Equity: {coe.get('coe_pct', 'N/A')}% ---\n"
        response += f"  Base nominal return: {result['assumptions']['base_nominal_coe_pct']:.1f}% "
        response += f"(real {result['assumptions']['real_market_return_pct']:.1f}% + "
        response += f"inflation {result['assumptions']['inflation_expectation_pct']:.1f}%)\n"
        response += f"  Systematic risk category: {coe.get('systematic_risk_category', 'N/A')}\n"
        response += f"  Risk premium adjustment: {coe.get('risk_premium_pct', 0):+.2f}%\n\n"

        cod = result.get("cost_of_debt", {})
        response += f"--- Cost of Debt (after-tax): {cod.get('aftertax_cod_pct', 'N/A')}% ---\n"
        response += f"  Pre-tax cost of debt: {cod.get('pretax_cod_pct', 'N/A')}%\n"
        response += f"  Credit risk category: {cod.get('credit_risk_category', 'N/A')}\n"
        response += f"  Credit spread: {cod.get('credit_spread_pct', 'N/A')}%\n"
        response += f"  Tax rate: {cod.get('tax_rate_pct', 'N/A')}%\n\n"

        cs = result.get("capital_structure", {})
        response += f"--- Capital Structure ---\n"
        response += f"  Equity weight: {cs.get('equity_weight_pct', 'N/A')}%\n"
        response += f"  Debt weight: {cs.get('debt_weight_pct', 'N/A')}%\n"
        response += f"  Source: {cs.get('source', 'N/A')}\n"

        return response
    except Exception as e:
        return f"Error estimating WACC for {ticker}: {str(e)}"


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
        
        result = _compare_roic_to_peers_svc(ticker, peer_list, years=years, use_cache=True)
        
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


@tool
def get_valuation_analysis(ticker: str) -> str:
    """
    Estimate fair (intrinsic) value using a simplified DCF model and calculate
    the Price/Fair Value ratio with a star rating (1-5).
    
    Uses Free Cash Flow projections, discounted at WACC, with terminal value.
    Includes uncertainty-adjusted fair value and margin of safety recommendation.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'NVDA')
    
    Returns:
        Fair value estimate, P/FV ratio, star rating, and DCF assumptions
    
    Example:
        get_valuation_analysis("AAPL") returns fair value, P/FV ratio of 0.85
        (3-star, fairly valued), with DCF breakdown.
    """
    try:
        result = estimate_fair_value(ticker, use_cache=True)
        
        if "error" in result:
            return f"Unable to estimate fair value for {ticker}: {result['error']}"
        
        response = f"Fair Value Analysis for {result['ticker']}:\n\n"
        
        fv = result.get('fair_value_per_share', 0)
        adj_fv = result.get('adjusted_fair_value', 0)
        price = result.get('current_price')
        pfv = result.get('price_to_fair_value')
        stars = result.get('star_rating', 3)
        disc = result.get('discount_premium_pct')
        
        response += f"Fair Value Per Share: ${fv:.2f}\n"
        response += f"Adjusted Fair Value (with margin of safety): ${adj_fv:.2f}\n"
        
        if price:
            response += f"Current Market Price: ${price:.2f}\n"
        if pfv:
            response += f"Price / Fair Value: {pfv:.2f}\n"
        
        response += f"Star Rating: {'*' * stars} ({stars}/5)\n"
        
        if disc is not None:
            if disc > 0:
                response += f"Trading at {abs(disc):.1f}% DISCOUNT to fair value\n"
            else:
                response += f"Trading at {abs(disc):.1f}% PREMIUM to fair value\n"
        
        # Uncertainty
        unc_rating = result.get('uncertainty_rating', 'N/A')
        mos = result.get('margin_of_safety_pct', 'N/A')
        response += f"\nUncertainty Rating: {unc_rating}\n"
        response += f"Recommended Margin of Safety: {mos}%\n"
        
        # DCF assumptions
        dcf = result.get('dcf_assumptions', {})
        response += f"\nDCF Assumptions:\n"
        response += f"  WACC: {dcf.get('wacc_pct', 'N/A')}%\n"
        response += f"  FCF Growth Rate: {dcf.get('fcf_growth_rate_pct', 'N/A')}%\n"
        response += f"  Terminal Growth: {dcf.get('terminal_growth_rate_pct', 'N/A')}%\n"
        response += f"  Base FCF: ${dcf.get('base_fcf', 0):,.0f}\n"
        response += f"  Projection Years: {dcf.get('projection_years', 'N/A')}\n"
        
        # Recent FCF history
        fcf_hist = result.get('fcf_history', [])
        if fcf_hist:
            response += f"\nRecent FCF History:\n"
            for h in fcf_hist:
                response += f"  {h['year']}: FCF ${h['fcf']:,.0f} (Revenue: ${h['revenue']:,.0f})\n"
        
        return response
        
    except Exception as e:
        return f"Error estimating fair value for {ticker}: {str(e)}"


@tool
def get_uncertainty_analysis(ticker: str) -> str:
    """
    Calculate an uncertainty rating based on financial volatility metrics.
    
    Assesses revenue volatility, ROIC volatility, financial leverage, and
    operating leverage to determine how predictable the company's future
    cash flows are. Higher uncertainty requires a larger margin of safety.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'NVDA')
    
    Returns:
        Uncertainty rating (Low to Extreme), component scores, and margin of safety
    
    Example:
        get_uncertainty_analysis("AAPL") might return "Low" uncertainty with
        a 20% recommended margin of safety.
    """
    try:
        result = calculate_uncertainty_rating(ticker, use_cache=True)
        
        response = f"Uncertainty Analysis for {result['ticker']}:\n\n"
        response += f"Uncertainty Rating: {result['uncertainty_rating']}\n"
        response += f"Uncertainty Score: {result['uncertainty_score']:.2f} / 4.0\n"
        response += f"Recommended Margin of Safety: {result['margin_of_safety_pct']}%\n\n"
        
        # Component details
        components = result.get('components', {})
        if components:
            response += "Component Analysis:\n"
            for name, comp in components.items():
                display_name = name.replace("_", " ").title()
                response += f"  {display_name}: {comp['label']} (score: {comp['score']}/4)\n"
        
        response += f"\n{result.get('explanation', '')}\n"
        
        return response
        
    except Exception as e:
        return f"Error calculating uncertainty for {ticker}: {str(e)}"


@tool
def compare_moat_to_peers(ticker: str, peer_tickers_str: str, years: int = 10) -> str:
    """
    Multi-dimensional moat comparison: ROIC spread, margins, growth, economic profit, fade period.
    
    This provides a standardized, globally comparable methodology that goes beyond
    single-metric (ROIC-only) comparison. Each company is measured by the same ruler.
    
    Args:
        ticker: Primary ticker to analyze (e.g., 'NVDA')
        peer_tickers_str: Comma-separated peer tickers (e.g., 'AMD,INTC,AVGO')
        years: Number of years to analyze (default: 10)
    
    Returns:
        Multi-dimensional comparison table with advantages highlighted
    """
    try:
        peer_list = [p.strip().upper() for p in peer_tickers_str.split(',') if p.strip()]
        
        if not peer_list:
            return "Error: Please provide at least one peer ticker (comma-separated)."
        
        result = _compare_moat_profiles_svc(ticker, peer_list, years=years, use_cache=True)
        
        if "error" in result:
            return f"Unable to compare moat profiles: {result['error']}"
        
        primary = result.get('primary_profile', {})
        
        response = f"Multi-Dimensional Moat Comparison ({result.get('period', 'N/A')}):\n\n"
        
        # Build comparison table
        all_profiles = [primary] + result.get('peer_profiles', [])
        
        response += f"{'Ticker':<8} {'ROIC%':>8} {'Spread%':>9} {'OpMarg%':>9} {'RevGrw%':>9} {'EconProfit':>14} {'Fade(yr)':>10}\n"
        response += "-" * 72 + "\n"
        
        for p in all_profiles:
            t = p.get('ticker', '?')
            roic = p.get('avg_roic_pct', '-')
            spread = p.get('roic_wacc_spread_pct', '-')
            margin = p.get('avg_op_margin_pct', '-')
            growth = p.get('avg_revenue_growth_pct', '-')
            ep = p.get('avg_economic_profit', '-')
            fade = p.get('fade_years', '-')
            
            roic_s = f"{roic:.1f}" if isinstance(roic, (int, float)) else str(roic)
            spread_s = f"{spread:+.1f}" if isinstance(spread, (int, float)) else str(spread)
            margin_s = f"{margin:.1f}" if isinstance(margin, (int, float)) else str(margin)
            growth_s = f"{growth:.1f}" if isinstance(growth, (int, float)) else str(growth)
            ep_s = f"${ep:,.0f}" if isinstance(ep, (int, float)) else str(ep)
            fade_s = f"{fade}" if fade != '-' else str(fade)
            
            marker = " <--" if t == ticker.upper() else ""
            response += f"{t:<8} {roic_s:>8} {spread_s:>9} {margin_s:>9} {growth_s:>9} {ep_s:>14} {fade_s:>10}{marker}\n"
        
        # Peer averages
        peer_avgs = result.get('peer_averages', {})
        if peer_avgs:
            response += "-" * 72 + "\n"
            response += f"{'PeerAvg':<8}"
            for key in ['avg_roic_pct', 'roic_wacc_spread_pct', 'avg_op_margin_pct', 'avg_revenue_growth_pct', 'avg_economic_profit', 'fade_years']:
                val = peer_avgs.get(key)
                if val is not None:
                    if key == 'avg_economic_profit':
                        response += f" ${val:>12,.0f}"
                    elif key == 'roic_wacc_spread_pct':
                        response += f" {val:>8+.1f}"
                    elif key == 'fade_years':
                        response += f" {val:>9.0f}"
                    else:
                        response += f" {val:>8.1f}"
                else:
                    response += f" {'N/A':>8}"
            response += "\n"
        
        # Advantages summary
        advantages = result.get('advantages', {})
        if advantages:
            response += "\nAdvantages vs Peer Average:\n"
            labels = {
                'avg_roic_pct': 'ROIC',
                'roic_wacc_spread_pct': 'ROIC-WACC Spread',
                'avg_op_margin_pct': 'Operating Margin',
                'avg_revenue_growth_pct': 'Revenue Growth',
                'avg_economic_profit': 'Economic Profit',
                'fade_years': 'Fade Period',
            }
            for key, adv in advantages.items():
                label = labels.get(key, key)
                diff = adv['difference']
                sign = "+" if diff > 0 else ""
                status = "ADVANTAGE" if adv['advantage'] else "DISADVANTAGE"
                response += f"  {label}: {sign}{diff:.1f} ({status})\n"
        
        return response
        
    except Exception as e:
        return f"Error comparing moat profiles: {str(e)}"


@tool
def analyze_moat_news(ticker: str, start_date: str = "", end_date: str = "") -> str:
    """
    Classify historical news into moat source categories using semantic analysis.
    
    Scans FNSPID news passages and classifies them by which moat source they
    relate to (Network Effects, Switching Costs, Intangible Assets, etc.)
    using a curated query bank and embedding similarity.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'NVDA')
        start_date: Optional start date YYYY-MM-DD (empty string for all)
        end_date: Optional end date YYYY-MM-DD (empty string for all)
    
    Returns:
        News passages classified by moat source with evidence
    """
    try:
        sd = start_date if start_date else None
        ed = end_date if end_date else None
        result = classify_passages_by_moat_source(ticker, start_date=sd, end_date=ed)
        
        if "error" in result:
            return f"Unable to classify news for {ticker}: {result['error']}"
        
        response = f"Moat News Classification for {result['ticker']} ({result['date_range']}):\n\n"
        response += f"Total classified passages: {result['total_classified']}\n"
        
        if result.get("primary_source"):
            response += f"Primary moat signal: {result['primary_source'].replace('_', ' ').title()}\n\n"
        
        counts = result.get("source_counts", {})
        response += "Moat Source Distribution:\n"
        for source, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            response += f"  {source.replace('_', ' ').title()}: {count} passages\n"
        
        response += "\nTop Evidence by Source:\n"
        for source, events in result.get("sources", {}).items():
            if not events:
                continue
            display = source.replace("_", " ").title()
            response += f"\n--- {display} ---\n"
            for e in events[:3]:  # Top 3 per source
                response += f"  [{e['date']}] (sim: {e['similarity']:.3f}, {e['strength']})\n"
                response += f"    {e['headline']}\n"
                response += f"    {e['passage_text'][:200]}...\n"
        
        return response
        
    except Exception as e:
        return f"Error analyzing moat news for {ticker}: {str(e)}"


@tool
def detect_moat_milestones(ticker: str) -> str:
    """
    Identify the most significant moat milestones in a company's history.
    
    Combines three signals to find milestones:
    1. Price-anchored events: Notable price moves (>5%) with moat-relevant news
    2. Moat-themed scans: News that strongly matches moat source patterns
    3. ROIC overlay: Connection to year-over-year ROIC changes
    
    Each milestone is scored by price impact and news relevance.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'NVDA', 'MSFT')
    
    Returns:
        Ranked milestones with timeline, moat source classification, and ROIC context
    """
    try:
        result = _detect_moat_milestones_svc(ticker, top_n=15)
        
        if "error" in result and not result.get("milestones"):
            return f"Unable to detect milestones for {ticker}: {result.get('error', 'Unknown error')}"
        
        milestones = result.get("milestones", [])
        timeline = result.get("timeline", [])
        dist = result.get("moat_source_distribution", {})
        
        response = f"Moat Milestones for {result['ticker']}:\n"
        response += f"Total candidates analyzed: {result.get('total_candidates', 0)}\n\n"
        
        if dist:
            response += "Moat Source Distribution:\n"
            for source, count in sorted(dist.items(), key=lambda x: x[1], reverse=True):
                response += f"  {source.replace('_', ' ').title()}: {count}\n"
            response += "\n"
        
        response += "Top Milestones (by significance score):\n\n"
        for i, m in enumerate(milestones[:10], 1):
            source_display = m["moat_source"].replace("_", " ").title()
            price_str = f" | Price: {m['price_impact_pct']:+.1f}%" if m.get("price_impact_pct") else ""
            response += f"{i}. [{m['date']}] {m['headline']}\n"
            response += f"   Source: {source_display} | Score: {m['milestone_score']:.3f} | Sim: {m['similarity']:.3f}{price_str}\n"
            if m.get("roic_context"):
                response += f"   ROIC: {m['roic_context']}\n"
            response += f"   {m['passage_text'][:180]}...\n\n"
        
        if timeline:
            response += "\nChronological Timeline:\n"
            for m in timeline:
                source_display = m["moat_source"].replace("_", " ").title()
                response += f"  {m['date']}: [{source_display}] {m['headline'][:80]}\n"
        
        return response
        
    except Exception as e:
        return f"Error detecting milestones for {ticker}: {str(e)}"


@tool
def get_capital_allocation_analysis(ticker: str) -> str:
    """
    Assess management's capital allocation quality for a company.

    Evaluates three pillars:
    1. Balance Sheet Management - leverage discipline and debt serviceability
    2. Investment Strategy - whether reinvestment earns ROIC above WACC
    3. Shareholder Distributions - dividend policy and buyback effectiveness

    Rating: Exemplary / Standard / Poor (each pillar scored 0-2, total 0-6).

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'NVDA')

    Returns:
        Capital allocation rating with pillar scores and explanation
    """
    try:
        result = assess_capital_allocation(ticker, use_cache=True)

        response = f"Capital Allocation Assessment for {result['ticker']}:\n\n"
        response += f"Rating: {result['capital_allocation_rating']} (score {result['overall_score']:.1f}/6.0)\n\n"

        for pillar_name, pillar_data in result["pillar_scores"].items():
            display = pillar_name.replace("_", " ").title()
            response += f"  {display}: {pillar_data['score']:.1f}/2.0\n"
            response += f"    {pillar_data['rationale']}\n\n"

        response += f"Summary: {result['explanation']}\n"
        return response
    except Exception as e:
        return f"Error assessing capital allocation for {ticker}: {str(e)}"


@tool
def get_financial_health_analysis(ticker: str) -> str:
    """
    Assess financial health and value destruction risk for a company.

    Evaluates whether financial distress could destroy cumulative economic
    profit. If risk is Critical, forces a No-Moat override regardless of
    competitive advantages.

    Components:
    - Leverage (Debt/Equity, interest coverage, Debt/EBIT)
    - Liquidity (current ratio, cash position)
    - Cash Flow Sufficiency (FCF consistency, debt repayment capacity)

    Status: Healthy / Watch / Distressed / Critical
    Override: moat_override_flag = true forces No-Moat rating

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'NVDA')

    Returns:
        Financial health status, risk assessment, and override flag
    """
    try:
        result = assess_financial_health(ticker, use_cache=True)

        response = f"Financial Health Assessment for {result['ticker']}:\n\n"
        response += f"Status: {result['financial_health_status']}\n"
        response += f"Value Destruction Risk: {result['value_destruction_risk']:.0%}\n"
        response += f"Moat Override Flag: {'YES - forces No Moat' if result['moat_override_flag'] else 'No'}\n\n"

        for comp_name, comp_data in result["components"].items():
            display = comp_name.replace("_", " ").title()
            response += f"  {display}: {comp_data['score']:.1f}/4.0\n"
            response += f"    {comp_data['rationale']}\n\n"

        response += f"Summary: {result['explanation']}\n"
        return response
    except Exception as e:
        return f"Error assessing financial health for {ticker}: {str(e)}"


@tool
def analyze_resilience(ticker: str, crisis: str = "") -> str:
    """
    Analyze how a company performed during market crises.
    
    Calculates drawdown, recovery time, and post-crisis returns for each
    major market downturn (Dot-Com Bust, 2008 Financial Crisis, COVID-19,
    2022 Rate Hikes). Also provides long-term CAGR and risk-adjusted metrics.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'NVDA')
        crisis: Optional crisis ID to analyze a single crisis.
                Options: 'dot_com_bust', 'financial_crisis', 'covid_crash', 'rate_hike_2022'
                Leave empty for all crises.
    
    Returns:
        Crisis resilience analysis with drawdowns, recovery times, and long-term metrics
    """
    try:
        cid = crisis if crisis else None
        result = analyze_crisis_resilience(ticker, crisis_id=cid)
        
        crises = result.get("crises", [])
        long_term = result.get("long_term_metrics", {})
        
        response = f"Resilience Analysis for {result['ticker']}:\n\n"
        
        if not crises:
            response += "No crisis data available (ticker may not have been listed during these periods).\n"
        else:
            response += "Crisis Performance:\n"
            for c in crises:
                response += f"\n  {c['label']} ({c['period']}):\n"
                response += f"    Drawdown: {c['drawdown_pct']:.1f}%\n"
                response += f"    Trough: ${c['trough_price']:.2f} on {c['trough_date']}\n"
                if c["recovery_days"] is not None:
                    response += f"    Recovery: {c['recovery_days']} days (by {c['recovery_date']})\n"
                else:
                    response += f"    Recovery: Not yet recovered in available data\n"
                if c["post_crisis_1yr_return_pct"] is not None:
                    response += f"    1-Year Post-Crisis Return: {c['post_crisis_1yr_return_pct']:+.1f}%\n"
                if c["post_crisis_3yr_return_pct"] is not None:
                    response += f"    3-Year Post-Crisis Return: {c['post_crisis_3yr_return_pct']:+.1f}%\n"
        
        if long_term:
            response += f"\nLong-Term Metrics ({long_term.get('period', 'N/A')}, {long_term.get('years', 'N/A')} years):\n"
            response += f"  CAGR: {long_term.get('cagr_pct', 'N/A')}%\n"
            response += f"  Annualized Volatility: {long_term.get('annualized_volatility_pct', 'N/A')}%\n"
            response += f"  Sharpe Ratio: {long_term.get('sharpe_ratio', 'N/A')}\n"
            response += f"  Sortino Ratio: {long_term.get('sortino_ratio', 'N/A')}\n"
            response += f"  Max Drawdown: {long_term.get('max_drawdown_pct', 'N/A')}%\n"
        
        return response
        
    except Exception as e:
        return f"Error analyzing resilience for {ticker}: {str(e)}"


@tool
def compare_resilience_to_peers(ticker: str, peer_tickers_str: str, crisis: str = "") -> str:
    """
    Compare how a company and its peers performed during market crises.
    
    Shows which companies had shallower drawdowns, faster recovery, and
    better post-crisis returns. Helps validate whether moats provide
    price protection during downturns.
    
    Args:
        ticker: Primary ticker (e.g., 'NVDA')
        peer_tickers_str: Comma-separated peer tickers (e.g., 'AMD,INTC,AVGO')
        crisis: Optional crisis ID ('dot_com_bust', 'financial_crisis', 'covid_crash', 'rate_hike_2022')
    
    Returns:
        Peer comparison table with drawdowns, recovery, and relative performance
    """
    try:
        peer_list = [p.strip().upper() for p in peer_tickers_str.split(",") if p.strip()]
        if not peer_list:
            return "Error: Please provide at least one peer ticker."
        
        cid = crisis if crisis else None
        result = compare_resilience(ticker, peer_list, crisis_id=cid)
        
        crisis_comp = result.get("crisis_comparison", [])
        lt_comp = result.get("long_term_comparison", [])
        
        response = f"Resilience Comparison: {result['ticker']} vs {', '.join(result['peers'])}:\n\n"
        
        if crisis_comp:
            # Group by crisis
            by_crisis: dict[str, list] = {}
            for row in crisis_comp:
                c_label = row.get("crisis", "Unknown")
                if c_label not in by_crisis:
                    by_crisis[c_label] = []
                by_crisis[c_label].append(row)
            
            for c_label, rows in by_crisis.items():
                response += f"--- {c_label} ---\n"
                response += f"{'Ticker':<8} {'Drawdown':>10} {'Recovery':>12} {'1yr Post':>10} {'3yr Post':>10}\n"
                response += "-" * 54 + "\n"
                for r in rows:
                    dd = f"{r['drawdown_pct']:.1f}%"
                    rec = f"{r['recovery_days']}d" if r.get("recovery_days") else "N/A"
                    p1 = f"{r['post_crisis_1yr_return_pct']:+.1f}%" if r.get("post_crisis_1yr_return_pct") is not None else "N/A"
                    p3 = f"{r['post_crisis_3yr_return_pct']:+.1f}%" if r.get("post_crisis_3yr_return_pct") is not None else "N/A"
                    marker = " <--" if r["ticker"] == ticker.upper() else ""
                    rel = ""
                    if r.get("relative_vs_peers_pct") is not None:
                        rel = f" (rel: {r['relative_vs_peers_pct']:+.1f}%)"
                    response += f"{r['ticker']:<8} {dd:>10} {rec:>12} {p1:>10} {p3:>10}{marker}{rel}\n"
                response += "\n"
        else:
            response += "No crisis comparison data available.\n\n"
        
        if lt_comp:
            response += "Long-Term Comparison:\n"
            response += f"{'Ticker':<8} {'CAGR':>8} {'Sharpe':>8} {'Sortino':>9} {'MaxDD':>8}\n"
            response += "-" * 45 + "\n"
            for lt in lt_comp:
                cagr = f"{lt.get('cagr_pct', 0):.1f}%"
                sharpe = f"{lt.get('sharpe_ratio', 0):.2f}"
                sortino = f"{lt.get('sortino_ratio', 0):.2f}"
                maxdd = f"{lt.get('max_drawdown_pct', 0):.1f}%"
                marker = " <--" if lt["ticker"] == ticker.upper() else ""
                response += f"{lt['ticker']:<8} {cagr:>8} {sharpe:>8} {sortino:>9} {maxdd:>8}{marker}\n"
        
        return response
        
    except Exception as e:
        return f"Error comparing resilience: {str(e)}"


@tool
def get_etf_tech_sector_holdings(sub_sector: str = "") -> str:
    """
    Get MOAT ETF technology sector holdings grouped by sub-sector.

    The VanEck Morningstar Wide Moat ETF (MOAT) holds companies with wide
    economic moats trading at attractive valuations. This tool returns the
    technology sector breakdown across Software & SaaS, Semiconductors &
    Hardware, Cybersecurity, and Platforms & Data Infrastructure.

    Args:
        sub_sector: Optional filter (e.g. "Software", "Semiconductors",
                    "Cybersecurity", "Platforms"). Leave empty for all.
    """
    import json

    data = _get_etf_tech_holdings_svc(sub_sector=sub_sector or None)
    return json.dumps(data, indent=2)


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
        get_moat_characteristics,       # Data-driven moat source identification
        search_news_by_topic,            # Semantic search in historical news
        get_roic_analysis,               # ROIC + excess profit + fade period
        get_wacc_breakdown,              # Morningstar-style WACC breakdown
        compare_roic_to_peers,           # Single-dimension ROIC peer comparison
        get_valuation_analysis,          # Fair value (DCF) + P/FV ratio + star rating
        get_uncertainty_analysis,        # Uncertainty rating + margin of safety
        compare_moat_to_peers,           # Multi-dimensional peer comparison
        analyze_moat_news,              # News-to-moat-source classification
        detect_moat_milestones,         # Milestone detection (price + news + ROIC)
        get_capital_allocation_analysis,  # Capital allocation rating
        get_financial_health_analysis,   # Financial health + moat override
        analyze_resilience,             # Crisis drawdown and recovery analysis
        compare_resilience_to_peers,    # Peer resilience comparison
        get_etf_tech_sector_holdings,   # MOAT ETF technology sector holdings
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
    if output_mode == "rating":
        policy_note = "Full rating allowed - MUST include structured moat assessment JSON block with [MOAT_ASSESSMENT_START] and [MOAT_ASSESSMENT_END] markers"
    elif output_mode == "direction":
        policy_note = "Direction only (no rating) - provide direction assessment but no Wide/Narrow/None rating"
    else:
        policy_note = "Signals only (no moat analysis) - tactical signals and market sentiment only"
    
    window_context = f"""
[WINDOW METADATA]
- Analysis Period: {window_start} to {window_end} ({window_duration:.1f} years)
- Output Mode: {output_mode}
- Policy: {policy_note}

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