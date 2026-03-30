## Backend (FastAPI + LangChain Moat Tutor)

MoatTutor backend provides a Morningstar-aligned tutoring workflow for economic moat analysis:

- Economic moat sources (official 5): Network Effects, Switching Costs, Intangible Assets, Cost Advantages, Efficient Scale
- ROIC vs WACC analysis with fade-period logic
- Capital Allocation rating (Exemplary / Standard / Poor)
- Financial Health assessment with deterministic No-Moat override
- 3-stage DCF fair value (Explicit -> Fade -> Perpetuity)
- Uncertainty-adjusted star rating cutoffs

### Quick Start

```bash
# 1) Install dependencies
pip install -r requirements.txt

# 2) Create .env
echo "LLM_PROVIDER=openai" > .env
echo "OPENAI_API_KEY=your_key_here" >> .env
echo "ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key" >> .env

# 3) Run API (port 8000)
uvicorn main:app --reload --port 8000
```

Then open `http://127.0.0.1:8000/docs`.

For detailed setup, see `tutorial/SETUP.md`.

## Core Modules

- `services/roic_calculator.py`
  - ROIC/NOPAT/Invested Capital series
  - Morningstar-style WACC building-block estimator
  - WACC detail breakdown endpoint support
  - Fade-period estimation for moat durability

- `services/capital_allocation.py`
  - Three-pillar capital allocation scoring:
    - Balance Sheet Management
    - Investment Strategy (ROIC vs WACC)
    - Shareholder Distributions
  - Rating output: `Exemplary | Standard | Poor`

- `services/financial_health.py`
  - Three-component financial health scoring:
    - Leverage
    - Liquidity
    - Cash Flow Sufficiency
  - Status output: `Healthy | Watch | Distressed | Critical`
  - `moat_override_flag` for deterministic No-Moat override

- `services/valuation_estimator.py`
  - 3-stage DCF fair value:
    - Stage I explicit forecast (years 1-5)
    - Stage II fade period (linked to moat durability)
    - Stage III perpetuity (Gordon Growth)
  - Equity bridge: EV -> Equity Value -> Fair Value/Share
  - Uncertainty rating + uncertainty-adjusted star rating bands

- `services/data_driven_moat_scorer.py`
  - Quantitative moat source scoring aligned to official 5-source taxonomy

- `services/moat_news_classifier.py`
  - Moat-source classification from historical news passages
  - Query bank aligned to official 5-source taxonomy

- `agent/moat_tutor.py`
  - Teaching-oriented agent prompt and tool orchestration
  - Includes tools for ROIC, valuation, uncertainty, WACC breakdown,
    capital allocation, financial health, moat-news classification, and resilience

## API Surface (Key Endpoints)

### Fundamentals

- `GET /api/v1/fundamentals/{ticker}/roic`
- `GET /api/v1/fundamentals/{ticker}/compare`
- `GET /api/v1/fundamentals/{ticker}/wacc`
- `GET /api/v1/fundamentals/{ticker}/summary`
- `GET /api/v1/fundamentals/{ticker}/valuation`
- `GET /api/v1/fundamentals/{ticker}/uncertainty`
- `GET /api/v1/fundamentals/{ticker}/capital-allocation`
- `GET /api/v1/fundamentals/{ticker}/financial-health`
- `GET /api/v1/fundamentals/{ticker}/moat-comparison`
- `GET /api/v1/fundamentals/{ticker}/resilience`
- `GET /api/v1/fundamentals/{ticker}/resilience-comparison`
- `GET /api/v1/fundamentals/{ticker}/moat-news`
- `GET /api/v1/fundamentals/{ticker}/milestones`

### Moat

- `GET /api/v1/moat/overall`
  - Runs full-window moat assessment and applies financial-health override logic.

### Chat

- `POST /api/v1/chat`
- `POST /api/v1/chat/stream`

## Historical News Data

The backend supports historical moat-news analysis using FNSPID + embeddings.

### Check status

```bash
python check_fnspid_data.py
```

### Generate/update embeddings (optional)

```bash
python -m services.fnspid_news_pipeline --tickers AAPL NVDA MSFT
python -m services.fnspid_news_pipeline
```

Optional flags:

- `--max-rows N`
- `--no-embeddings`

## Alpha Vantage Setup

Add to `.env`:

```bash
ALPHA_VANTAGE_API_KEY=your_key_here
ALPHA_VANTAGE_BASE_URL=https://www.alphavantage.co/query
```

Used for fundamentals and additional news coverage where applicable.

## Notes on Methodology

- WACC is implemented as a Morningstar-style building-block approximation for tutoring consistency (not raw beta CAPM).
- Financial health override is applied post-analysis for deterministic behavior.
- Star ratings use uncertainty-adjusted bands (higher uncertainty requires deeper discount for same star level).


