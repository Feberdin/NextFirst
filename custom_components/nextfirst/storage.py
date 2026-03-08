"""NextFirst persistent storage wrapper.

Purpose:
- Provide robust loading/saving/migration around Home Assistant Store.

Input/Output:
- Input: root document and experience list from manager.
- Output: validated/migrated root document for runtime use.

Invariants:
- Stored document always includes `schema_version` and `experiences` list.
- Migrations are idempotent.

Debugging:
- Enable DEBUG logs and inspect schema_version + migration path.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORAGE_KEY, STORAGE_VERSION
from .domain import default_root_document
from .errors import NextFirstSystemError

_LOGGER = logging.getLogger(__name__)


class NextFirstStorage:
    """Storage abstraction that shields manager from raw persistence details."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._store = Store[dict[str, Any]](hass, STORAGE_VERSION, STORAGE_KEY)

    async def async_load(self) -> dict[str, Any]:
        """Load and migrate storage document, returning runtime-safe structure."""
        raw = await self._store.async_load()
        if raw is None:
            _LOGGER.info("%s storage not found. Creating default document.", DOMAIN)
            return default_root_document()

        if not isinstance(raw, dict):
            raise NextFirstSystemError(
                "Storage is corrupted: root document is not an object. "
                "Fix: remove invalid storage file and restart Home Assistant."
            )

        return self._migrate_if_needed(raw)

    async def async_save(self, data: dict[str, Any]) -> None:
        """Persist full root document."""
        try:
            await self._store.async_save(data)
        except Exception as err:  # pragma: no cover - defensive HA boundary
            raise NextFirstSystemError(
                f"Failed to save NextFirst data. Reason: {err}. "
                "Fix: check filesystem permissions and available disk space."
            ) from err

    def _migrate_if_needed(self, doc: dict[str, Any]) -> dict[str, Any]:
        """Apply forward-only migrations from older versions."""
        version = int(doc.get("schema_version", 1))

        # Why this exists: future versions can evolve safely without hard crashes.
        if version == 1:
            merged = default_root_document()
            merged.update(doc)
            merged.setdefault("experiences", [])
            merged["schema_version"] = 1
            return merged

        raise NextFirstSystemError(
            f"Unsupported schema_version={version}. "
            "Fix: update integration to a compatible version."
        )
