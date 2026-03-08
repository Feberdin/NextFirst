"""NextFirst domain model and pure business rules.

Purpose:
- Hold serializable data models and deterministic state transition logic.

Input/Output:
- Input: dictionaries from storage/services and explicit transition requests.
- Output: validated dataclass instances and serialized dictionaries.

Invariants:
- Required fields always exist for persisted experiences.
- State transitions follow allowed transition map.
- Unknown future fields are preserved in `extra`.

Debugging:
- Reproduce issues by round-tripping `Experience.from_dict(...).to_dict()`.
- Transition bugs are isolated in `ensure_transition_allowed`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from .errors import InvalidTransitionError, ValidationError


class ExperienceStatus(str, Enum):
    """Supported lifecycle states for one experience entry."""

    OPEN = "open"
    SKIPPED = "skipped"
    EXPERIENCED = "experienced"
    ARCHIVED = "archived"


class ExperienceOrigin(str, Enum):
    """Source of an experience."""

    MANUAL = "manual"
    AI = "ai"


ALLOWED_TRANSITIONS: dict[ExperienceStatus, set[ExperienceStatus]] = {
    ExperienceStatus.OPEN: {ExperienceStatus.SKIPPED, ExperienceStatus.EXPERIENCED},
    ExperienceStatus.SKIPPED: {ExperienceStatus.OPEN},
    ExperienceStatus.EXPERIENCED: {ExperienceStatus.ARCHIVED},
    ExperienceStatus.ARCHIVED: {ExperienceStatus.OPEN},
}


def utc_now_iso() -> str:
    """Return timezone-aware UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def ensure_transition_allowed(current: ExperienceStatus, target: ExperienceStatus) -> None:
    """Fail fast for invalid lifecycle transitions.

    Example:
    - Input: skipped -> experienced
    - Output: raises InvalidTransitionError with a clear remediation hint.
    """
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidTransitionError(
            f"Invalid transition from '{current.value}' to '{target.value}'. "
            "Allowed path: skipped experiences must be reactivated to open first."
        )


@dataclass(slots=True)
class MediaRef:
    """Reference to one media object, stored separately from core data."""

    media_id: str
    experience_id: str
    path: str
    thumbnail_path: str | None = None
    captured_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "media_id": self.media_id,
            "experience_id": self.experience_id,
            "path": self.path,
            "thumbnail_path": self.thumbnail_path,
            "captured_at": self.captured_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "MediaRef":
        return cls(
            media_id=str(raw.get("media_id", uuid4())),
            experience_id=str(raw.get("experience_id", "")),
            path=str(raw.get("path", "")),
            thumbnail_path=raw.get("thumbnail_path"),
            captured_at=raw.get("captured_at"),
            metadata=dict(raw.get("metadata") or {}),
        )


@dataclass(slots=True)
class StatusHistoryEntry:
    """One recorded status change for auditability and timeline support."""

    timestamp: str
    from_status: str
    to_status: str
    reason: str = "user_action"

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "from": self.from_status,
            "to": self.to_status,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "StatusHistoryEntry":
        return cls(
            timestamp=str(raw.get("timestamp", utc_now_iso())),
            from_status=str(raw.get("from", "unknown")),
            to_status=str(raw.get("to", "unknown")),
            reason=str(raw.get("reason", "user_action")),
        )


