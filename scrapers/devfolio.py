import time

from .base import BaseScraper

_API = "https://api.devfolio.co/api/hackathons/"


class DevfolioScraper(BaseScraper):
    name = "devfolio"

    def scrape(self) -> list[dict]:
        hackathons = []

        for page in range(1, 6):
            try:
                resp = self.session.get(
                    _API,
                    params={"page": page, "limit": 20, "offset": (page - 1) * 20},
                    headers={**self.session.headers, "Accept": "application/json"},
                    timeout=15,
                )
                resp.raise_for_status()
                data    = resp.json()
                items   = data.get("result", [])
                total_p = data.get("pages", 1)
                if not items:
                    break

                for item in items:
                    h = self._parse(item)
                    if h:
                        hackathons.append(h)

                if page >= total_p:
                    break

            except Exception:
                break

            time.sleep(1)

        return hackathons

    def _parse(self, item: dict) -> dict | None:
        if not item.get("is_online", False):
            return None

        title = (item.get("name") or "").strip()
        slug  = item.get("slug", "")
        url   = f"https://devfolio.co/{slug}" if slug else ""
        if not title or not url:
            return None

        start = self.parse_date((item.get("starts_at") or "")[:10])
        end   = self.parse_date((item.get("ends_at")   or "")[:10])

        # Sum prize amounts from prizes list
        prizes = item.get("prizes") or []
        if prizes:
            prize = f"{len(prizes)} prize{'s' if len(prizes)!=1 else ''}"
        else:
            prize = None

        desc = (item.get("tagline") or "").strip() or None
        img  = item.get("cover_img") or (item.get("hackathon_setting") or {}).get("logo")

        return self.make_hackathon(
            title=title, url=url,
            start_date=start, end_date=end,
            prize=prize, description=desc, image_url=img,
        )
