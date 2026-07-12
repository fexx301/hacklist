import re
import time

from .base import BaseScraper

_API = "https://unstop.com/api/public/opportunity/search-result"


class UnstopScraper(BaseScraper):
    name = "unstop"

    def scrape(self) -> list[dict]:
        hackathons = []
        session_headers = {
            **self.session.headers,
            "Accept":  "application/json",
            "Referer": "https://unstop.com/hackathons",
        }

        for page in range(1, 5):
            try:
                resp = self.session.get(
                    _API,
                    params={
                        "opportunity": "hackathons",
                        "per_page":    18,
                        "oppstatus":   "open",
                        "undefined":   "true",
                        "page":        page,
                    },
                    headers=session_headers,
                    timeout=15,
                )
                resp.raise_for_status()
                data  = resp.json()
                items = data.get("data", {}).get("data", [])
                if not items:
                    break

                for item in items:
                    h = self._parse(item)
                    if h:
                        hackathons.append(h)

                last_page = data.get("data", {}).get("last_page", 1)
                if page >= last_page:
                    break

            except Exception:
                break

            time.sleep(1)

        return hackathons

    def _parse(self, item: dict) -> dict | None:
        title = (item.get("title") or "").strip()
        if not title:
            return None

        # Only online
        if (item.get("region") or "").lower() not in ("online", "virtual", ""):
            return None

        url = item.get("seo_url") or item.get("short_url") or ""
        if not url:
            slug = item.get("public_url", "")
            url  = f"https://unstop.com/{slug}" if slug else ""
        if not url:
            return None

        regn = item.get("regnRequirements") or {}
        start = self.parse_date((regn.get("start_regn_dt") or "")[:10])
        end   = self.parse_date((item.get("end_date") or regn.get("end_regn_dt") or "")[:10])

        # Strip HTML from description
        details_html = item.get("details") or ""
        desc = re.sub(r"<[^>]+>", " ", details_html).strip()[:300] or None

        img = item.get("logoUrl2") or (item.get("opportunity_config") or {}).get("banner_config")
        if isinstance(img, str) and img.startswith("{"):
            img = None  # banner_config is JSON, not a URL

        return self.make_hackathon(
            title=title, url=url,
            start_date=start, end_date=end,
            description=desc, image_url=img,
        )
