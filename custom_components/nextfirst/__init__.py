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
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

from .const import (
    CONF_AI_API_KEY,
    CONF_AI_ENABLED,
    CONF_DEBUG_ENABLED,
    DEFAULT_OPTIONS,
    DOMAIN,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)

RUNTIME_MANAGER = "manager"
RUNTIME_UNSUBS = "unsubs"


def _merged_options(entry: ConfigEntry) -> dict[str, Any]:
    """Merge defaults + config-entry data + options.

    Why this exists:
    - Config flow captures initial AI fields (for immediate usability).
    - Options flow remains the source for later edits and takes precedence.
    """
    options = dict(DEFAULT_OPTIONS)
    options.update(
        {
            CONF_AI_ENABLED: bool(entry.data.get(CONF_AI_ENABLED, options[CONF_AI_ENABLED])),
            CONF_AI_API_KEY: str(entry.data.get(CONF_AI_API_KEY, options[CONF_AI_API_KEY])),
        }
    )
    options.update(entry.options)
    return options


async def async_setup_entry(hass: "HomeAssistant", entry: "ConfigEntry") -> bool:
    """Set up NextFirst from config entry."""
    # Lazy import keeps config-flow import path resilient across HA versions.
    from .api import async_register_http_api
    from .manager import NextFirstManager
    from .panel import async_setup_panel
    from .scheduler import async_setup_monthly_scheduler
    from .services import async_register_services
    from .storage import NextFirstStorage

    hass.data.setdefault(DOMAIN, {})

    storage = NextFirstStorage(hass)
    manager = NextFirstManager(hass, storage)
    await manager.async_initialize()

    hass.data[DOMAIN][entry.entry_id] = {
        RUNTIME_MANAGER: manager,
        "entry": entry,
        RUNTIME_UNSUBS: [],
    }

    opts = _merged_options(entry)
    if bool(opts.get(CONF_DEBUG_ENABLED, False)):
        logging.getLogger("custom_components.nextfirst").setLevel(logging.DEBUG)
        _LOGGER.debug("NextFirst debug mode enabled from options.")

    await async_register_services(
        hass,
        manager,
        options_getter=lambda: _merged_options(entry),
    )
    await async_register_http_api(hass)
    await async_setup_panel(hass)
    unsub_scheduler = async_setup_monthly_scheduler(
        hass,
        manager,
        options_getter=lambda: _merged_options(entry),
    )
    hass.data[DOMAIN][entry.entry_id][RUNTIME_UNSUBS].append(unsub_scheduler)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("NextFirst setup complete for entry_id=%s", entry.entry_id)
    return True


async def async_unload_entry(hass: "HomeAssistant", entry: "ConfigEntry") -> bool:
    """Unload one config entry and associated entities."""
    from .panel import async_unload_panel

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    # Single-instance integration: remove panel when unloading the entry.
    await async_unload_panel(hass)

    runtime = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    for unsub in runtime.get(RUNTIME_UNSUBS, []):
        try:
            unsub()
        except Exception:
            continue

    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if not hass.data.get(DOMAIN):
        hass.data.pop(DOMAIN, None)

    _LOGGER.info("NextFirst unloaded for entry_id=%s", entry.entry_id)
    return True
