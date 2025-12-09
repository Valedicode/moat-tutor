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
  - 3 mock tools: news, prices, moat characteristics
  - Support for OpenAI and local LLMs

- **FastAPI Integration** (`main.py`)
  - `/chat` endpoint for natural language interaction
  - CORS enabled for frontend

- **Pedagogical Features** (see `tutorial/TUTORING_FEATURES.md`)
  - Concept definitions for every term used
  - 6 structured learning paths (Beginner, Analyst, Event-Chain, etc.)
  - Comprehension checks after every response
  - Active learning suggestions
  - Data transparency and honest limitations

### Test the API

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain why AAPL stock moved from 2023-01-01 to 2023-02-28"}'
```

Or visit: `http://127.0.0.1:8000/docs`


