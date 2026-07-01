# Moneyball Studio — Work Handoff

> Paste this whole file (or `@HANDOFF.md`) into the next session to continue.
> Last updated: 2026-07-01

## TL;DR for the next session

> I'm continuing a UI/UX + data-contract fix on Moneyball Studio (FastAPI +
> React/Vite + Postgres/pgvector in Docker). The **Internal Server Error is already
> fixed** and the backend is verified green. Backend, frontend metric contract,
> and player photos are done. **Remaining work: finish the UI/UX polish pass
> (task #4) and the final rebuild+verify (task #5).** Read `HANDOFF.md`, then
> continue from "Remaining work" below. Use the ui-ux-pro-max skill for the polish.

---

## What the app is

- **backend/** — FastAPI, asyncpg, pgvector. Endpoints:
  - `GET /api/players/` — full list w/ stats (client caches & filters in-browser)
  - `GET /api/players/{id}` — one player detail
  - `GET /api/players/{id}/similar` — cosine lookalikes (17-dim PCA `stats_vector`)
- **frontend/** — React 18 + Vite 6 + Tailwind v4 + framer-motion + recharts +
  react-query + react-router. ESPN-inspired dark theme. Pages: Browse, Player,
  Similar, Compare, NotFound.
- **Postgres** (pgvector/pgvector:pg16) seeded from FotMob data via `ingest/`.
- Everything runs via `docker-compose.yml`:
  - frontend → http://localhost (nginx, port 80)
  - backend  → http://localhost:8000
  - db       → localhost:5432  (container `moneyball_db`, db `football`)
  - pgadmin  → localhost:5050 (profile `tools`)

## Root cause of "Something went wrong / Internal Server Error" (FIXED)

The user reworked the stats pipeline: `player_season_stats` went from a 10-metric
model to **35 real metric columns + `stats_vector VECTOR(17)`**. But the API and
the entire frontend still referenced the **old 10 metric names**, 5 of which no
longer exist as columns. asyncpg threw `UndefinedColumnError: column
pss.progressive_passes_per90 does not exist` → 500 → frontend `ErrorState`
rendered "Something went wrong".

Two more latent breakages were found and fixed alongside it:
1. **Player photos 403'd** — FotMob player images are `.png`, ingestion stored `.jpg`.
2. **`category` semantics changed** — it now holds *specific* role labels
   ("Center Back", "Striker"…) and `main_position` uses codes incl. `DM/AM/RWB/LWB`,
   but the whole UI is built on 3 broad roles `Attack/Midfield/Defender`.

---

## DONE (verified)

### Task 1 — Backend metric schema (the 500) ✅
New canonical **12-metric set** (all map 1:1 to real DB columns):
`npxg_per90, shots_on_target_per90, xa_per90, big_chances_created_per90,
successful_passes_per90, successful_pass_rate, successful_dribbles_per90,
accurate_long_balls_per90, tackles_per90, interceptions_per90, recoveries_per90,
aerial_duel_success_rate`. Rate columns are stored **0–100** (render as %).

- `backend/models.py` — `PlayerStats` rewritten to the 12 fields.
- `backend/routers/players.py` — added `STAT_COLUMNS` tuple + `_stat_select(alias)`
  helper; both list & detail queries use it; `_build_stats()` shared by both
  endpoints (detail no longer hand-builds `PlayerStats`).

### Task 2 — Frontend metric contract ✅
- `frontend/src/api/types.ts` — `PlayerStats` matches the 12 fields; `MetricKey`
  comment updated.
- `frontend/src/lib/metrics.ts` — `METRICS` (12, with labels/short/isPercent/unit)
  and `METRIC_GROUPS` (Attacking / Possession & Progression / Defending & Duels).
- `frontend/src/components/PlayerCard.tsx` — `HOVER_METRICS` per category updated
  to valid keys.
- `npm run lint` (tsc -b --noEmit) passes clean.

### Task 3 — Player photos jpg→png ✅
- DB: `UPDATE players SET photo_url = regexp_replace(...,'\.jpg$','.png')` — all
  2491 rows updated (verified png=2491, jpg=0).
- `ingest/transformation.py` — `PLAYER_IMAGE_URL` comment + `.png` in
  `insert_players()` so re-ingests are correct.
- Note: club & league logos already resolve 200 (they were always `.png`).
- Existing memory `sofifa-image-hotlink.md`: photos still need
  `referrerPolicy="no-referrer"` (already set in `SmartImage.tsx`). FotMob serves
  fine but keep the no-referrer policy.

### Role normalization (new, done as part of the fix) ✅
- `backend/roles.py` (NEW) — `broad_role(category, main_position)` →
  Attack/Midfield/Defender; `role_categories()` / `role_positions()` for the SQL
  filter; `clean_position()` turns the `{}` ingestion artifact (37 players) into null.
- `backend/routers/players.py` & `similar.py` — output `category` is now the broad
  role; `main_position` is cleaned; the `?category=` SQL filter matches the broad
  role via label-set + position-code fallback.
- `frontend/src/components/PositionPitch.tsx` — added coords + names for
  `AM, DM, LWB, RWB, CF` so every code in the data plots on the pitch.
- **Verified API**: 2271 players, broad split Attack 675 / Defender 870 /
  Midfield 726; `?category=Defender` → 870, all Defender; null main_position = 37;
  list/detail/similar all HTTP 200.

Backend image was rebuilt (`docker compose up -d --build backend`) and is green.

---

## REMAINING WORK

### Task 4 — UI/UX polish pass (IN PROGRESS) ⏳
Goal: industry-grade polish. The codebase is already strong (good design system in
`src/index.css`, motion, skeletons). Use the **ui-ux-pro-max** skill. Candidate
improvements (verify each against current files before editing):

- **Accessibility (priority 1):**
  - Add `aria-label`s to icon-only controls (sort button, clear, compare links,
    chevrons, back buttons).
  - Range slider in `SimilarPage.tsx ThresholdControl` needs an `aria-label` /
    `aria-valuetext`.
  - Verify focus-visible rings on all interactive elements (cards have them; check
    dropdown rows, filter fields, segmented control).
  - `prefers-reduced-motion` is handled in CSS globally; double-check framer-motion
    page transitions also respect it (consider `useReducedMotion()`).
- **Radar with 12 axes** (`RadarChart.tsx`): was tuned for ~9 axes; confirm 12
  labels don't crowd — may need smaller tick font / radius tweak / shortened `short`.
- **Player profile**: surface the **league logo** (we have `club.league.logo_url`)
  next to club name in the hero — "incorporate the new logos" ask. Currently only
  club crest + country flag are shown.
- **Stat table** group titles now include "Possession & Progression" / "Defending &
  Duels" — verify the `w-28 sm:w-48` label column still fits the longer metric names.
- **NavBar**: only a single "Search" link; fine, but consider active-state polish.
- **SearchBar**: the "/" focus hotkey is commented out — re-enable cleanly
  (with input-guard) or remove the dangling `kbd` hint for consistency.
- **Empty/loading/error states** already exist (`states.tsx`) — keep consistent.
- Re-check 375px mobile + landscape, dark-mode contrast (it's dark-only).
- Don't introduce emojis as icons; keep the existing SVG icon style.

### Task 5 — Rebuild & verify end-to-end (PENDING) ⏳
```bash
# from repo root (Git Bash)
docker compose up -d --build           # rebuild frontend + backend
# frontend typecheck/build
cd frontend && npm run lint            # tsc -b --noEmit  (and `npm run build` for a full build)
```
Then verify in browser at **http://localhost** (NOT :5173 unless running `vite dev`):
- Browse grid loads, photos + crests + flags render, hover metrics show.
- Category segmented control (All/Attackers/Midfielders/Defenders) filters.
- Open a player → radar (12 axes), stat table, positions pitch, "Find similar".
- Similar page → threshold slider, position filter, compare CTA.
- Compare page → overlaid radar + metric breakdown.

Smoke-test commands used previously:
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/players/
PID=$(docker exec moneyball_db psql -U postgres -d football -t \
  -c "SELECT player_id FROM player_season_stats ORDER BY minutes_played DESC NULLS LAST LIMIT 1;" | tr -d ' ')
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8000/api/players/$PID"
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8000/api/players/$PID/similar?limit=5"
```

---

## Gotchas / environment notes

- **Windows + Git Bash**: use POSIX paths; `docker exec moneyball_db psql -U postgres
  -d football -c "..."` for DB. In SQL strings inside bash, escape backslashes
  (`'\\.jpg$'`).
- **Backend code is baked into the image** (no volume mount) → must
  `docker compose up -d --build backend` after editing Python. Frontend is also a
  built nginx image (rebuild to see changes at :80), or run `vite dev` at :5173 with
  the `/api` proxy for hot reload.
- DB data persists in the `pgdata` volume — the photo `UPDATE` and any data fixes
  survive restarts but are **not** in `schema.sql`; a fresh volume re-seed needs the
  `ingest/` pipeline (now `.png`-correct).
- `data/` working CSVs changed (git status shows many new `fotmob_*`/`mapped_*`
  files and deleted old ones) — that's the user's reworked pipeline, leave it.
- Metric **rate** columns (`successful_pass_rate`, `aerial_duel_success_rate`) are
  0–100 in the DB; `formatStat(..., isPercent=true)` renders them as `xx.x%`.

## Key files map

```
backend/
  models.py            PlayerStats = 12 metrics
  roles.py             NEW broad_role/role_categories/role_positions/clean_position
  routers/players.py   STAT_COLUMNS, _stat_select, _build_stats, list+detail
  routers/similar.py   cosine query; outputs broad role + clean position
  schema.sql           35-col player_season_stats + VECTOR(17) + hnsw index
frontend/src/
  api/types.ts         PlayerStats + MetricKey
  lib/metrics.ts       METRICS (12) + METRIC_GROUPS (3)
  lib/percentiles.ts   client percentile engine (iterates METRICS)
  components/RadarChart.tsx, StatTable.tsx, PlayerCard.tsx, PositionPitch.tsx,
             FilterBar.tsx, SmartImage.tsx, primitives.tsx, states.tsx
  pages/BrowsePage.tsx, PlayerPage.tsx, SimilarPage.tsx, ComparePage.tsx
ingest/transformation.py   .png player image URL; load pipeline
docker-compose.yml
```

## Open questions for the user (ask if relevant)

1. The 32-metric set (all `player_season_stats` columns) is now surfaced in the
   stat table, radar chart, and compare page — confirm this is the desired set.
2. You mentioned testing cosine similarity on a *smaller* set of players — is the
   current 2271-row DB the intended test slice, or should ingestion be re-run?
