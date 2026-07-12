from bs4 import BeautifulSoup

from scrapers.devpost import DevpostScraper
from scrapers.mlh import MLHScraper
from scrapers.unstop import UnstopScraper

DEVPOST_ITEM = {
    "title": "  Space Apps Challenge  ",
    "url": "https://spaceapps.devpost.com",
    "displayed_location": {"icon": "globe", "location": "Online"},
    "submission_period_dates": "Jul 15 - Aug 20, 2026",
    "prize_amount": "<span data-currency=\"USD\">$</span><span>10,000</span>",
    "themes": [{"name": "Space"}, {"name": "Open Data"}],
    "thumbnail_url": "https://img.devpost.com/thumb.png",
}


def test_devpost_parse():
    h = DevpostScraper()._parse(DEVPOST_ITEM)
    assert h["title"] == "Space Apps Challenge"
    assert h["start_date"] == "2026-07-15"
    assert h["end_date"] == "2026-08-20"
    assert h["prize"] == "$10,000"
    assert h["description"] == "Space, Open Data"


def test_devpost_skips_in_person():
    item = {**DEVPOST_ITEM, "displayed_location": {"icon": "map-marker-alt"}}
    assert DevpostScraper()._parse(item) is None


def test_devpost_skips_missing_title():
    assert DevpostScraper()._parse({"title": "", "url": "https://x.test"}) is None


def test_unstop_prize_cash_total():
    prizes = [
        {"rank": "First", "cash": 50000, "currency": "fa-rupee"},
        {"rank": "Second", "cash": 25000, "currency": "fa-rupee"},
    ]
    assert UnstopScraper._extract_prize(prizes) == "₹75,000"


def test_unstop_prize_non_cash():
    prizes = [
        {"rank": "First", "cash": None, "others": "Free 1-Year Domain"},
        {"rank": "Second", "cash": None, "others": "Free 1-Year Domain"},
        {"rank": "Third", "cash": None, "others": "ChatGPT Credits"},
    ]
    assert UnstopScraper._extract_prize(prizes) == "Free 1-Year Domain; ChatGPT Credits"


def test_unstop_prize_empty():
    assert UnstopScraper._extract_prize([]) is None
    assert UnstopScraper._extract_prize(None) is None


def test_unstop_parse_unescapes_entities():
    item = {
        "title": "FinTech Hack",
        "region": "online",
        "seo_url": "https://unstop.com/hackathons/fintech",
        "regnRequirements": {"start_regn_dt": "2026-08-01T00:00:00", "end_regn_dt": "2026-08-10T00:00:00"},
        "end_date": "2026-08-15T00:00:00",
        "details": "<p>Dates: &nbsp;11th &amp; 12th July</p>",
        "prizes": [],
    }
    h = UnstopScraper()._parse(item)
    assert h["description"] == "Dates: 11th & 12th July"


MLH_HTML = """
<a itemtype="https://schema.org/Event" href="https://hack.example.edu">
  <meta itemprop="eventAttendanceMode" content="https://schema.org/OnlineEventAttendanceMode" />
  <meta itemprop="startDate" content="2026-09-05T00:00:00" />
  <meta itemprop="endDate" content="2026-09-07T00:00:00" />
  <meta itemprop="image" content="https://mlh.io/img.png" />
  <h3 class="event-name">Example Hacks</h3>
</a>
"""


def test_mlh_parse():
    ev = BeautifulSoup(MLH_HTML, "lxml").select_one("a")
    h = MLHScraper()._parse(ev)
    assert h["title"] == "Example Hacks"
    assert h["start_date"] == "2026-09-05"
    assert h["end_date"] == "2026-09-07"
    assert h["image_url"] == "https://mlh.io/img.png"


def test_mlh_skips_in_person():
    html = MLH_HTML.replace("OnlineEventAttendanceMode", "OfflineEventAttendanceMode")
    ev = BeautifulSoup(html, "lxml").select_one("a")
    assert MLHScraper()._parse(ev) is None
