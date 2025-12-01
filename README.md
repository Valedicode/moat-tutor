## MoatTutor

### Overview

MoatTutor is an LLM-powered agent that explains the historical behavior of **MOAT-style technology stocks** in clear, non-technical language.  
Instead of predicting prices, it focuses on **explainability**: connecting financial news, fundamentals, and price movements to long-term **economic moats** (durable competitive advantages such as network effects or switching costs).

The goal is to help non-finance users understand why a stock might have moved the way it did, using plain-language narratives grounded in real data.

---

### Features

- **Plain-language explanations** of key concepts like switching costs, network effects, and intangible assets.
- **Narratives linking events to price moves**, e.g., how specific news or fundamental changes relate to later rallies or drawdowns.
- **Integration of multiple data types**: financial news (text) plus historical price time series (OHLC + volume).

---

### Tech Stack

- **Agent & orchestration**: `LangChain` (with potential `LangGraph` for more complex, graph-based workflows).
- **Backend API**: `FastAPI` for serving the agent and data endpoints.
- **Frontend**: `Next.js` for a web UI to explore explanations and visualizations.

---

### High-Level Architecture

- **Data Layer**
  - Curated dataset of:
    - Selected MOAT-style technology companies and their moat characteristics.
    - Time-indexed financial news and company communications.
    - Aligned historical OHLCV price data.

- **Processing & Attribution Layer**
  - Event windows linking news timestamps to subsequent price behavior.
  - Optional ML models and feature attribution (e.g., SHAP) over engineered features to identify key drivers.

- **LLM Agent Layer**
  - Prompt templates that combine:
    - Relevant news snippets.
    - Price segments and simple derived metrics.
    - Company and moat metadata.
  - Components for:
    - Generating human-readable narratives.
    - Explaining financial concepts in simple terms.
    - Translating attribution outputs into user-friendly language.

- **Service & Interface Layer**
  - **FastAPI backend** exposing endpoints to:
    - Retrieve relevant data and context for a given company and time range.
    - Call the LangChain/LangGraph-based agent to generate explanations.
  - **Next.js frontend** to:
    - Select a company and period of interest.
    - Trigger explanation generation.
    - Display narratives, charts, and (optionally) attribution highlights.

---

### Data Inputs

- **Text data**
  - Financial news articles and headlines.
  - Company press releases and earnings summaries.

- **Time series data**
  - OHLCV price histories for selected MOAT-style technology stocks.
  - Simple derived metrics (returns, volatility, event-window moves, etc.).

All data is loaded from a **controlled, historical dataset** for reproducibility (no live trading or real-time data).

---

### Getting Started

- **Prerequisites**
  - Python 3.10+ for the `FastAPI` backend and LangChain/LangGraph agent.
  - Node.js 18+ for the `Next.js` frontend.
  - Access to an LLM API or local model (e.g., OpenAI or an open-source model).

1. **Clone the repository**
   ```bash
   git clone https://github.com/Valedicode/moat-tutor.git
   cd moat-tutor
   ```

2. **Frontend setup (Next.js)**
   Navigate to the frontend directory and install dependencies:
   ```bash
   cd frontend
   pnpm install
   ```

3. **Backend setup (FastAPI + LangChain)**
   Navigate to the backend directory and install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Run the application**
   - Start the backend server (from the `backend/` directory):
     ```bash
     uvicorn main:app --reload
     ```
   - Start the frontend development server (from the `frontend/` directory):
     ```bash
     pnpm dev
     ```