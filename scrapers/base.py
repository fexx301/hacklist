import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import dateparser
import requests


class BaseScraper(ABC):
    name: str = ""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })

    @abstractmethod
    def scrape(self) -> list[dict]:
        pass

    def parse_date(self, text: str) -> str | None:
        if not text:
            return None
        parsed = dateparser.parse(text.strip(), settings={"RETURN_AS_TIMEZONE_AWARE": False, "PREFER_DAY_OF_MONTH": "first"})
        return parsed.strftime("%Y-%m-%d") if parsed else None

    def parse_date_range(self, text: str) -> tuple[str | None, str | None]:
        if not text:
            return None, None
        parts = re.split(r"\s*[-–]\s*", text.strip(), maxsplit=1)
        if len(parts) == 2:
            return self.parse_date(parts[0]), self.parse_date(parts[1])
        return self.parse_date(parts[0]), None

    def determine_status(self, start_date: str | None, end_date: str | None) -> str:
        today = datetime.now(timezone.utc).date()
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
            end   = datetime.strptime(end_date,   "%Y-%m-%d").date() if end_date   else start
            if not start:
                return "upcoming"
            if end and end < today:
                return "past"
            if start <= today:
                return "ongoing"
        except (ValueError, TypeError):
            pass
        return "upcoming"

    def make_hackathon(
        self,
        title: str,
        url: str,
        start_date: str | None = None,
        end_date: str | None = None,
        prize: str | None = None,
        description: str | None = None,
        image_url: str | None = None,
    ) -> dict:
        return {
            "title":       title,
            "url":         url,
            "source":      self.name,
            "start_date":  start_date,
            "end_date":    end_date,
            "prize":       prize,
            "description": description,
            "image_url":   image_url,
            "status":      self.determine_status(start_date, end_date),
            "scraped_at":  datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds"),
        }