@dataclass(slots=True)
class Experience:
    """Main domain object for one planned or completed experience."""

    id: str
    title: str
    status: ExperienceStatus
    created_at: str
    updated_at: str
    origin: ExperienceOrigin
    description: str | None = None
    category: str | None = None
    tags: list[str] = field(default_factory=list)
    courage_level: str | None = None
    duration_minutes: int | None = None
    cost_level: str | None = None
    budget_per_person_eur: int | None = None
    travel_minutes: int | None = None
    age_group: str | None = None
    weather_hint: str | None = None
    indoor_outdoor: str | None = None
    family_friendly: bool | None = None
    notes: str | None = None
    completed_at: str | None = None
    rating: int | None = None
    would_repeat: bool | None = None
    location: str | None = None
    offer_url: str | None = None
    media: list[MediaRef] = field(default_factory=list)
    history: list[StatusHistoryEntry] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        title: str,
        origin: ExperienceOrigin = ExperienceOrigin.MANUAL,
        **kwargs: Any,
    ) -> "Experience":
        """Factory for a new open experience with generated ID and timestamps."""
        title = title.strip()
        if not title:
            raise ValidationError("Title is required and must not be empty.")

        now = utc_now_iso()
        return cls(
            id=str(uuid4()),
            title=title,
            status=ExperienceStatus.OPEN,
            created_at=now,
            updated_at=now,
            origin=origin,
            description=kwargs.get("description"),
            category=kwargs.get("category"),
            tags=list(kwargs.get("tags") or []),
            courage_level=kwargs.get("courage_level"),
            duration_minutes=kwargs.get("duration_minutes"),
            cost_level=kwargs.get("cost_level"),
            budget_per_person_eur=kwargs.get("budget_per_person_eur"),
            travel_minutes=kwargs.get("travel_minutes"),
            age_group=kwargs.get("age_group"),
            weather_hint=kwargs.get("weather_hint"),
            indoor_outdoor=kwargs.get("indoor_outdoor"),
            family_friendly=kwargs.get("family_friendly"),
            notes=kwargs.get("notes"),
            location=kwargs.get("location"),
            offer_url=kwargs.get("offer_url"),
            extra=dict(kwargs.get("extra") or {}),
        )

    def mark_status(self, target: ExperienceStatus, reason: str = "user_action") -> None:
        """Apply a validated status transition and update lifecycle fields."""
        ensure_transition_allowed(self.status, target)
        now = utc_now_iso()
        self.history.append(
            StatusHistoryEntry(
                timestamp=now,
                from_status=self.status.value,
                to_status=target.value,
                reason=reason,
            )
        )
        self.status = target
        self.updated_at = now

        # Completion timestamp is only set when first entering experienced state.
        if target == ExperienceStatus.EXPERIENCED and not self.completed_at:
            self.completed_at = now

    def to_dict(self) -> dict[str, Any]:
        """Serialize for persistent JSON storage."""
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "origin": self.origin.value,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "courage_level": self.courage_level,
            "duration_minutes": self.duration_minutes,
            "cost_level": self.cost_level,
            "budget_per_person_eur": self.budget_per_person_eur,
            "travel_minutes": self.travel_minutes,
            "age_group": self.age_group,
            "weather_hint": self.weather_hint,
            "indoor_outdoor": self.indoor_outdoor,
            "family_friendly": self.family_friendly,
            "notes": self.notes,
            "completed_at": self.completed_at,
            "rating": self.rating,
            "would_repeat": self.would_repeat,
            "location": self.location,
            "offer_url": self.offer_url,
            "media": [m.to_dict() for m in self.media],
            "history": [h.to_dict() for h in self.history],
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Experience":
        """Deserialize from storage while preserving unknown keys in `extra`."""
        required_title = str(raw.get("title", "")).strip()
        if not required_title:
            raise ValidationError("Stored experience is invalid: missing required field 'title'.")

        # Preserve future fields not explicitly known by this version.
        known_fields = {
            "id",
            "title",
            "status",
            "created_at",
            "updated_at",
            "origin",
            "description",
            "category",
            "tags",
            "courage_level",
            "duration_minutes",
            "cost_level",
            "budget_per_person_eur",
            "travel_minutes",
            "age_group",
            "weather_hint",
            "indoor_outdoor",
            "family_friendly",
            "notes",
            "completed_at",
            "rating",
            "would_repeat",
            "location",
            "offer_url",
            "media",
            "history",
            "extra",
        }
        dynamic_extra = {k: v for k, v in raw.items() if k not in known_fields}

        return cls(
            id=str(raw.get("id", uuid4())),
            title=required_title,
            status=ExperienceStatus(raw.get("status", ExperienceStatus.OPEN.value)),
            created_at=str(raw.get("created_at", utc_now_iso())),
            updated_at=str(raw.get("updated_at", utc_now_iso())),
            origin=ExperienceOrigin(raw.get("origin", ExperienceOrigin.MANUAL.value)),
            description=raw.get("description"),
            category=raw.get("category"),
            tags=list(raw.get("tags") or []),
            courage_level=raw.get("courage_level"),
            duration_minutes=raw.get("duration_minutes"),
            cost_level=raw.get("cost_level"),
            budget_per_person_eur=raw.get("budget_per_person_eur"),
            travel_minutes=raw.get("travel_minutes"),
            age_group=raw.get("age_group"),
            weather_hint=raw.get("weather_hint"),
            indoor_outdoor=raw.get("indoor_outdoor"),
            family_friendly=raw.get("family_friendly"),
            notes=raw.get("notes"),
            completed_at=raw.get("completed_at"),
            rating=raw.get("rating"),
            would_repeat=raw.get("would_repeat"),
            location=raw.get("location"),
            offer_url=raw.get("offer_url"),
            media=[MediaRef.from_dict(item) for item in (raw.get("media") or [])],
            history=[StatusHistoryEntry.from_dict(item) for item in (raw.get("history") or [])],
            extra={**dict(raw.get("extra") or {}), **dynamic_extra},
        )


def default_root_document() -> dict[str, Any]:
    """Return initial storage root with schema version and defaults."""
    return {
        "schema_version": 1,
        "updated_at": utc_now_iso(),
        "experiences": [],
        "categories": [
            "Natur",
            "Essen",
            "Ausflug",
            "Kreativ",
            "Lernen",
            "Familie",
            "Abenteuer",
            "Kultur",
            "Zuhause",
            "Technik",
            "Gesundheit",
            "Soziales",
            "Reisen",
            "Spiele",
        ],
        "stats_cache": {},
        "settings_snapshot": {},
        "social_history": [],
        "protocol_history": [],
    }
