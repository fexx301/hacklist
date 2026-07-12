from datetime import date, timedelta

from scrapers.base import BaseScraper


class DummyScraper(BaseScraper):
    name = "dummy"

    def scrape(self):
        return []


def scraper():
    return DummyScraper()


def test_parse_date_plain():
    assert scraper().parse_date("Jul 15, 2026") == "2026-07-15"


def test_parse_date_empty():
    assert scraper().parse_date("") is None
    assert scraper().parse_date(None) is None


def test_parse_date_range_hyphen():
    start, end = scraper().parse_date_range("Jul 15 - Jul 20, 2026")
    assert start == "2026-07-15"
    assert end == "2026-07-20"


def test_parse_date_range_single():
    start, end = scraper().parse_date_range("Jul 15, 2026")
    assert start == "2026-07-15"
    assert end is None


def test_determine_status_past():
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    assert scraper().determine_status(week_ago, yesterday) == "past"


def test_determine_status_ongoing():
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    assert scraper().determine_status(yesterday, tomorrow) == "ongoing"


def test_determine_status_upcoming():
    next_week = (date.today() + timedelta(days=7)).isoformat()
    assert scraper().determine_status(next_week, None) == "upcoming"
    assert scraper().determine_status(None, None) == "upcoming"


def test_make_hackathon_shape():
    h = scraper().make_hackathon(title="T", url="https://x.test")
    assert h["source"] == "dummy"
    assert h["status"] == "upcoming"
    assert h["scraped_at"]
