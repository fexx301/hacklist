import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from apscheduler.schedulers.background import BackgroundScheduler

from db import log_scrape, prune_stale, update_statuses, upsert_hackathon
from scrapers import get_all_scrapers

log = logging.getLogger(__name__)

# Guards against overlapping runs (manual refresh vs. the daily job).
# Held for the duration of a scrape; SQLite writes happen only in the
# coordinating thread, so worker threads never touch the database.
_scrape_lock = threading.Lock()


def is_scraping() -> bool:
    return _scrape_lock.locked()


def run_all_scrapers() -> bool:
    """Scrape all sources concurrently. Returns False if a run was already in progress."""
    if not _scrape_lock.acquire(blocking=False):
        log.info("Scrape already running; skipping")
        return False
    try:
        update_statuses()
        scrapers = get_all_scrapers()
        with ThreadPoolExecutor(max_workers=len(scrapers)) as pool:
            futures = {pool.submit(s.scrape): s for s in scrapers}
            for future in as_completed(futures):
                scraper = futures[future]
                try:
                    items = future.result()
                    for h in items:
                        upsert_hackathon(h)
                    log_scrape(scraper.name, "success", len(items))
                    log.info("%s: scraped %d hackathons", scraper.name, len(items))
                except Exception as exc:
                    log_scrape(scraper.name, "error", 0, str(exc))
                    log.error("%s failed: %s", scraper.name, exc)
        update_statuses()
        prune_stale()
    finally:
        _scrape_lock.release()
    return True


_scheduler: BackgroundScheduler | None = None


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(run_all_scrapers, "interval", hours=24, id="daily_scrape")
    _scheduler.start()
    log.info("Scheduler started — daily scrape every 24 h")
