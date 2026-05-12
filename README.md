# MoatTutor

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-339933?logo=nodedotjs&logoColor=white)](https://nodejs.org/)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-1.x-121212?logo=langchain&logoColor=white)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.x-1C3C3C)](https://github.com/langchain-ai/langgraph)

[![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![pnpm](https://img.shields.io/badge/pnpm-frontend%20package%20manager-f6921e?logo=pnpm&logoColor=white)](https://pnpm.io/)

[![Forks](https://img.shields.io/github/forks/Valedicode/moat-tutor?style=social)](https://github.com/Valedicode/moat-tutor/network/members)
[![Stars](https://img.shields.io/github/stars/Valedicode/moat-tutor?style=social)](https://github.com/Valedicode/moat-tutor/stargazers)
[![Contributors](https://img.shields.io/github/contributors/Valedicode/moat-tutor)](https://github.com/Valedicode/moat-tutor/graphs/contributors)

[![Issues](https://img.shields.io/github/issues/Valedicode/moat-tutor)](https://github.com/Valedicode/moat-tutor/issues)
[![Last Commit](https://img.shields.io/github/last-commit/Valedicode/moat-tutor)](https://github.com/Valedicode/moat-tutor/commits/main)
[![Pull Requests](https://img.shields.io/github/issues-pr/Valedicode/moat-tutor)](https://github.com/Valedicode/moat-tutor/pulls)

---

## Overview

MoatTutor is an LLM-powered agent that explains the historical behavior of **MOAT-style technology stocks** in clear, non-technical language.
Instead of predicting prices, it focuses on **explainability**: connecting financial news, fundamentals, and price movements to long-term **economic moats** (durable competitive advantages such as network effects or switching costs).

The current backend also includes a Morningstar-aligned research flow for tutoring:
- ROIC vs WACC moat test with building-block WACC assumptions
- Capital Allocation rating (Exemplary / Standard / Poor)
- Financial Health status with deterministic No-Moat override
- 3-stage DCF fair value (Explicit -> Fade -> Perpetuity)
- Uncertainty-adjusted star-rating cutoffs

The goal is to help non-finance users understand why a stock might have moved the way it did, using plain-language narratives grounded in real data.

---

## Features

- **Plain-language explanations** of key concepts like switching costs, network effects, and intangible assets.
- **Narratives linking events to price moves**, e.g., how specific news or fundamental changes relate to later rallies or drawdowns.
- **Integration of multiple data types**: financial news (text) plus historical price time series (OHLC + volume).
- **Morningstar-style tutoring workflow**: moat assessment, valuation, uncertainty, and risk overlays.

---

## Tech Stack

- **Languages**: **Python** (3.10+) for the backend and agent; **TypeScript** for the Next.js app.
- **Agent & orchestration**: **LangChain** and **LangGraph** for LLM calls, tools, and graph-style workflows.
- **Backend API**: **FastAPI** (with **Uvicorn**) for serving the agent and data endpoints.
- **Frontend**: **Next.js** and **React** for the web UI; **Tailwind CSS** for styling; **Recharts** for charts. **pnpm** is the package manager for the Next.js app (`pnpm install` / `pnpm dev`).

---

## High-Level Architecture

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

## Data Inputs

- **Historical News Data (FNSPID)**
  - 142,287 curated news passages from 2015-2023
  - Semantic search with OpenAI embeddings
  - 9 tickers with full coverage: AAPL, NVDA, MSFT, AMD, GOOGL, AVGO, ORCL, CSCO, MU
  - Stored locally as compressed passages + embeddings

- **Recent News Data (yfinance)**
  - Real-time news for all supported tickers
  - Typically covers last 30 days
  - Used for queries after 2023

- **Alpha Vantage Fundamentals / Supplemental News**
  - Fundamental statements used for ROIC, WACC, capital allocation, financial health, and valuation
  - Supplemental coverage for recent periods where needed

- **Time series data**
  - OHLCV price histories for selected MOAT-style technology stocks
  - Simple derived metrics (returns, volatility, event-window moves, etc.)

---

## Getting Started

### Prerequisites

- Python 3.10+ for the `FastAPI` backend and LangChain/LangGraph agent.
- Node.js 18+ for the `Next.js` frontend.
- Access to an LLM API (e.g., OpenAI API key).

### 1. Clone the repository

```bash
git clone https://github.com/Valedicode/moat-tutor.git
cd moat-tutor
```

### 2. Backend setup (FastAPI + LangChain)

```bash
cd backend
pip install -r requirements.txt
```

For complete backend capabilities and API endpoints, see `backend/README.md`.

Create a `.env` file in the `backend/` directory:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
LLM_STREAMING=true
```

#### Start the backend server

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### 3. Frontend setup (Next.js)

```bash
cd frontend
pnpm install
pnpm dev
```

The frontend will be available at `http://localhost:3000`.

---

## Contributors

This project was developed as part of the **Research Focus Class** at **RWTH Aachen University**, in the **i5** group.

MoatTutor was developed by **[Kevin Ha](https://github.com/Valedicode)**, with supervision from **Er Jin**, **Yixin Peng**, and **Prof. Stefan Decker**.

---