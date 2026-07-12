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


from datetime import date, timedelta

from scrapers.dorahacks import DoraHacksScraper
from scrapers.kaggle import KaggleScraper

DORAHACKS_ITEM = {
    "title": "WEEX AI Wars II: Rise of Intelligence",
    "uname": "weex-ai-wars2",
    "start_time": 1794002400,   # 2026-11-06 UTC
    "end_time": 1794193200,     # 2026-11-09 UTC (Nov 8 19:00 EST)
    "bonus_price": 200000,
    "venue_name": None,
    "venue_address": None,
    "description": "# Welcome!\n\n**Build** AI agents. [Register](https://x.test) now.",
    "image_url": "https://cdn.dorahacks.io/img.png",
}


def test_dorahacks_parse():
    h = DoraHacksScraper()._parse(DORAHACKS_ITEM)
    assert h["title"] == "WEEX AI Wars II: Rise of Intelligence"
    assert h["url"] == "https://dorahacks.io/hackathon/weex-ai-wars2"
    assert h["start_date"] == "2026-11-06"
    assert h["end_date"] == "2026-11-09"
    assert h["prize"] == "$200,000"
    assert "Welcome! Build AI agents. Register now." in h["description"]


def test_dorahacks_skips_in_person():
    item = {**DORAHACKS_ITEM, "venue_name": "To be announced"}
    assert DoraHacksScraper()._parse(item) is None


def test_dorahacks_skips_missing_uname():
    item = {**DORAHACKS_ITEM, "uname": None}
    assert DoraHacksScraper()._parse(item) is None


def _kaggle_item(**overrides):
    item = {
        "title": "ARC Prize 2026",
        "ref": "https://www.kaggle.com/competitions/arc-prize-2026",
        "enabledDate": "2026-03-25T00:00:00Z",
        "deadline": (date.today() + timedelta(days=60)).isoformat() + "T23:59:00Z",
        "reward": "$1,000,000",
        "description": "Create an AI capable of novel reasoning.",
    }
    item.update(overrides)
    return item


def test_kaggle_parse():
    h = KaggleScraper()._parse(_kaggle_item())
    assert h["title"] == "ARC Prize 2026"
    assert h["url"] == "https://www.kaggle.com/competitions/arc-prize-2026"
    assert h["start_date"] == "2026-03-25"
    assert h["prize"] == "$1,000,000"


def test_kaggle_slug_ref_builds_url():
    h = KaggleScraper()._parse(_kaggle_item(ref="arc-prize-2026"))
    assert h["url"] == "https://www.kaggle.com/competitions/arc-prize-2026"


def test_kaggle_knowledge_reward_is_not_prize():
    h = KaggleScraper()._parse(_kaggle_item(reward="Knowledge"))
    assert h["prize"] is None


def test_kaggle_skips_closed_competitions():
    old = _kaggle_item(deadline="2025-01-01T00:00:00Z")
    assert KaggleScraper()._parse(old) is None


def test_kaggle_scrape_skipped_without_creds(monkeypatch):
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    assert KaggleScraper().scrape() == []
