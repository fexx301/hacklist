# Hacklist

Hacklist aggregates online hackathons from six sources — **Devpost, MLH, Devfolio, Unstop, HackerEarth, and Twitter/X** — into one searchable dashboard, so you don't have to check each platform individually. A Python backend scrapes and stores listings on a daily schedule and serves them over a small API; a Next.js frontend lets you filter by source, status, and prize, sort the results, and share filtered views by URL.

## Architecture

The app runs as **two processes**:

| Part | Stack | Port | Entry point |
|------|-------|------|-------------|
| Backend API | FastAPI + APScheduler + SQLite | **8001** | `api.py` |
| Frontend | Next.js (App Router) + Tailwind | **3000** | `frontend/` |

- The frontend calls the backend at the URL in `frontend/.env.local` (`NEXT_PUBLIC_API_URL`, default `http://localhost:8001`), so **both must be running**.
- Scrapers live in `scrapers/` (one module per source). `scheduler.py` runs all of them every 24 hours; the first launch with an empty database also kicks off an immediate scrape.
- Data is stored in SQLite (`hackathons.db`). Twitter scraping uses `twscrape`, which keeps its own account store in `accounts.db`. Both `*.db` files are git-ignored.

There is also an alternative all-in-one **Streamlit** UI in `app.py` (no separate frontend needed) — see [Alternative: Streamlit UI](#alternative-streamlit-ui).

## Prerequisites

- **Python 3.14** (a virtualenv is already checked in at `.venv/`)
- **Node.js** (for the Next.js frontend; dependencies are in `frontend/node_modules`)

## Setup

### 1. Backend environment

The backend reads credentials from a `.env` file at the repo root. Copy the example and fill it in:

```bash
cp .env.example .env
```

The only credentials are for **Twitter/X**, and they are **optional** — they're used solely by the Twitter scraper. Use a throwaway/burner account; the other five sources need no credentials.

```
TWITTER_USERNAME=...
TWITTER_PASSWORD=...
TWITTER_EMAIL=...
TWITTER_EMAIL_PASSWORD=...
```

If you don't supply them, the other scrapers still work — the Twitter scrape will simply fail and be logged.

If you need to (re)install Python dependencies:

```bash
.venv/bin/pip install -r requirements.txt
```

### 2. Frontend environment

`frontend/.env.local` points the UI at the backend:

```
NEXT_PUBLIC_API_URL=http://localhost:8001
```

## Running

Start the **backend** (terminal 1):

```bash
.venv/bin/uvicorn api:app --host 127.0.0.1 --port 8001
```

Start the **frontend** (terminal 2):

```bash
cd frontend
npm run dev
```

Then open **http://localhost:3000**.

On first run with an empty database, the backend triggers a background scrape — give it ~30 seconds and refresh, or hit **Refresh now** in the sidebar.

## API

The backend exposes a small JSON API (consumed by the frontend):

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/api/hackathons` | List hackathons. Query params: `sources`, `statuses`, `search`, `has_prize`. |
| `GET`  | `/api/stats` | Totals by source/status + per-source last-scrape times. |
| `POST` | `/api/refresh` | Trigger a background re-scrape of all sources. |
| `GET`  | `/api/status` | Whether a scrape is currently running. |

## Alternative: Streamlit UI

`app.py` is a self-contained Streamlit dashboard over the same database and scrapers — handy if you don't want to run the separate frontend:

```bash
.venv/bin/streamlit run app.py
```

## Project layout

```
api.py          FastAPI backend (serves the Next.js frontend)
app.py          Streamlit UI (alternative, standalone)
scheduler.py    Runs all scrapers; daily 24h job
db.py           SQLite access + status logic
scrapers/       One module per source (devpost, mlh, devfolio, unstop, hackerearth, twitter)
frontend/       Next.js + Tailwind dashboard
```
