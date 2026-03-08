"""NextFirst application manager.

Purpose:
- Orchestrate domain operations, persistence, and integration update signals.

Input/Output:
- Input: service payloads and option settings.
- Output: updated persistent state + lightweight dict responses for services/entities.

Invariants:
- Experience IDs are unique.
- Every mutation persists data and emits one data-changed signal.
- Invalid records are skipped safely during load, never crashing the whole integration.

Debugging:
- Track operation path via INFO logs and check SIGNAL_DATA_CHANGED subscribers.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import SIGNAL_DATA_CHANGED
from .domain import Experience, ExperienceOrigin, ExperienceStatus, MediaRef, default_root_document, utc_now_iso
from .errors import ExperienceNotFoundError, ValidationError
from .storage import NextFirstStorage

_LOGGER = logging.getLogger(__name__)


class NextFirstManager:
    """Runtime state manager for all NextFirst data operations."""

    def __init__(self, hass: HomeAssistant, storage: NextFirstStorage) -> None:
        self.hass = hass
        self.storage = storage
        self._doc: dict[str, Any] = default_root_document()
        self._experiences: dict[str, Experience] = {}
        self._lock = asyncio.Lock()
        self.last_ai_generation: str | None = None

    async def async_initialize(self) -> None:
        """Load persisted data and build in-memory index."""
        self._doc = await self.storage.async_load()
        self._experiences.clear()

        for raw in self._doc.get("experiences", []):
            try:
                item = Experience.from_dict(raw)
                self._experiences[item.id] = item
            except Exception as err:  # defensive load for damaged entries
                _LOGGER.warning(
                    "Skipping invalid experience while loading storage. entry=%s reason=%s",
                    raw,
                    err,
                )

        _LOGGER.info("NextFirst initialized with %s experiences", len(self._experiences))
        await self.async_record_protocol_event(
            action="initialize",
            message=f"Loaded {len(self._experiences)} experience entries.",
        )

    def _append_protocol_event(
        self,
        *,
        level: str,
        action: str,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Append one protocol event to in-memory document."""
        event = {
            "timestamp": utc_now_iso(),
            "level": level,
            "action": action,
            "message": message,
            "context": context or {},
        }
        self._doc.setdefault("protocol_history", [])
        self._doc["protocol_history"].append(event)
        self._doc["protocol_history"] = self._doc["protocol_history"][-500:]
        return event

    async def async_record_protocol_event(
        self,
        *,
        action: str,
        message: str,
        level: str = "info",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Persist one protocol event for diagnostics and support."""
        async with self._lock:
            event = self._append_protocol_event(
                level=level,
                action=action,
                message=message,
                context=context,
            )
            await self._persist_and_notify()
            return event

    def _require(self, experience_id: str) -> Experience:
        item = self._experiences.get(experience_id)
        if item is None:
            raise ExperienceNotFoundError(
                f"ExperienceNotFound: id={experience_id} not found. "
                "Fix: refresh list and verify the selected experience ID."
            )
        return item

    async def _persist_and_notify(self) -> None:
        """Persist runtime state and notify entities/listeners in one place."""
        self._doc["updated_at"] = utc_now_iso()
        self._doc["experiences"] = [exp.to_dict() for exp in self._experiences.values()]
        self._doc.setdefault("social_history", [])
        await self.storage.async_save(self._doc)
        async_dispatcher_send(self.hass, SIGNAL_DATA_CHANGED)

    async def async_create_experience(self, title: str, **kwargs: Any) -> dict[str, Any]:
        """Create and persist one new experience in open state."""
        async with self._lock:
            origin = ExperienceOrigin(kwargs.pop("origin", ExperienceOrigin.MANUAL.value))
            exp = Experience.create(title=title, origin=origin, **kwargs)
            self._experiences[exp.id] = exp
            self._append_protocol_event(
                level="info",
                action="create_experience",
                message=f"Created experience '{exp.title}'.",
                context={"experience_id": exp.id, "origin": exp.origin.value},
            )
            await self._persist_and_notify()
            return exp.to_dict()

    async def async_update_experience(self, experience_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Update mutable fields for an existing experience."""
        async with self._lock:
            exp = self._require(experience_id)

            # Why explicit whitelist: avoids silent schema drift through arbitrary writes.
            mutable_fields = {
                "title",
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
                "rating",
                "would_repeat",
                "location",
            }

            for key, value in updates.items():
                if key in mutable_fields:
                    setattr(exp, key, value)

            if not str(exp.title).strip():
                raise ValidationError("Title must not be empty. Fix: provide a non-empty title.")

            exp.updated_at = utc_now_iso()
            self._append_protocol_event(
                level="info",
                action="update_experience",
                message=f"Updated experience '{exp.title}'.",
                context={"experience_id": exp.id, "updated_fields": list(updates.keys())},
            )
            await self._persist_and_notify()
            return exp.to_dict()

    async def async_delete_experience(self, experience_id: str) -> None:
        """Delete one experience by id."""
        async with self._lock:
            _ = self._require(experience_id)
            del self._experiences[experience_id]
            self._append_protocol_event(
                level="info",
                action="delete_experience",
                message="Deleted one experience entry.",
                context={"experience_id": experience_id},
            )
            await self._persist_and_notify()

    async def async_mark_skipped(self, experience_id: str) -> dict[str, Any]:
        async with self._lock:
            exp = self._require(experience_id)
            exp.mark_status(ExperienceStatus.SKIPPED)
            self._append_protocol_event(
                level="info",
                action="mark_skipped",
                message=f"Marked '{exp.title}' as skipped.",
                context={"experience_id": exp.id},
            )
            await self._persist_and_notify()
            return exp.to_dict()

    async def async_reactivate_experience(self, experience_id: str) -> dict[str, Any]:
        async with self._lock:
            exp = self._require(experience_id)
            exp.mark_status(ExperienceStatus.OPEN)
            self._append_protocol_event(
                level="info",
                action="reactivate_experience",
                message=f"Reactivated '{exp.title}' to open.",
                context={"experience_id": exp.id},
            )
            await self._persist_and_notify()
            return exp.to_dict()

    async def async_mark_experienced(
        self,
        experience_id: str,
        note: str | None = None,
        rating: int | None = None,
        would_repeat: bool | None = None,
        location: str | None = None,
    ) -> dict[str, Any]:
        """Mark one experience as completed and optionally enrich completion metadata."""
        async with self._lock:
            exp = self._require(experience_id)
            exp.mark_status(ExperienceStatus.EXPERIENCED)
            if note is not None:
                exp.notes = note
            if rating is not None:
                exp.rating = rating
            if would_repeat is not None:
                exp.would_repeat = would_repeat
            if location is not None:
                exp.location = location
            self._append_protocol_event(
                level="info",
                action="mark_experienced",
                message=f"Marked '{exp.title}' as experienced.",
                context={"experience_id": exp.id},
            )
            await self._persist_and_notify()
            return exp.to_dict()

    async def async_archive_experience(self, experience_id: str) -> dict[str, Any]:
        """Archive one experienced entry for later rediscovery."""
        async with self._lock:
            exp = self._require(experience_id)
            exp.mark_status(ExperienceStatus.ARCHIVED)
            self._append_protocol_event(
                level="info",
                action="archive_experience",
                message=f"Archived '{exp.title}'.",
                context={"experience_id": exp.id},
            )
            await self._persist_and_notify()
            return exp.to_dict()

    async def async_attach_media(
        self,
        experience_id: str,
        path: str,
        thumbnail_path: str | None = None,
        captured_at: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Attach a media reference to an experience.

        Example:
        - Input: path='/media/nextfirst/2026/03/pic.jpg'
        - Output: media entry appended to experience.media with generated media_id.
        """
        if not path or not str(path).strip():
            raise ValidationError(
                "Media path is required. Fix: provide an absolute or HA media path."
            )

        async with self._lock:
            exp = self._require(experience_id)
            media = MediaRef(
                media_id=str(uuid4()),
                experience_id=experience_id,
                path=path,
                thumbnail_path=thumbnail_path,
                captured_at=captured_at or utc_now_iso(),
                metadata=metadata or {},
            )
            exp.media.append(media)
            exp.updated_at = utc_now_iso()
            self._append_protocol_event(
                level="info",
                action="attach_media",
                message=f"Attached media to '{exp.title}'.",
                context={"experience_id": exp.id, "media_id": media.media_id, "path": media.path},
            )
            await self._persist_and_notify()
            return media.to_dict()

    async def async_add_note(self, experience_id: str, note: str) -> dict[str, Any]:
        """Update free-text note for one experience."""
        async with self._lock:
            exp = self._require(experience_id)
            exp.notes = note
            exp.updated_at = utc_now_iso()
            self._append_protocol_event(
                level="info",
                action="add_note",
                message=f"Updated note on '{exp.title}'.",
                context={"experience_id": exp.id},
            )
            await self._persist_and_notify()
            return exp.to_dict()

    def get_statistics(self) -> dict[str, Any]:
        """Compute lightweight statistics for sensors and service responses."""
        open_count = 0
        skipped_count = 0
        experienced_count = 0

        for exp in self._experiences.values():
            if exp.status == ExperienceStatus.OPEN:
                open_count += 1
            elif exp.status == ExperienceStatus.SKIPPED:
                skipped_count += 1
            elif exp.status in (ExperienceStatus.EXPERIENCED, ExperienceStatus.ARCHIVED):
                experienced_count += 1

        experienced_sorted = sorted(
            [e for e in self._experiences.values() if e.completed_at],
            key=lambda x: x.completed_at or "",
            reverse=True,
        )

        return {
            "open_count": open_count,
            "skipped_count": skipped_count,
            "experienced_count": experienced_count,
            "experienced_this_month": self._experienced_this_month(),
            "last_ai_generation": self.last_ai_generation,
            "album_recent": [self._album_item(e) for e in experienced_sorted[:20]],
            "social_shares_total": len(self._doc.get("social_history", [])),
        }

    def _experienced_this_month(self) -> int:
        now_prefix = utc_now_iso()[:7]  # YYYY-MM
        return sum(1 for e in self._experiences.values() if (e.completed_at or "").startswith(now_prefix))

    @staticmethod
    def _album_item(exp: Experience) -> dict[str, Any]:
        """Build compact album item for timeline-like visualization in attributes."""
        first_media = exp.media[0].to_dict() if exp.media else None
        return {
            "id": exp.id,
            "title": exp.title,
            "category": exp.category,
            "completed_at": exp.completed_at,
            "location": exp.location,
            "budget_per_person_eur": exp.budget_per_person_eur,
            "note": exp.notes,
            "rating": exp.rating,
            "would_repeat": exp.would_repeat,
            "media_preview": first_media,
            "media_count": len(exp.media),
        }

    def list_by_status(self, status: ExperienceStatus) -> list[dict[str, Any]]:
        """Return serialized list for UI/service consumption."""
        return [e.to_dict() for e in self._experiences.values() if e.status == status]

    def list_all(self) -> list[dict[str, Any]]:
        """Return all entries sorted by updated timestamp descending."""
        return [
            e.to_dict()
            for e in sorted(self._experiences.values(), key=lambda x: x.updated_at, reverse=True)
        ]

    async def async_record_share_event(
        self,
        *,
        source_type: str,
        source_id: str | None,
        provider: str,
        ok: bool,
        message: str,
    ) -> dict[str, Any]:
        """Persist one social sharing attempt for traceability and debugging."""
        async with self._lock:
            event = {
                "timestamp": utc_now_iso(),
                "source_type": source_type,
                "source_id": source_id,
                "provider": provider,
                "ok": ok,
                "message": message,
            }
            self._doc.setdefault("social_history", [])
            self._doc["social_history"].append(event)
            self._doc["social_history"] = self._doc["social_history"][-200:]
            self._append_protocol_event(
                level="info" if ok else "warning",
                action="social_share",
                message=f"Social share ({provider}) result: {message}",
                context={
                    "source_type": source_type,
                    "source_id": source_id,
                    "provider": provider,
                    "ok": ok,
                },
            )
            await self._persist_and_notify()
            return event

    def get_share_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return newest social share events first."""
        history = list(self._doc.get("social_history", []))
        return list(reversed(history[-max(1, limit) :]))

    def get_protocol_history(self, limit: int = 200) -> list[dict[str, Any]]:
        """Return newest protocol events first."""
        history = list(self._doc.get("protocol_history", []))
        return list(reversed(history[-max(1, limit) :]))
