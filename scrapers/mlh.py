from datetime import datetime

from bs4 import BeautifulSoup

from .base import BaseScraper


class MLHScraper(BaseScraper):
    name = "mlh"

    def scrape(self) -> list[dict]:
        hackathons = []
        year = datetime.now().year
        for y in [year, year + 1]:
            try:
                resp = self.session.get(f"https://mlh.io/seasons/{y}/events", timeout=15)
                if resp.status_code != 200:
                    continue
            except Exception:
                continue

            soup   = BeautifulSoup(resp.text, "lxml")
            # Each event is an <a> with itemscope/itemtype="https://schema.org/Event"
            events = soup.select('a[itemtype="https://schema.org/Event"]')
            for ev in events:
                try:
                    h = self._parse(ev)
                    if h:
                        hackathons.append(h)
                except Exception:
                    continue

        return hackathons

    def _parse(self, ev) -> dict | None:
        # Filter online-only via schema.org meta
        mode_el = ev.find("meta", itemprop="eventAttendanceMode")
        mode    = (mode_el.get("content") or "") if mode_el else ""
        if mode and "Online" not in mode and "Mixed" not in mode:
            return None

        url = ev.get("href", "")
        if not url:
            return None

        # Title: first meaningful text heading in the card
        title_el = ev.select_one("h3, h4, [class*='event-name'], [class*='name']")
        title    = title_el.get_text(strip=True) if title_el else ""
        if not title:
            # fallback: first non-empty text node
            for el in ev.find_all(["h2","h3","h4","h5","p","span"]):
                t = el.get_text(strip=True)
                if t and len(t) > 3:
                    title = t
                    break
        if not title:
            return None

        # Dates from schema.org meta
        start_el = ev.find("meta", itemprop="startDate")
        end_el   = ev.find("meta", itemprop="endDate")
        start = self.parse_date((start_el.get("content") or "")[:10]) if start_el else None
        end   = self.parse_date((end_el.get("content")   or "")[:10]) if end_el   else None

        img_el = ev.find("meta", itemprop="image")
        img    = img_el.get("content") if img_el else None

        return self.make_hackathon(title=title, url=url, start_date=start, end_date=end, image_url=img)
