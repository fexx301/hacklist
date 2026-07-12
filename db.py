import sqlite3
from contextlib import contextmanager
from datetime import date, datetime

DB_PATH = "hackathons.db"


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
            (source, status, count, error_msg, datetime.utcnow().isoformat()),
        )


def update_statuses():
    today = date.today().isoformat()
    with _conn() as c:
        c.execute("UPDATE hackathons SET status='past'    WHERE end_date < ? AND status != 'past'", (today,))
        c.execute(
            "UPDATE hackathons SET status='ongoing' WHERE start_date <= ? AND (end_date >= ? OR end_date IS NULL) AND status = 'upcoming'",
            (today, today),
        )


def get_hackathons(sources=None, statuses=None, search=None, has_prize=False):
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
    """

    with _conn() as c:
        rows = c.execute(query, params).fetchall()
    return [dict(r) for r in rows]


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
