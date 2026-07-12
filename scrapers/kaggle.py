import logging
import os
from datetime import date

from .base import BaseScraper

log = logging.getLogger(__name__)

_API = "https://www.kaggle.com/api/v1/competitions/list"

# Rewards that aren't really prizes
_NON_PRIZES = {"knowledge", "kudos", ""}


class KaggleScraper(BaseScraper):
    """Kaggle competitions via the official API.

    Requires KAGGLE_USERNAME and KAGGLE_KEY (free: kaggle.com → Settings → API
    → Create New Token). Without them the scraper is skipped entirely.
    """

    name = "kaggle"

    def scrape(self) -> list[dict]:
        username = os.getenv("KAGGLE_USERNAME", "")
        key      = os.getenv("KAGGLE_KEY", "")
        if not username or not key:
            return []

        hackathons = []
        for page in (1, 2):
            resp = self.session.get(
                _API,
                params={"page": page, "sortBy": "latestDeadline"},
                auth=(username, key),
                timeout=15,
            )
            resp.raise_for_status()
            items = resp.json()
            if not items:
                break
            for item in items:
                h = self._parse(item)
                if h:
                    hackathons.append(h)
        return hackathons

    def _parse(self, item: dict) -> dict | None:
        title = (item.get("title") or "").strip()
        url   = item.get("ref") or ""
        if url and not url.startswith("http"):
            url = f"https://www.kaggle.com/competitions/{url}"
        if not title or not url:
            return None

        start = self.parse_date((item.get("enabledDate") or "")[:10])
        end   = self.parse_date((item.get("deadline") or "")[:10])

        # Competitions run for months; only keep ones still accepting entries
        if end and end < date.today().isoformat():
            return None

        reward = (item.get("reward") or "").strip()
        prize  = reward if reward.lower() not in _NON_PRIZES else None

        desc = (item.get("description") or "").strip()[:300] or None

        return self.make_hackathon(
            title=title, url=url,
            start_date=start, end_date=end,
            prize=prize, description=desc,
        )
