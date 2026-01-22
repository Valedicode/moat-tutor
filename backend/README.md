## Backend (FastAPI + LangChain Tutoring Agent)

MoatTutor is a **teaching financial agent** that explains stock behavior while actively tutoring users in financial concepts.

### Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create .env file with your OpenAI key
echo "LLM_PROVIDER=openai" > .env
echo "OPENAI_API_KEY=your_key_here" >> .env

# 3. Test the agent
python interactive_tutorial.py

# 4. Run the API server
uvicorn main:app --reload
```

**For detailed setup instructions**, see [`tutorial/SETUP.md`](tutorial/SETUP.md)

### What's Built

- **MoatTutor Agent** (`agent/moat_tutor.py`)
  - Teaching-first system prompt with 9-section response structure
  - MOAT framework education (5 characteristics)
  - Adaptive learning based on user expertise
  - Interactive features: comprehension checks, learning paths, concept definitions
  - 5 tools: news (with semantic search), prices, time series, moat characteristics, topic search
  - Support for OpenAI and local LLMs

- **Historical News Pipeline** (`services/fnspid_news_pipeline.py`)
  - Streams 45M+ rows from Hugging Face FNSPID dataset
  - Filters and deduplicates 142K+ news passages (2015-2023)
  - Generates OpenAI embeddings for semantic search
  - Supports 9 tickers: AAPL, NVDA, MSFT, AMD, GOOGL, AVGO, ORCL, CSCO, MU
  - Local storage: ~63 MB compressed

- **Semantic News Retrieval** (`services/fnspid_retrieval.py`)
  - Embedding-based similarity search
  - Date range filtering
  - Returns top-k most relevant passages
  - Integrated with agent tools

- **FastAPI Integration** (`main.py`)
  - `/chat` endpoint for natural language interaction
  - `/chat/stream` for streaming responses
  - `/charts/{ticker}` for price data
  - CORS enabled for frontend

- **Pedagogical Features** (see `tutorial/TUTORING_FEATURES.md`)
  - Concept definitions for every term used
  - 6 structured learning paths (Beginner, Analyst, Event-Chain, etc.)
  - Comprehension checks after every response
  - Active learning suggestions
  - Data transparency and honest limitations

### Historical News Data Setup

The backend includes a powerful historical news pipeline using the FNSPID dataset:

#### Check Data Status

```bash
python check_fnspid_data.py
```

#### Generate Embeddings (Optional)

**Note:** Embeddings may already be included. Only run this if you need to regenerate or add new tickers.

```bash
# Generate for specific tickers (~$1-2 per ticker via OpenAI API)
python -m services.fnspid_news_pipeline --tickers AAPL NVDA MSFT

# Generate for all supported tickers
python -m services.fnspid_news_pipeline

# Options:
# --max-rows N         # Limit rows for testing
# --no-embeddings      # Skip embedding generation
```

**Data Coverage:**
- ✅ AAPL: 30,655 passages (14.72 MB)
- ✅ NVDA: 22,122 passages (9.84 MB)
- ✅ MSFT: 20,708 passages (10.19 MB)
- ✅ AMD: 29,380 passages (13.87 MB)
- ✅ GOOGL: 1,632 passages (0.16 MB)
- ✅ AVGO: 3,824 passages (0.32 MB)
- ✅ ORCL: 13,622 passages (5.73 MB)
- ✅ CSCO: 1,443 passages (0.12 MB)
- ✅ MU: 18,901 passages (7.75 MB)
- ⚠️ PLTR: No historical data (IPO 2020)

**Total:** 142,287 passages, 62.71 MB

### Test the API

```bash
# General analysis (chronological summary)
curl -X POST "http://127.0.0.1:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain why AAPL moved from 2023-01-01 to 2023-06-30"}'

# Semantic search (topic-specific)
curl -X POST "http://127.0.0.1:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find news about NVDA AI chip demand",
    "ticker": "NVDA",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31"
  }'
```

Or visit: `http://127.0.0.1:8000/docs`


