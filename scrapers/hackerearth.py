import re
import time

from bs4 import BeautifulSoup

from .base import BaseScraper

_BASE = "https://www.hackerearth.com"


class HackerEarthScraper(BaseScraper):
    name = "hackerearth"

    def scrape(self) -> list[dict]:
        hackathons = []
        seen: set[str] = set()

        for path in ("/challenges/hackathon/", "/challenges/hackathon/upcoming/"):
            url = _BASE + path
            try:
                resp = self.session.get(url, timeout=15)
                resp.raise_for_status()
            except Exception:
                continue

            soup = BeautifulSoup(resp.text, "lxml")

            for card in soup.select(".challenge-card"):
                try:
                    h = self._parse_card(card)
                    if h and h["url"] not in seen:
                        seen.add(h["url"])
                        hackathons.append(h)
                except Exception:
                    continue

            time.sleep(1)

        return hackathons

    def _parse_card(self, card) -> dict | None:
        link_el = card.select_one("a.challenge-card-link, a.challenge-card-wrapper")
        if not link_el:
            return None
        url = link_el.get("href", "")
        if not url.startswith("http"):
            url = _BASE + url

        # Title: prefer the `title` attribute on .challenge-name (avoids truncation)
        name_el = card.select_one(".challenge-name")
        title   = (name_el.get("title") or "").strip() if name_el else ""
        if not title:
            span = card.select_one(".challenge-list-title")
            title = span.get_text(strip=True) if span else ""
        if not title:
            return None

        # Date: "Jun  8, 2026 UTC (UTC)" — strip timezone suffix
        date_el   = card.select_one(".date")
        date_text = re.sub(r"\s*UTC.*$", "", date_el.get_text(strip=True)) if date_el else ""
        # Remove font-awesome icon text if any
        date_text = re.sub(r"^[^\w]+", "", date_text).strip()
        start     = self.parse_date(date_text) if date_text else None

        # Image from background-image style
        img_el  = card.select_one(".event-image")
        img     = None
        if img_el:
            style = img_el.get("style", "")
            m = re.search(r"url\(['\"]?([^'\")]+)['\"]?\)", style)
            img = m.group(1) if m else None

        # Prize: check if "Prizes" type is mentioned
        prize_el = card.select_one(".type")
        prize = prize_el.get_text(strip=True).replace("Prizes", "").strip() or "Prizes" if prize_el else None

        return self.make_hackathon(title=title, url=url, start_date=start, image_url=img, prize=prize)
