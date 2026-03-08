"""NextFirst monthly scheduler.

Purpose:
- Trigger monthly summary generation at configured day/hour.

Input/Output:
- Input: Home Assistant time events + integration options.
- Output: notifications for monthly summaries.

Invariants:
- At most one run per month key (`YYYY-MM`) for each loaded entry.
- Scheduler remains passive unless monthly_summary_enabled is true.

Debugging:
- Enable debug mode and inspect scheduler logs + persistent notifications.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable

from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change

from .const import (
    CONF_MONTHLY_SUMMARY_DAY,
    CONF_MONTHLY_SUMMARY_ENABLED,
    CONF_MONTHLY_SUMMARY_HOUR,
)
from .manager import NextFirstManager
from .monthly_summary import build_monthly_summary

_LOGGER = logging.getLogger(__name__)


def async_setup_monthly_scheduler(
    hass: HomeAssistant,
    manager: NextFirstManager,
    options_getter: Callable[[], dict[str, Any]],
) -> Callable[[], None]:
    """Register monthly scheduler callback and return unsubscribe handler."""
    runtime_state: dict[str, str | None] = {"last_month_key": None}

    @callback
    async def _on_tick(now: datetime) -> None:
        opts = options_getter()
        if not bool(opts.get(CONF_MONTHLY_SUMMARY_ENABLED, False)):
            return

        target_day = int(opts.get(CONF_MONTHLY_SUMMARY_DAY, 1))
        target_hour = int(opts.get(CONF_MONTHLY_SUMMARY_HOUR, 9))

        if now.day != target_day or now.hour != target_hour:
            return

        month_key = now.strftime("%Y-%m")
        if runtime_state["last_month_key"] == month_key:
            return

        summary = build_monthly_summary(manager.list_all(), month_key)
        runtime_state["last_month_key"] = month_key

        persistent_notification.async_create(
            hass,
            message=summary["summary_text"],
            title=f"NextFirst Monatsrückblick {month_key}",
            notification_id=f"nextfirst_monthly_summary_{month_key}",
        )

        _LOGGER.debug("Monthly summary created for %s", month_key)

    # Check every full hour, then evaluate day/hour guard in callback.
    unsubscribe = async_track_time_change(hass, _on_tick, minute=0, second=0)
    return unsubscribe
