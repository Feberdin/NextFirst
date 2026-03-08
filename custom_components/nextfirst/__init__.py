"""NextFirst Home Assistant integration bootstrap.

Purpose:
- Set up runtime objects, storage-backed manager, services, and platforms.

Input/Output:
- Input: ConfigEntry from Home Assistant.
- Output: loaded integration with registered entities and services.

Invariants:
- One manager per config entry.
- Manager initialization runs before platform forwarding.

Debugging:
- Setup problems are logged early; check config entry options and storage load path.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DEFAULT_OPTIONS, DOMAIN, PLATFORMS
from .manager import NextFirstManager
from .services import async_register_services
from .storage import NextFirstStorage

_LOGGER = logging.getLogger(__name__)

RUNTIME_MANAGER = "manager"


def _merged_options(entry: ConfigEntry) -> dict[str, Any]:
    options = dict(DEFAULT_OPTIONS)
    options.update(entry.options)
    return options


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NextFirst from config entry."""
    hass.data.setdefault(DOMAIN, {})

    storage = NextFirstStorage(hass)
    manager = NextFirstManager(hass, storage)
    await manager.async_initialize()

    hass.data[DOMAIN][entry.entry_id] = {
        RUNTIME_MANAGER: manager,
        "entry": entry,
    }

    await async_register_services(
        hass,
        manager,
        options_getter=lambda: _merged_options(entry),
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("NextFirst setup complete for entry_id=%s", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload one config entry and associated entities."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if not hass.data.get(DOMAIN):
        hass.data.pop(DOMAIN, None)

    _LOGGER.info("NextFirst unloaded for entry_id=%s", entry.entry_id)
    return True
