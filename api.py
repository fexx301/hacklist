from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import os
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import get_hackathon, get_hackathons, get_last_scrape_times, get_stats, init_db, update_statuses
from scheduler import is_scraping, run_all_scrapers, start_scheduler

REFRESH_TOKEN = os.getenv("REFRESH_TOKEN", "")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    update_statuses()
    start_scheduler()
    yield


app = FastAPI(title="Hacklist API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Hackathon(BaseModel):
    id: int
    title: str
    url: str
    source: str
    start_date: str | None
    end_date: str | None
    prize: str | None
    description: str | None
    image_url: str | None
    status: str
    scraped_at: str


class Stats(BaseModel):
    total: int
    by_source: dict[str, int]
    by_status: dict[str, int]


class SourceScrape(BaseModel):
    status: str
    last_scraped: str


class DashboardStats(BaseModel):
    stats: Stats
    sources: dict[str, SourceScrape]


class RefreshResponse(BaseModel):
    status: str


class ScrapeStatus(BaseModel):
    scraping: bool


@app.get("/api/hackathons", response_model=list[Hackathon])
def list_hackathons(
    sources:   list[str] = Query(default=[]),
    statuses:  list[str] = Query(default=["upcoming", "ongoing"]),
    search:    str        = Query(default=""),
    has_prize: bool       = Query(default=False),
    limit:     int        = Query(default=500, ge=1, le=1000),
    offset:    int        = Query(default=0, ge=0),
):
    return get_hackathons(
        sources   = sources  or None,
        statuses  = statuses or None,
        search    = search   or None,
        has_prize = has_prize,
        limit     = limit,
        offset    = offset,
    )


@app.get("/api/stats", response_model=DashboardStats)
def dashboard_stats():
    return {
        "stats":   get_stats(),
        "sources": get_last_scrape_times(),
    }


@app.post("/api/refresh", response_model=RefreshResponse)
async def refresh(
    background_tasks: BackgroundTasks,
    x_refresh_token: str | None = Header(default=None),
):
    # Open by default for local use; set REFRESH_TOKEN in the environment
    # to require the X-Refresh-Token header (e.g. once deployed publicly).
    if REFRESH_TOKEN and x_refresh_token != REFRESH_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid refresh token")
    if is_scraping():
        return {"status": "already_running"}
    background_tasks.add_task(run_all_scrapers)
    return {"status": "started"}


@app.get("/api/status", response_model=ScrapeStatus)
def scrape_status():
    return {"scraping": is_scraping()}


def _ics_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
            .replace(";", "\\;")
            .replace(",", "\\,")
            .replace("\n", "\\n")
    )


def build_ics(h: dict) -> str:
    """Render a hackathon as an all-day iCalendar event (DTEND is exclusive)."""
    start = date.fromisoformat(h["start_date"])
    end   = date.fromisoformat(h["end_date"]) if h.get("end_date") else start
    dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Hacklist//hacklist//EN",
        "BEGIN:VEVENT",
        f"UID:hacklist-{h['id']}@hacklist",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART;VALUE=DATE:{start.strftime('%Y%m%d')}",
        f"DTEND;VALUE=DATE:{(end + timedelta(days=1)).strftime('%Y%m%d')}",
        f"SUMMARY:{_ics_escape(h['title'])}",
        f"URL:{h['url']}",
    ]
    if h.get("description"):
        lines.append(f"DESCRIPTION:{_ics_escape(h['description'][:500])}")
    lines += ["END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(lines) + "\r\n"


@app.get("/api/hackathons/{hackathon_id}/calendar.ics")
def hackathon_calendar(hackathon_id: int):
    h = get_hackathon(hackathon_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hackathon not found")
    if not h.get("start_date"):
        raise HTTPException(status_code=422, detail="Hackathon has no dates")
    return Response(
        content=build_ics(h),
        media_type="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="hackathon-{hackathon_id}.ics"'},
    )
