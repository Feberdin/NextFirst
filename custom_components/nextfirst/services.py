"""NextFirst Home Assistant service registration.

Purpose:
- Expose domain operations as HA services with validation and clear errors.

Input/Output:
- Input: ServiceCall payloads from automations/dashboard/manual calls.
- Output: state mutations and optional service response dictionaries.

Invariants:
- Every mutation service delegates to manager methods.
- Validation/user errors are returned with actionable messages.

Debugging:
- Trigger services manually in Developer Tools and inspect logs + response payloads.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

import voluptuous as vol
from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import aiohttp_client

from .ai.service import generate_and_store_suggestions
from .const import (
    DOMAIN,
    SERVICE_ADD_NOTE,
    SERVICE_ATTACH_MEDIA,
    SERVICE_CREATE_EXPERIENCE,
    SERVICE_DELETE_EXPERIENCE,
    SERVICE_GENERATE_AI_SUGGESTIONS,
    SERVICE_GET_ALBUM,
    SERVICE_GET_STATISTICS,
    SERVICE_MARK_EXPERIENCED,
    SERVICE_MARK_SKIPPED,
    SERVICE_REACTIVATE_EXPERIENCE,
    SERVICE_UPDATE_EXPERIENCE,
)
from .errors import NextFirstError
from .manager import NextFirstManager

_LOGGER = logging.getLogger(__name__)


async def async_register_services(
    hass: HomeAssistant,
    manager: NextFirstManager,
    options_getter: Callable[[], dict[str, Any]],
) -> None:
    """Register all integration services once for the domain."""

    def to_ha_error(err: Exception) -> HomeAssistantError:
        if isinstance(err, NextFirstError):
            return HomeAssistantError(str(err))
        return HomeAssistantError(f"Unexpected NextFirst error: {err}")

    async def create_experience(call: ServiceCall) -> None:
        try:
            await manager.async_create_experience(
                title=call.data["title"],
                description=call.data.get("description"),
                category=call.data.get("category"),
                courage_level=call.data.get("courage_level"),
                duration_minutes=call.data.get("duration_minutes"),
                travel_minutes=call.data.get("travel_minutes"),
                notes=call.data.get("notes"),
            )
        except Exception as err:
            raise to_ha_error(err) from err

    async def update_experience(call: ServiceCall) -> None:
        try:
            exp_id = call.data["experience_id"]
            updates = {k: v for k, v in call.data.items() if k != "experience_id"}
            await manager.async_update_experience(exp_id, updates)
        except Exception as err:
            raise to_ha_error(err) from err

    async def delete_experience(call: ServiceCall) -> None:
        try:
            await manager.async_delete_experience(call.data["experience_id"])
        except Exception as err:
            raise to_ha_error(err) from err

    async def mark_skipped(call: ServiceCall) -> None:
        try:
            await manager.async_mark_skipped(call.data["experience_id"])
        except Exception as err:
            raise to_ha_error(err) from err

    async def reactivate_experience(call: ServiceCall) -> None:
        try:
            await manager.async_reactivate_experience(call.data["experience_id"])
        except Exception as err:
            raise to_ha_error(err) from err

    async def mark_experienced(call: ServiceCall) -> None:
        try:
            await manager.async_mark_experienced(
                call.data["experience_id"],
                note=call.data.get("note"),
                rating=call.data.get("rating"),
                would_repeat=call.data.get("would_repeat"),
                location=call.data.get("location"),
            )
        except Exception as err:
            raise to_ha_error(err) from err

    async def attach_media(call: ServiceCall) -> None:
        try:
            await manager.async_attach_media(
                experience_id=call.data["experience_id"],
                path=call.data["path"],
                thumbnail_path=call.data.get("thumbnail_path"),
                captured_at=call.data.get("captured_at"),
                metadata=call.data.get("metadata"),
            )
        except Exception as err:
            raise to_ha_error(err) from err

    async def add_note(call: ServiceCall) -> None:
        try:
            await manager.async_add_note(call.data["experience_id"], call.data["note"])
        except Exception as err:
            raise to_ha_error(err) from err

    async def generate_ai_suggestions(call: ServiceCall) -> None:
        try:
            session = aiohttp_client.async_get_clientsession(hass)
            created = await generate_and_store_suggestions(
                manager=manager,
                session=session,
                options=options_getter(),
                count_override=call.data.get("count"),
            )
            persistent_notification.async_create(
                hass,
                message=f"NextFirst hat {len(created)} KI-Vorschläge erzeugt.",
                title="NextFirst",
                notification_id="nextfirst_ai_result",
            )
        except Exception as err:
            raise to_ha_error(err) from err

    async def get_statistics(call: ServiceCall) -> dict[str, Any]:
        try:
            return manager.get_statistics()
        except Exception as err:
            raise to_ha_error(err) from err

    async def get_album(call: ServiceCall) -> dict[str, Any]:
        try:
            return {"album": manager.get_statistics().get("album_recent", [])}
        except Exception as err:
            raise to_ha_error(err) from err

    services: list[tuple[str, Any, vol.Schema | None]] = [
        (
            SERVICE_CREATE_EXPERIENCE,
            create_experience,
            vol.Schema(
                {
                    vol.Required("title"): str,
                    vol.Optional("description"): str,
                    vol.Optional("category"): str,
                    vol.Optional("courage_level"): str,
                    vol.Optional("duration_minutes"): int,
                    vol.Optional("travel_minutes"): int,
                    vol.Optional("notes"): str,
                }
            ),
        ),
        (
            SERVICE_UPDATE_EXPERIENCE,
            update_experience,
            vol.Schema(
                {
                    vol.Required("experience_id"): str,
                    vol.Optional("title"): str,
                    vol.Optional("description"): str,
                    vol.Optional("category"): str,
                    vol.Optional("courage_level"): str,
                    vol.Optional("duration_minutes"): int,
                    vol.Optional("travel_minutes"): int,
                    vol.Optional("notes"): str,
                    vol.Optional("rating"): int,
                    vol.Optional("would_repeat"): bool,
                    vol.Optional("location"): str,
                }
            ),
        ),
        (
            SERVICE_DELETE_EXPERIENCE,
            delete_experience,
            vol.Schema({vol.Required("experience_id"): str}),
        ),
        (
            SERVICE_MARK_SKIPPED,
            mark_skipped,
            vol.Schema({vol.Required("experience_id"): str}),
        ),
        (
            SERVICE_REACTIVATE_EXPERIENCE,
            reactivate_experience,
            vol.Schema({vol.Required("experience_id"): str}),
        ),
        (
            SERVICE_MARK_EXPERIENCED,
            mark_experienced,
            vol.Schema(
                {
                    vol.Required("experience_id"): str,
                    vol.Optional("note"): str,
                    vol.Optional("rating"): int,
                    vol.Optional("would_repeat"): bool,
                    vol.Optional("location"): str,
                }
            ),
        ),
        (
            SERVICE_ATTACH_MEDIA,
            attach_media,
            vol.Schema(
                {
                    vol.Required("experience_id"): str,
                    vol.Required("path"): str,
                    vol.Optional("thumbnail_path"): str,
                    vol.Optional("captured_at"): str,
                    vol.Optional("metadata"): dict,
                }
            ),
        ),
        (
            SERVICE_ADD_NOTE,
            add_note,
            vol.Schema({vol.Required("experience_id"): str, vol.Required("note"): str}),
        ),
        (
            SERVICE_GENERATE_AI_SUGGESTIONS,
            generate_ai_suggestions,
            vol.Schema({vol.Optional("count"): int}),
        ),
    ]

    for name, handler, schema in services:
        if hass.services.has_service(DOMAIN, name):
            continue
        hass.services.async_register(DOMAIN, name, handler, schema=schema)

    if not hass.services.has_service(DOMAIN, SERVICE_GET_STATISTICS):
        hass.services.async_register(
            DOMAIN,
            SERVICE_GET_STATISTICS,
            get_statistics,
            supports_response=SupportsResponse.ONLY,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_GET_ALBUM):
        hass.services.async_register(
            DOMAIN,
            SERVICE_GET_ALBUM,
            get_album,
            supports_response=SupportsResponse.ONLY,
        )

    _LOGGER.info("Registered NextFirst services")
