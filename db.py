import re
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone

DB_PATH = "hackathons.db"

# Prefer richer sources when collapsing cross-source duplicates
_SOURCE_PRIORITY = ["devpost", "devfolio", "mlh", "hackerearth", "dorahacks", "kaggle", "unstop", "twitter"]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with _conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS hackathons (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                url         TEXT    UNIQUE NOT NULL,
                source      TEXT    NOT NULL,
                start_date  TEXT,
                end_date    TEXT,
                prize       TEXT,
                description TEXT,
                image_url   TEXT,
                status      TEXT    DEFAULT 'upcoming',
                scraped_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS scrape_logs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                source      TEXT    NOT NULL,
                status      TEXT    NOT NULL,
                count       INTEGER DEFAULT 0,
                error_msg   TEXT,
                scraped_at  TEXT    NOT NULL
            );
        """)


def upsert_hackathon(h: dict):
    with _conn() as c:
        c.execute("""
            INSERT INTO hackathons
                (title, url, source, start_date, end_date, prize, description, image_url, status, scraped_at)
            VALUES
                (:title, :url, :source, :start_date, :end_date, :prize, :description, :image_url, :status, :scraped_at)
            ON CONFLICT(url) DO UPDATE SET
                title       = excluded.title,
                start_date  = excluded.start_date,
                end_date    = excluded.end_date,
                prize       = excluded.prize,
                description = excluded.description,
                image_url   = excluded.image_url,
                status      = excluded.status,
                scraped_at  = excluded.scraped_at
        """, h)


def log_scrape(source: str, status: str, count: int = 0, error_msg: str = None):
    with _conn() as c:
        c.execute(
            "INSERT INTO scrape_logs (source, status, count, error_msg, scraped_at) VALUES (?,?,?,?,?)",
            (source, status, count, error_msg, now_iso()),
        )


def update_statuses():
    today = date.today().isoformat()
    with _conn() as c:
        c.execute("UPDATE hackathons SET status='past'    WHERE end_date < ? AND status != 'past'", (today,))
        c.execute(
            "UPDATE hackathons SET status='ongoing' WHERE start_date <= ? AND (end_date >= ? OR end_date IS NULL) AND status = 'upcoming'",
            (today, today),
        )


def prune_stale():
    """Remove rows that no longer earn their place:
    - past events older than 90 days
    - upcoming/ongoing events not re-seen by any scrape in 14 days (delisted at the source)
    """
    past_cutoff = (date.today() - timedelta(days=90)).isoformat()
    seen_cutoff = (datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=14)).isoformat()
    with _conn() as c:
        c.execute("DELETE FROM hackathons WHERE status = 'past' AND end_date < ?", (past_cutoff,))
        c.execute("DELETE FROM hackathons WHERE status != 'past' AND scraped_at < ?", (seen_cutoff,))


def _norm_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def _richness(row: dict) -> tuple:
    filled = sum(1 for k in ("start_date", "end_date", "prize", "description", "image_url") if row.get(k))
    src = _SOURCE_PRIORITY.index(row["source"]) if row["source"] in _SOURCE_PRIORITY else len(_SOURCE_PRIORITY)
    return (-filled, src)


def _same_event(a: dict, b: dict) -> bool:
    sa, sb = a.get("start_date"), b.get("start_date")
    if not sa or not sb:
        return True  # same title, one side has no date — assume same event
    try:
        da = datetime.strptime(sa, "%Y-%m-%d")
        db_ = datetime.strptime(sb, "%Y-%m-%d")
    except ValueError:
        return sa == sb
    return abs((da - db_).days) <= 7


def dedupe_rows(rows: list[dict]) -> list[dict]:
    """Collapse the same event listed on multiple platforms: identical normalized
    titles with start dates within a week are one event; keep the richest row."""
    clusters: dict[str, list[list[dict]]] = {}
    for row in rows:
        key = _norm_title(row["title"])
        for cluster in clusters.setdefault(key, []):
            if _same_event(cluster[0], row):
                cluster.append(row)
                break
        else:
            clusters[key].append([row])

    keep_ids = set()
    for groups in clusters.values():
        for cluster in groups:
            keep_ids.add(min(cluster, key=_richness)["id"])

    return [r for r in rows if r["id"] in keep_ids]


def get_hackathons(sources=None, statuses=None, search=None, has_prize=False,
                   limit=500, offset=0, dedupe=True):
    query = "SELECT * FROM hackathons WHERE 1=1"
    params: list = []

    if sources:
        query += f" AND source IN ({','.join('?'*len(sources))})"
        params.extend(sources)
    if statuses:
        query += f" AND status IN ({','.join('?'*len(statuses))})"
        params.extend(statuses)
    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    if has_prize:
        query += " AND prize IS NOT NULL AND prize != ''"

    query += """
        ORDER BY
            CASE status WHEN 'ongoing' THEN 0 WHEN 'upcoming' THEN 1 ELSE 2 END,
            start_date ASC
        LIMIT ? OFFSET ?
    """
    params += [limit, offset]

    with _conn() as c:
        rows = c.execute(query, params).fetchall()
    result = [dict(r) for r in rows]
    return dedupe_rows(result) if dedupe else result


def get_hackathon(hackathon_id: int) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM hackathons WHERE id = ?", (hackathon_id,)).fetchone()
    return dict(row) if row else None


def get_stats():
    with _conn() as c:
        total     = c.execute("SELECT COUNT(*) FROM hackathons").fetchone()[0]
        by_source = dict(c.execute("SELECT source, COUNT(*) FROM hackathons GROUP BY source").fetchall())
        by_status = dict(c.execute("SELECT status, COUNT(*) FROM hackathons GROUP BY status").fetchall())
    return {"total": total, "by_source": by_source, "by_status": by_status}


def get_last_scrape_times():
    with _conn() as c:
        rows = c.execute("""
            SELECT l.source, l.status, l.scraped_at
            FROM scrape_logs l
            INNER JOIN (
                SELECT source, MAX(scraped_at) AS max_ts FROM scrape_logs GROUP BY source
            ) m ON l.source = m.source AND l.scraped_at = m.max_ts
        """).fetchall()
    return {r["source"]: {"status": r["status"], "last_scraped": r["scraped_at"]} for r in rows}
