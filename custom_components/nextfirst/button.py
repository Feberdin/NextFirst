"""NextFirst button platform.

Purpose:
- Provide one-click actions, currently AI suggestion generation.

Input/Output:
- Input: button press in Home Assistant UI.
- Output: invokes corresponding NextFirst service.

Invariants:
- Button does not contain business logic; it delegates to services.

Debugging:
- If button does nothing, check service registration and logs for service call errors.
"""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SERVICE_GENERATE_AI_SUGGESTIONS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities for one config entry."""
    async_add_entities([GenerateSuggestionsButton(entry.entry_id)])


class GenerateSuggestionsButton(ButtonEntity):
    """Dashboard button for generating AI suggestions on demand."""

    _attr_has_entity_name = True
    _attr_name = "NextFirst Generate Suggestions"
    _attr_icon = "mdi:lightbulb-on-outline"

    def __init__(self, entry_id: str) -> None:
        self._attr_unique_id = f"{entry_id}_generate_suggestions"

    async def async_press(self) -> None:
        """Call generation service when the button is pressed."""
        await self.hass.services.async_call(
            DOMAIN,
            SERVICE_GENERATE_AI_SUGGESTIONS,
            {},
            blocking=True,
        )
