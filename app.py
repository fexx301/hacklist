from __future__ import annotations

import logging
import threading
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from db import get_hackathons, get_last_scrape_times, get_stats, init_db
from scheduler import run_all_scrapers, start_scheduler

logging.basicConfig(level=logging.INFO)

# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Hackathon Tracker",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* card hover effect */
[data-testid="stVerticalBlockBorderWrapper"] {
    transition: box-shadow .15s;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,.12);
}
/* tighten metric labels */
[data-testid="stMetricLabel"] { font-size: .8rem !important; }
/* badge pill helper */
.badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 12px;
    font-size: .68rem;
    font-weight: 700;
    letter-spacing: .03em;
}
</style>
""", unsafe_allow_html=True)

SOURCE_COLORS = {
    "devpost":     "#0070f3",
    "mlh":         "#e7243e",
    "devfolio":    "#6c63ff",
    "unstop":      "#ff6b35",
    "hackerearth": "#44cc11",
    "twitter":     "#1a1a2e",
}
STATUS_COLORS = {
    "upcoming": ("#2e7d32", "#e8f5e9"),
  "ongoing":  ("#1565c0", "#e3f2fd"),
    "past":     ("#757575", "#f5f5f5"),
}

ALL_SOURCES = list(SOURCE_COLORS.keys())

# ── one-time initialisation (survives Streamlit reruns) ──────────────────────
@st.cache_resource
def _boot():
    init_db()
    start_scheduler()
    stats = get_stats()
    if stats["total"] == 0:
        # First launch — kick off an immediate background scrape
        t = threading.Thread(target=run_all_scrapers, daemon=True)
        t.start()
    return True

_boot()

# ── sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚡ Hackathon Tracker")
    st.caption("Online hackathons, aggregated daily.")
    st.divider()

    st.subheader("Filters")
    sel_sources  = st.multiselect("Source",  ALL_SOURCES, placeholder="All sources")
    sel_statuses = st.multiselect("Status",  ["upcoming", "ongoing"], default=["upcoming", "ongoing"])
    has_prize    = st.checkbox("Has prize info only")
    search       = st.text_input("Search", placeholder="AI, Web3, React…")

    st.divider()

    if st.button("⟳  Refresh now", type="primary", use_container_width=True):
        with st.spinner("Scraping all sources…"):
            run_all_scrapers()
        st.success("Done! Data updated.")
        st.rerun()

    # Per-source scrape health
    st.subheader("Last scraped")
    times = get_last_scrape_times()
    for src in ALL_SOURCES:
        info = times.get(src)
        if info:
            ts  = info["last_scraped"][:10]
            ico = "✅" if info["status"] == "success" else "❌"
            st.caption(f"{ico} **{src}** — {ts}")
        else:
            st.caption(f"⏳ **{src}** — never")

# ── header metrics ────────────────────────────────────────────────────────────
stats = get_stats()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total",    stats["total"])
c2.metric("Upcoming", stats["by_status"].get("upcoming", 0))
c3.metric("Ongoing",  stats["by_status"].get("ongoing",  0))
c4.metric("Sources",  len(stats["by_source"]))

st.divider()

# ── fetch hackathons ──────────────────────────────────────────────────────────
hackathons = get_hackathons(
    sources  = sel_sources  or None,
    statuses = sel_statuses or None,
    search   = search       or None,
    has_prize= has_prize,
)

# ── empty state ───────────────────────────────────────────────────────────────
if not hackathons:
    stats_total = get_stats()["total"]
    if stats_total == 0:
        st.info(
            "🚀 **First-time setup** — a background scrape is running now. "
            "Refresh the page in about 30 seconds to see results."
        )
    else:
        st.warning("No hackathons match your current filters.")
    st.stop()

st.caption(f"Showing **{len(hackathons)}** hackathon{'s' if len(hackathons) != 1 else ''}")

# ── card helpers ──────────────────────────────────────────────────────────────
def _fmt_date(d: str | None) -> str:
    if not d:
        return ""
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%b %d, %Y")
    except ValueError:
        return d


def _badge(text: str, fg: str, bg: str) -> str:
    return (
        f'<span class="badge" style="color:{fg};background:{bg}">'
        f"{text}</span>"
    )


def render_card(h: dict):
    src_color = SOURCE_COLORS.get(h["source"], "#333")
    fg, bg    = STATUS_COLORS.get(h["status"], ("#333", "#eee"))

    with st.container(border=True):
        # badges + title row
        badges = (
            _badge(h["source"].upper(), "white", src_color)
            + " "
            + _badge(h["status"].upper(), fg, bg)
        )
        st.markdown(badges, unsafe_allow_html=True)
        st.markdown(f"**[{h['title'][:80]}{'…' if len(h['title']) > 80 else ''}]({h['url']})**")

        # metadata row
        meta: list[str] = []
        start = _fmt_date(h.get("start_date"))
        end   = _fmt_date(h.get("end_date"))
        if start:
            meta.append(f"📅 {start}" + (f" → {end}" if end and end != start else ""))
        if h.get("prize"):
            meta.append(f"💰 {h['prize']}")
        if meta:
            st.caption("  ·  ".join(meta))

        if h.get("description"):
            desc = h["description"]
            st.caption(desc[:160] + "…" if len(desc) > 160 else desc)

        st.link_button("Register →", h["url"], use_container_width=True)


# ── grid (3 columns) ─────────────────────────────────────────────────────────
COLS = 3
for row_start in range(0, len(hackathons), COLS):
    cols = st.columns(COLS)
    for col, h in zip(cols, hackathons[row_start : row_start + COLS]):
        with col:
            render_card(h)
