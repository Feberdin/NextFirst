"""NextFirst sidebar panel registration.

Purpose:
- Register a custom Home Assistant sidebar panel and serve its frontend module.

Input/Output:
- Input: Home Assistant runtime during integration setup.
- Output: visible sidebar item `NextFirst` at `/nextfirst`.

Invariants:
- Static module URL remains stable for cache-safe panel loading.

Debugging:
- If sidebar entry is missing, verify frontend dependency and static path registration logs.
"""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PANEL_PATH = "nextfirst"
STATIC_URL = "/nextfirst_static"


async def async_setup_panel(hass: HomeAssistant) -> None:
    """Register static panel resources and sidebar item."""
    static_dir = Path(__file__).parent / "frontend"

    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL, str(static_dir), cache_headers=False)]
        )
    except Exception:  # pragma: no cover - idempotent setup on reload
        _LOGGER.debug("NextFirst static path already registered", exc_info=True)

    try:
        await frontend.async_register_built_in_panel(
            hass,
            component_name="custom",
            frontend_url_path=PANEL_PATH,
            sidebar_title="NextFirst",
            sidebar_icon="mdi:compass-outline",
            config={
                "_panel_custom": {
                    "name": "nextfirst-panel",
                    "module_url": f"{STATIC_URL}/nextfirst-panel.js",
                    "embed_iframe": False,
                    "trust_external": False,
                }
            },
            require_admin=False,
        )
    except Exception:  # pragma: no cover - idempotent setup on reload
        _LOGGER.debug("NextFirst panel already registered", exc_info=True)

    _LOGGER.info("NextFirst panel registered at /%s", PANEL_PATH)


async def async_unload_panel(hass: HomeAssistant) -> None:
    """Remove the sidebar panel on integration unload."""
    try:
        await frontend.async_remove_panel(hass, PANEL_PATH)
    except Exception:  # pragma: no cover - defensive cleanup
        _LOGGER.debug("NextFirst panel cleanup skipped", exc_info=True)
