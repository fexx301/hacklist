import logging

from apscheduler.schedulers.background import BackgroundScheduler

from db import log_scrape, update_statuses, upsert_hackathon
from scrapers import get_all_scrapers

log = logging.getLogger(__name__)


def run_all_scrapers():
    update_statuses()
    for scraper in get_all_scrapers():
        try:
            items = scraper.scrape()
            for h in items:
                upsert_hackathon(h)
            log_scrape(scraper.name, "success", len(items))
            log.info("%s: scraped %d hackathons", scraper.name, len(items))
        except Exception as exc:
            log_scrape(scraper.name, "error", 0, str(exc))
            log.error("%s failed: %s", scraper.name, exc)


_scheduler: BackgroundScheduler | None = None


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(run_all_scrapers, "interval", hours=24, id="daily_scrape")
    _scheduler.start()
    log.info("Scheduler started — daily scrape every 24 h")
