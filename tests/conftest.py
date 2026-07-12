import pytest

import db


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    return db


def make_row(**overrides):
    row = {
        "title": "Test Hackathon",
        "url": "https://example.com/hack",
        "source": "devpost",
        "start_date": "2026-08-01",
        "end_date": "2026-08-03",
        "prize": "$5,000",
        "description": "A test event",
        "image_url": "https://example.com/img.png",
        "status": "upcoming",
        "scraped_at": "2026-07-12T00:00:00",
    }
    row.update(overrides)
    return row
