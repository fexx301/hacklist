from api import build_ics


def test_build_ics_all_day_event():
    ics = build_ics({
        "id": 42,
        "title": "AI Hack; Online, 2026",
        "url": "https://example.com/hack",
        "start_date": "2026-08-01",
        "end_date": "2026-08-03",
        "description": "Line one\nLine two",
    })
    assert "BEGIN:VCALENDAR" in ics
    assert "UID:hacklist-42@hacklist" in ics
    assert "DTSTART;VALUE=DATE:20260801" in ics
    # DTEND is exclusive → end date + 1
    assert "DTEND;VALUE=DATE:20260804" in ics
    assert "SUMMARY:AI Hack\\; Online\\, 2026" in ics
    assert "DESCRIPTION:Line one\\nLine two" in ics
    assert ics.endswith("END:VCALENDAR\r\n")


def test_build_ics_no_end_date():
    ics = build_ics({
        "id": 1,
        "title": "One Day",
        "url": "https://example.com",
        "start_date": "2026-08-01",
        "end_date": None,
    })
    assert "DTSTART;VALUE=DATE:20260801" in ics
    assert "DTEND;VALUE=DATE:20260802" in ics
