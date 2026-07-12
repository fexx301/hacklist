from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from db import get_hackathons, get_stats, get_last_scrape_times, init_db, update_statuses
from scheduler import run_all_scrapers, start_scheduler

app = FastAPI(title="Hackathon Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_scraping = False


@app.on_event("startup")
async def startup():
    init_db()
    update_statuses()
    start_scheduler()


@app.get("/api/hackathons")
def list_hackathons(
    sources:   list[str] = Query(default=[]),
    statuses:  list[str] = Query(default=["upcoming", "ongoing"]),
    search:    str        = Query(default=""),
    has_prize: bool       = Query(default=False),
):
    return get_hackathons(
        sources   = sources  or None,
        statuses  = statuses or None,
        search    = search   or None,
        has_prize = has_prize,
    )


@app.get("/api/stats")
def dashboard_stats():
    return {
        "stats":   get_stats(),
        "sources": get_last_scrape_times(),
    }


@app.post("/api/refresh")
async def refresh(background_tasks: BackgroundTasks):
    global _scraping
    if _scraping:
        return {"status": "already_running"}
    _scraping = True

    def do_scrape():
        global _scraping
        try:
            run_all_scrapers()
        finally:
            _scraping = False

    background_tasks.add_task(do_scrape)
    return {"status": "started"}


@app.get("/api/status")
def scrape_status():
    return {"scraping": _scraping}
