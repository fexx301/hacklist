import re
import time

import requests

from .base import BaseScraper

_API = "https://devpost.com/api/hackathons"


class DevpostScraper(BaseScraper):
    name = "devpost"

    def scrape(self) -> list[dict]:
        hackathons = []
        session = requests.Session()
        session.headers.update({
            **self.session.headers,
            "Accept":   "application/json",
            "Referer":  "https://devpost.com/hackathons",
        })

        for page in range(1, 6):
            try:
                resp = session.get(
                    _API,
                    params={
                        "page":             page,
                        "status[]":         ["upcoming", "open"],
                        "challenge_type[]": "hackathons",
                        "order_by":         "recently-added",
                    },
                    timeout=15,
                )
                resp.raise_for_status()
                data  = resp.json()
                items = data.get("hackathons", [])
                if not items:
                    break

                for item in items:
                    h = self._parse(item)
                    if h:
                        hackathons.append(h)

                if page >= data.get("meta", {}).get("total_pages", 1):
                    break

            except Exception:
                break

            time.sleep(1)

        return hackathons

    def _parse(self, item: dict) -> dict | None:
        title = item.get("title", "").strip()
        url   = item.get("url", "")
        if not title or not url:
            return None

        # Devpost returns only online hackathons when no location filter is set,
        # but double-check via displayed_location icon
        loc = item.get("displayed_location") or {}
        if isinstance(loc, dict) and loc.get("icon") not in (None, "globe", ""):
            return None  # skip in-person

        dates_raw = item.get("submission_period_dates", "")
        start, end = self.parse_date_range(dates_raw)

        # prize_amount may contain HTML spans — strip them
        prize_raw = item.get("prize_amount", "") or ""
        prize = re.sub(r"<[^>]+>", "", prize_raw).strip() or None

        themes = ", ".join(t["name"] for t in (item.get("themes") or []))
        desc   = themes or None

        img = item.get("thumbnail_url")

        return self.make_hackathon(
            title=title, url=url,
            start_date=start, end_date=end,
            prize=prize, description=desc, image_url=img,
        )
