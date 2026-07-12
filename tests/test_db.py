from datetime import date, datetime, timedelta

from tests.conftest import make_row


def test_upsert_inserts_and_updates(test_db):
    test_db.upsert_hackathon(make_row())
    test_db.upsert_hackathon(make_row(title="Renamed", prize="$9,000"))
    rows = test_db.get_hackathons(statuses=["upcoming"])
    assert len(rows) == 1
    assert rows[0]["title"] == "Renamed"
    assert rows[0]["prize"] == "$9,000"


def test_filters(test_db):
    test_db.upsert_hackathon(make_row(url="https://a.test", source="devpost", prize="$1"))
    test_db.upsert_hackathon(make_row(url="https://b.test", source="mlh", prize=None, title="MLH Winter"))

    assert len(test_db.get_hackathons(sources=["devpost"])) == 1
    assert len(test_db.get_hackathons(has_prize=True)) == 1
    assert len(test_db.get_hackathons(search="winter")) == 1
    assert len(test_db.get_hackathons(search="nomatch")) == 0


def test_pagination(test_db):
    for i in range(5):
        test_db.upsert_hackathon(make_row(url=f"https://p{i}.test", title=f"Event number {i}"))
    assert len(test_db.get_hackathons(limit=2, dedupe=False)) == 2
    assert len(test_db.get_hackathons(limit=10, offset=4, dedupe=False)) == 1


def test_update_statuses(test_db):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    week_ago = (date.today() - timedelta(days=7)).isoformat()

    test_db.upsert_hackathon(make_row(url="https://past.test", title="Old", start_date=week_ago, end_date=yesterday))
    test_db.upsert_hackathon(make_row(url="https://live.test", title="Live", start_date=yesterday, end_date=tomorrow))
    test_db.update_statuses()

    rows = {r["url"]: r["status"] for r in test_db.get_hackathons(statuses=["past", "ongoing", "upcoming"])}
    assert rows["https://past.test"] == "past"
    assert rows["https://live.test"] == "ongoing"


def test_prune_stale(test_db):
    long_past = (date.today() - timedelta(days=120)).isoformat()
    stale_scrape = (datetime.now() - timedelta(days=30)).isoformat()

    test_db.upsert_hackathon(make_row(
        url="https://ancient.test", title="Ancient", status="past",
        start_date=long_past, end_date=long_past,
    ))
    test_db.upsert_hackathon(make_row(
        url="https://ghost.test", title="Ghost", scraped_at=stale_scrape,
    ))
    test_db.upsert_hackathon(make_row(url="https://fresh.test", title="Fresh"))
    test_db.prune_stale()

    rows = test_db.get_hackathons(statuses=["past", "ongoing", "upcoming"], dedupe=False)
    urls = {r["url"] for r in rows}
    assert urls == {"https://fresh.test"}


def test_dedupe_collapses_cross_source_duplicates(test_db):
    test_db.upsert_hackathon(make_row(
        url="https://devpost.test", source="devpost", title="AI Global Hack 2026",
        prize=None, description=None, image_url=None,
    ))
    test_db.upsert_hackathon(make_row(
        url="https://unstop.test", source="unstop", title="AI  Global  Hack  2026!",
        start_date="2026-08-02", prize="₹50,000",
    ))
    rows = test_db.get_hackathons()
    assert len(rows) == 1
    # unstop row wins: it has more fields filled
    assert rows[0]["source"] == "unstop"


def test_dedupe_keeps_distinct_events_with_same_name(test_db):
    test_db.upsert_hackathon(make_row(url="https://spring.test", title="CodeFest", start_date="2026-08-01"))
    test_db.upsert_hackathon(make_row(url="https://fall.test", title="CodeFest", start_date="2026-11-01", source="mlh"))
    rows = test_db.get_hackathons()
    assert len(rows) == 2
