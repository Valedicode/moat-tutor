## Backend (FastAPI)

### Setup

From the repo root:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # on Windows
pip install -r requirements.txt
```

### Run the API

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000` with docs at `http://127.0.0.1:8000/docs`.


