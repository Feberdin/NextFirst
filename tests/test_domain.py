"""Tests for NextFirst domain logic.

Purpose:
- Validate status transitions, serialization stability, and key error cases.

Input/Output:
- Input: domain objects and transition requests.
- Output: deterministic pass/fail for business rules.

Invariants:
- Illegal transitions fail loudly.
- Unknown fields survive round-trip via `extra`.

Debugging:
- Run pytest with -k domain -vv to isolate failures quickly.
"""

from __future__ import annotations

import pytest

from custom_components.nextfirst.domain import (
    Experience,
    ExperienceStatus,
    default_root_document,
)
from custom_components.nextfirst.errors import InvalidTransitionError, ValidationError


def test_create_experience_happy_path() -> None:
    exp = Experience.create(title="Zum ersten Mal Klettern")

    assert exp.title == "Zum ersten Mal Klettern"
    assert exp.status == ExperienceStatus.OPEN
    assert exp.id


def test_invalid_empty_title_negative() -> None:
    with pytest.raises(ValidationError):
        Experience.create(title="  ")


def test_status_transition_open_to_experienced_happy_path() -> None:
    exp = Experience.create(title="Barfusspark besuchen")
    exp.mark_status(ExperienceStatus.EXPERIENCED)

    assert exp.status == ExperienceStatus.EXPERIENCED
    assert exp.completed_at is not None
    assert exp.history[-1].to_status == ExperienceStatus.EXPERIENCED.value


def test_status_transition_skipped_to_experienced_negative() -> None:
    exp = Experience.create(title="Nachtwanderung")
    exp.mark_status(ExperienceStatus.SKIPPED)

    with pytest.raises(InvalidTransitionError):
        exp.mark_status(ExperienceStatus.EXPERIENCED)


def test_roundtrip_preserves_unknown_fields_edge_case() -> None:
    raw = {
        "id": "abc",
        "title": "Unbekanntes Feld testen",
        "status": "open",
        "created_at": "2026-03-08T10:00:00+00:00",
        "updated_at": "2026-03-08T10:00:00+00:00",
        "origin": "manual",
        "future_field": {"x": 1},
    }

    exp = Experience.from_dict(raw)
    dumped = exp.to_dict()

    assert exp.extra["future_field"] == {"x": 1}
    assert dumped["extra"]["future_field"] == {"x": 1}


def test_default_root_document_contains_schema_and_defaults() -> None:
    doc = default_root_document()

    assert doc["schema_version"] == 1
    assert isinstance(doc["experiences"], list)
    assert "Natur" in doc["categories"]
