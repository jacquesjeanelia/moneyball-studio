# Moneyball Studio

A football scouting platform for the top 5 European leagues (2024/25). Search 1,700+ players, break down per-90 performance metrics against positional peers, and surface statistical lookalikes powered by pgvector cosine similarity.

## Features

- **Instant search & filters** — as-you-type search over name/club/nationality, with position, league, country and max-price filters (futbin-style). All filtering is client-side over a single cached dataset for zero-latency interaction.
- **Player profiles** — per-90 stat tables and percentile radars computed against positional peers, plus market value, age, height and preferred foot.
- **Statistical lookalikes** — vector similarity (pgvector cosine distance) with an adjustable similarity threshold.
- **Head-to-head compare** — two players side by side with an overlaid percentile radar and metric-by-metric breakdown. Reachable directly from any lookalike row.
- **Polished UX** — ESPN-inspired dark theme, route/hover/stagger animations (Framer Motion), graceful image fallbacks, code-split routes, URL-synced search state.

## Architecture

```
┌──────────────┐      /api/*       ┌──────────────┐      asyncpg      ┌──────────────┐
│  frontend    │ ────proxy───────▶ │   backend    │ ────────────────▶ │   Postgres   │
│ React + nginx│                   │   FastAPI    │                   │  + pgvector  │
│   :80        │                   │   :8000      │                   │   :5432      │
└──────────────┘                   └──────────────┘                   └──────────────┘
```

- **Frontend** — React 18 + TypeScript + Vite, React Router, TanStack Query, Framer Motion, Recharts, Tailwind v4. Built to static assets and served by nginx, which also proxies `/api` to the backend (same-origin → no CORS in the default setup).
- **Backend** — FastAPI + asyncpg with a connection pool. Three endpoints (below).
- **Data** — PostgreSQL 16 with the `pgvector` extension. Each player-season carries a 10-dimension normalized stat vector with an HNSW cosine index.

### API

| Method | Path | Description |
| ------ | ---- | ----------- |
| `GET` | `/api/players/` | List players. Query: `season`, `position`, `country_id`, `club_id`. Each row carries market value + season stats (enables client-side search/filter/percentiles). |
| `GET` | `/api/players/{id}` | Full player detail incl. season stats. Query: `season`. |
| `GET` | `/api/players/{id}/similar` | Top lookalikes by cosine similarity, same position. Query: `season`, `limit` (1–100). Returns `similarity_score` in `[0,1]`. |
| `GET` | `/health` | Liveness probe. |

## Quick start (Docker — full stack)

Requires Docker. Brings up Postgres, the API and the nginx-served frontend:

```bash
docker compose up -d --build
```

Then open **http://localhost**. The API is at **http://localhost:8000**; pgAdmin (optional) via `docker compose --profile tools up -d pgadmin` at **http://localhost:5050**.

> **First run / empty DB?** The schema is created automatically, but player data is loaded by the ingestion pipeline. If `SELECT count(*) FROM players` is 0, load it:
> ```bash
> # from the repo root, with the DB container running
> python ingest/transformation.py     # reads data/, scales features, loads Postgres
> ```

## Local development

**Backend** (needs the DB running — `docker compose up -d db`):

```bash
cd backend
pip install -r requirements.txt
# DATABASE_URL defaults to postgresql://postgres:postgres@localhost:5432/football
uvicorn main:app --reload --port 8000
```

**Frontend**:

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173, proxies /api to VITE_PROXY_TARGET (default :8011)
```

Point the dev proxy at your backend:

```bash
# frontend/.env.local
VITE_PROXY_TARGET=http://127.0.0.1:8000
```

## Deployment

The build is **deploy-agnostic** via a single env var, `VITE_API_BASE_URL` (baked at build time):

- **Empty (default)** — the app calls same-origin `/api`, proxied by nginx (Docker) or the Vite dev proxy. Recommended when frontend and API share an origin.
- **Set to a full origin** (e.g. `https://moneyball-api.onrender.com`) — the app calls that origin directly. Use this when hosting the frontend as a static site (Vercel/Netlify) with the API on a separate domain.

### Option A — single host (Docker)

```bash
docker compose up -d --build
```

Everything is served from one origin; no CORS configuration needed.

### Option B — static frontend (Vercel/Netlify) + hosted API

1. Deploy the backend + Postgres (Render/Railway/Fly). Set `CORS_ORIGINS` on the backend to your frontend URL, e.g. `CORS_ORIGINS=https://moneyball.vercel.app`.
2. Build the frontend pointing at the API:
   ```bash
   cd frontend
   VITE_API_BASE_URL=https://your-api-host npm run build
   # deploy ./dist  (SPA: rewrite all routes to /index.html)
   ```

The backend reads two env vars: `DATABASE_URL` and `CORS_ORIGINS` (comma-separated allowed origins).

## Data pipeline

`ingest/` sources player stats (SofaScore via ScraperFC) and bio/market data (Transfermarkt), fuzzy-matches them, scales the 10 feature metrics to `[0,1]`, and loads everything into Postgres with the stat vectors. See `ingest/ingestion.py` (sourcing/merge) and `ingest/transformation.py` (transform/load).

## Tech notes

- Percentile radars are computed client-side against each player's positional cohort — the FBref/StatsBomb convention — from the one cached player list.
- Routes that pull in Recharts (detail/similar/compare) are lazy-loaded, so the browse page ships ~110 KB gzipped.
- Player photos, club crests and flags degrade gracefully to initials/glyph fallbacks if a remote asset fails.
