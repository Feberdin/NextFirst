"""Tests for monthly summary generation.

Purpose:
- Verify monthly recap metrics and text generation from completed experiences.

Input/Output:
- Input: serialized experience dictionaries.
- Output: deterministic summary dict with counts and category stats.

Invariants:
- Only experienced/archived items from requested month are counted.

Debugging:
- Compare input completed_at/status values against summary counters.
"""

from __future__ import annotations

from custom_components.nextfirst.monthly_summary import build_monthly_summary


def test_monthly_summary_happy_path_counts_and_top_category() -> None:
    experiences = [
        {
            "id": "1",
            "status": "experienced",
            "title": "Kletterpark",
            "category": "Abenteuer",
            "completed_at": "2026-03-10T10:00:00+00:00",
            "would_repeat": True,
            "media": [{"path": "/media/a.jpg"}],
        },
        {
            "id": "2",
            "status": "archived",
            "title": "Museum bei Nacht",
            "category": "Kultur",
            "completed_at": "2026-03-11T10:00:00+00:00",
            "would_repeat": False,
            "media": [],
        },
        {
            "id": "3",
            "status": "experienced",
            "title": "Sonnenaufgangswanderung",
            "category": "Abenteuer",
            "completed_at": "2026-03-13T06:00:00+00:00",
            "would_repeat": True,
            "media": [{"path": "/media/b.jpg"}],
        },
        {
            "id": "4",
            "status": "open",
            "title": "Nicht abgeschlossen",
            "category": "Lernen",
            "completed_at": "2026-03-20T06:00:00+00:00",
            "would_repeat": False,
            "media": [],
        },
    ]

    result = build_monthly_summary(experiences, "2026-03")

    assert result["total_experienced"] == 3
    assert result["top_category"] == "Abenteuer"
    assert result["with_media"] == 2
    assert result["would_repeat_count"] == 2
    assert "Monatsrückblick 2026-03" in result["summary_text"]


def test_monthly_summary_negative_no_entries_for_month() -> None:
    experiences = [
        {
            "id": "1",
            "status": "experienced",
            "title": "Vorheriger Monat",
            "category": "Natur",
            "completed_at": "2026-02-10T10:00:00+00:00",
            "would_repeat": True,
            "media": [{"path": "/media/a.jpg"}],
        }
    ]

    result = build_monthly_summary(experiences, "2026-03")

    assert result["total_experienced"] == 0
    assert "noch keine Erlebnisse" in result["summary_text"]
