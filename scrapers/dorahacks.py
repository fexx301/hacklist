import logging
import re
import time
from datetime import datetime, timezone

from .base import BaseScraper

log = logging.getLogger(__name__)

_API = "https://dorahacks.io/api/hackathon/"


class DoraHacksScraper(BaseScraper):
    name = "dorahacks"

    def scrape(self) -> list[dict]:
        hackathons = []
        headers = {
            **self.session.headers,
            "Accept":  "application/json",
            "Referer": "https://dorahacks.io/hackathon",
        }

        for status in ("upcoming", "ongoing"):
            for page in range(1, 4):
                try:
                    resp = self.session.get(
                        _API,
                        params={"page": page, "page_size": 20, "status": status},
                        headers=headers,
                        timeout=15,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as exc:
                    log.warning("dorahacks: %s page %d failed, stopping early: %s", status, page, exc)
                    break

                items = data.get("results", [])
                if not items:
                    break

                for item in items:
                    h = self._parse(item)
                    if h:
                        hackathons.append(h)

                if not data.get("next"):
                    break
                # The API rate-limits bursts with a human-verification page
                time.sleep(2)
            time.sleep(2)

        return hackathons

    def _parse(self, item: dict) -> dict | None:
        title = (item.get("title") or "").strip()
        uname = item.get("uname")
        if not title or not uname:
            return None  # no uname means no public page to link to

        # Online events have no venue; a venue (even "To be announced") means in-person
        if item.get("venue_name") or item.get("venue_address"):
            return None

        bonus = item.get("bonus_price")
        prize = f"${int(bonus):,}" if isinstance(bonus, (int, float)) and bonus > 0 else None

        # Description is markdown — strip syntax down to plain text
        desc = re.sub(r"[#*_>`]|\!?\[([^\]]*)\]\([^)]*\)", r"\1", item.get("description") or "")
        desc = re.sub(r"\s+", " ", desc).strip()[:300] or None

        return self.make_hackathon(
            title=title,
            url=f"https://dorahacks.io/hackathon/{uname}",
            start_date=self._ts_to_date(item.get("start_time")),
            end_date=self._ts_to_date(item.get("end_time")),
            prize=prize,
            description=desc,
            image_url=item.get("image_url"),
        )

    @staticmethod
    def _ts_to_date(ts) -> str | None:
        if not ts:
            return None
        try:
            return datetime.fromtimestamp(int(ts), tz=timezone.utc).date().isoformat()
        except (ValueError, TypeError, OSError):
            return None
