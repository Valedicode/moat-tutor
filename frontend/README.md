## Frontend (Next.js)

MoatTutor frontend is a Next.js app that visualizes and explains economic moat analysis from the backend API.

It includes:

- Chat + tutoring interactions
- Overall moat views and radar charts
- Time-window moat analysis views
- Fundamentals-driven outputs (ROIC/WACC, valuation, uncertainty, capital allocation, financial health)

## Quick Start

From `frontend/`:

```bash
pnpm install
pnpm dev
```

The app runs at `http://localhost:3000`.

## Backend Dependency

The frontend expects the backend API to be running.

Start backend from `backend/`:

```bash
uvicorn main:app --reload --port 8000
```

Backend docs: `http://localhost:8000/docs`

## Environment Variables

Set this in a frontend `.env.local` file if your backend is not on default localhost:

```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

Notes:

- Most frontend API calls use same-origin paths (`/api/v1/...`) and rely on your dev setup/proxy.
- Streaming chat explicitly uses `NEXT_PUBLIC_BACKEND_URL` in `src/lib/moatTutorApi.ts`.

## Key Files

- `src/lib/moatTutorApi.ts`
  - Shared frontend API client/types
  - Moat assessment types (5-source taxonomy with `efficient_scale`)
  - Endpoints for moat, fundamentals, and chat flows

- `src/components/studio/views/OverallMoatView.tsx`
  - Overall moat score UI
  - Radar mapping to 5 factors

- `src/components/charts/MoatRadar.tsx`
  - Radar visualization for moat dimensions

## Scripts

```bash
pnpm dev     # start dev server
pnpm build   # production build
pnpm start   # serve production build
pnpm lint    # run eslint
```

## Troubleshooting

- If requests fail, verify backend is running on port `8000`.
- If streaming fails, check `NEXT_PUBLIC_BACKEND_URL`.
- If factor fields mismatch, ensure backend and frontend are both on the updated 5-source moat schema.
