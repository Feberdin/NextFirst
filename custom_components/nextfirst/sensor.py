"""NextFirst sensor platform.

Purpose:
- Expose overview statistics as Home Assistant sensors for dashboards/automations.

Input/Output:
- Input: manager statistics snapshots.
- Output: sensor states + diagnostic attributes.

Invariants:
- Sensor state is derived from manager data, not duplicated local counters.

Debugging:
- Trigger a service mutation and verify SIGNAL_DATA_CHANGED updates sensor state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RUNTIME_MANAGER
from .const import DOMAIN, SIGNAL_DATA_CHANGED
from .manager import NextFirstManager


@dataclass(slots=True)
class NextFirstSensorDescription:
    """Declarative mapping from manager stats to sensor entities."""

    key: str
    name: str
    icon: str
    value_getter: Callable[[dict[str, Any]], Any]
    device_class: str | None = None
    attributes_getter: Callable[[dict[str, Any]], dict[str, Any]] | None = None


SENSORS = [
    NextFirstSensorDescription(
        key="open_count",
        name="NextFirst Open Count",
        icon="mdi:clipboard-text-outline",
        value_getter=lambda stats: stats["open_count"],
    ),
    NextFirstSensorDescription(
        key="skipped_count",
        name="NextFirst Skipped Count",
        icon="mdi:skip-next-circle-outline",
        value_getter=lambda stats: stats["skipped_count"],
    ),
    NextFirstSensorDescription(
        key="experienced_count",
        name="NextFirst Experienced Count",
        icon="mdi:party-popper",
        value_getter=lambda stats: stats["experienced_count"],
    ),
    NextFirstSensorDescription(
        key="experienced_this_month",
        name="NextFirst Experienced This Month",
        icon="mdi:calendar-check-outline",
        value_getter=lambda stats: stats["experienced_this_month"],
    ),
    NextFirstSensorDescription(
        key="last_ai_generation",
        name="NextFirst Last AI Generation",
        icon="mdi:robot-outline",
        value_getter=lambda stats: stats["last_ai_generation"] or "never",
    ),
    NextFirstSensorDescription(
        key="album_recent",
        name="NextFirst Album Recent",
        icon="mdi:image-multiple-outline",
        value_getter=lambda stats: len(stats["album_recent"]),
        attributes_getter=lambda stats: {"items": stats["album_recent"]},
    ),
    NextFirstSensorDescription(
        key="social_shares_total",
        name="NextFirst Social Shares Total",
        icon="mdi:share-variant-outline",
        value_getter=lambda stats: stats.get("social_shares_total", 0),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NextFirst sensor entities for one config entry."""
    runtime = hass.data[DOMAIN][entry.entry_id]
    manager: NextFirstManager = runtime[RUNTIME_MANAGER]
    async_add_entities(
        [NextFirstSensor(entry.entry_id, manager, description) for description in SENSORS],
        update_before_add=True,
    )


class NextFirstSensor(SensorEntity):
    """Sensor backed by manager statistics."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry_id: str,
        manager: NextFirstManager,
        description: NextFirstSensorDescription,
    ) -> None:
        self._entry_id = entry_id
        self._manager = manager
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_icon = description.icon
        self._state: Any = None
        self._attrs: dict[str, Any] = {}

    async def async_added_to_hass(self) -> None:
        """Register dispatcher callback for state refresh."""
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_DATA_CHANGED, self._handle_update)
        )

    async def async_update(self) -> None:
        """Fetch latest value from manager."""
        stats = self._manager.get_statistics()
        self._state = self.entity_description.value_getter(stats)
        if self.entity_description.attributes_getter:
            self._attrs = self.entity_description.attributes_getter(stats)
        else:
            self._attrs = {}

    @property
    def native_value(self) -> Any:
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return self._attrs

    @callback
    def _handle_update(self) -> None:
        self.async_schedule_update_ha_state(True)
