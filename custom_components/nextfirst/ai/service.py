"""AI orchestration service.

Purpose:
- Build provider context from integration options and create open experiences from drafts.

Input/Output:
- Input: manager instance, options, and requested suggestion count override.
- Output: list of created NextFirst experiences.

Invariants:
- AI is optional and must never block non-AI functionality.
- Generated entries are marked with origin=ai.

Debugging:
- Check options snapshot and provider selection when generation fails.
"""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientSession

from ..const import (
    CONF_AI_API_KEY,
    CONF_AI_ENABLED,
    CONF_AI_MAX_TOKENS,
    CONF_AI_MODEL,
    CONF_AI_PROVIDER,
    CONF_AI_SUGGESTION_COUNT,
    CONF_AI_TEMPERATURE,
    CONF_BUDGET_PER_PERSON_EUR,
    CONF_CUSTOM_INTERESTS,
    CONF_EXCLUSIONS,
    CONF_FAMILY_FRIENDLY_ONLY,
    CONF_GOOD_WEATHER_ONLY,
    CONF_MAX_TRAVEL_MINUTES,
    CONF_TRAVEL_ORIGIN,
    CONF_PREFERRED_CATEGORIES,
    CONF_PREFERRED_COURAGE_LEVELS,
)
from ..domain import ExperienceOrigin, utc_now_iso
from ..errors import AIProviderError, ValidationError
from ..manager import NextFirstManager
from .providers.base import SuggestionContext
from .providers.openai import OpenAISuggestionProvider

_LOGGER = logging.getLogger(__name__)


def _resolve_origin_coordinates(manager: NextFirstManager, travel_origin: str) -> tuple[float, float] | None:
    """Resolve travel origin from entity id (for example zone.home) or 'lat,lon' text."""
    raw = str(travel_origin or "").strip()
    if not raw:
        return None

    if "," in raw:
        try:
            lat_s, lon_s = [part.strip() for part in raw.split(",", maxsplit=1)]
            return (float(lat_s), float(lon_s))
        except (TypeError, ValueError):
            return None

    state = manager.hass.states.get(raw)
    if state is None:
        return None
    lat = state.attributes.get("latitude")
    lon = state.attributes.get("longitude")
    if lat is None or lon is None:
        return None
    try:
        return (float(lat), float(lon))
    except (TypeError, ValueError):
        return None


async def _geocode_location(
    session: ClientSession,
    location: str,
) -> tuple[float, float] | None:
    """Resolve a human-readable location to coordinates via Nominatim."""
    query = str(location or "").strip()
    if not query:
        return None
    try:
        async with session.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "jsonv2", "limit": 1},
            headers={"User-Agent": "NextFirst/0.3"},
            timeout=20,
        ) as resp:
            if resp.status >= 400:
                return None
            payload = await resp.json(content_type=None)
            if not payload:
                return None
            first = payload[0]
            return (float(first["lat"]), float(first["lon"]))
    except Exception:
        return None


async def _estimate_drive_minutes(
    session: ClientSession,
    origin: tuple[float, float],
    dest: tuple[float, float],
) -> int | None:
    """Estimate drive duration in minutes using OSRM public routing API."""
    try:
        async with session.get(
            (
                "https://router.project-osrm.org/route/v1/driving/"
                f"{origin[1]},{origin[0]};{dest[1]},{dest[0]}"
            ),
            params={"overview": "false"},
            timeout=20,
        ) as resp:
            if resp.status >= 400:
                return None
            payload = await resp.json(content_type=None)
            routes = payload.get("routes") or []
            if not routes:
                return None
            seconds = float(routes[0].get("duration", 0))
            if seconds <= 0:
                return None
            return int(round(seconds / 60))
    except Exception:
        return None


async def generate_and_store_suggestions(
    manager: NextFirstManager,
    session: ClientSession,
    options: dict[str, Any],
    count_override: int | None = None,
) -> list[dict[str, Any]]:
    """Generate AI suggestions and store them as open experiences."""
    ai_enabled = bool(options.get(CONF_AI_ENABLED, False))
    if not ai_enabled:
        raise ValidationError(
            "AI suggestions are disabled. Fix: enable AI in NextFirst options first."
        )

    provider_name = str(options.get(CONF_AI_PROVIDER, "openai"))
    if provider_name != "openai":
        raise AIProviderError(
            f"Unsupported AI provider '{provider_name}'. Fix: use provider 'openai'."
        )

    suggestion_count = int(count_override or options.get(CONF_AI_SUGGESTION_COUNT, 2))
    target_count = max(1, min(suggestion_count, 20))
    context = SuggestionContext(
        suggestion_count=target_count,
        max_travel_minutes=int(options.get(CONF_MAX_TRAVEL_MINUTES, 60)),
        family_friendly_only=bool(options.get(CONF_FAMILY_FRIENDLY_ONLY, False)),
        good_weather_only=bool(options.get(CONF_GOOD_WEATHER_ONLY, False)),
        budget_per_person_eur=int(options.get(CONF_BUDGET_PER_PERSON_EUR, 0) or 0),
        travel_origin=str(options.get(CONF_TRAVEL_ORIGIN, "zone.home") or "zone.home"),
        preferred_categories=list(options.get(CONF_PREFERRED_CATEGORIES, [])),
        preferred_courage_levels=list(options.get(CONF_PREFERRED_COURAGE_LEVELS, [])),
        custom_interests=str(options.get(CONF_CUSTOM_INTERESTS, "")),
        exclusions=str(options.get(CONF_EXCLUSIONS, "")),
    )
    origin_coords = _resolve_origin_coordinates(manager, context.travel_origin)

    provider = OpenAISuggestionProvider(
        session=session,
        api_key=str(options.get(CONF_AI_API_KEY, "")),
        model=str(options.get(CONF_AI_MODEL, "gpt-4.1-mini")),
        temperature=float(options.get(CONF_AI_TEMPERATURE, 0.7)),
        max_tokens=int(options.get(CONF_AI_MAX_TOKENS, 600)),
    )

    drafts = []
    seen_titles: set[str] = set()
    attempts = 0
    dropped_missing_location = 0
    dropped_distance = 0
    fallback_without_verified_route = 0
    # Providers may return fewer suggestions than requested; retry with remaining count.
    while len(drafts) < target_count and attempts < 4:
        attempts += 1
        remaining = target_count - len(drafts)
        batch = await provider.generate(
            SuggestionContext(
                suggestion_count=remaining,
                max_travel_minutes=context.max_travel_minutes,
                family_friendly_only=context.family_friendly_only,
                good_weather_only=context.good_weather_only,
                budget_per_person_eur=context.budget_per_person_eur,
                travel_origin=context.travel_origin,
                preferred_categories=context.preferred_categories,
                preferred_courage_levels=context.preferred_courage_levels,
                custom_interests=context.custom_interests,
                exclusions=context.exclusions,
            )
        )
        for draft in batch:
            key = draft.title.strip().lower()
            if not key or key in seen_titles:
                continue
            if not str(draft.location or "").strip():
                dropped_missing_location += 1
                continue
            if origin_coords is not None:
                coords = await _geocode_location(session, str(draft.location))
                if coords is not None:
                    drive_minutes = await _estimate_drive_minutes(session, origin_coords, coords)
                    if drive_minutes is not None:
                        if drive_minutes > context.max_travel_minutes:
                            dropped_distance += 1
                            continue
                        draft.travel_minutes = drive_minutes
                    else:
                        # Keep draft if routing service is unavailable; still enforce
                        # model-provided travel time when present.
                        fallback_without_verified_route += 1
                        if (
                            draft.travel_minutes is not None
                            and draft.travel_minutes > context.max_travel_minutes
                        ):
                            dropped_distance += 1
                            continue
                else:
                    # Keep draft if geocoding fails; still enforce model-provided time
                    # when available so max travel preference remains active.
                    fallback_without_verified_route += 1
                    if (
                        draft.travel_minutes is not None
                        and draft.travel_minutes > context.max_travel_minutes
                    ):
                        dropped_distance += 1
                        continue
            elif draft.travel_minutes is not None and draft.travel_minutes > context.max_travel_minutes:
                dropped_distance += 1
                continue
            seen_titles.add(key)
            drafts.append(draft)
            if len(drafts) >= target_count:
                break

    created: list[dict[str, Any]] = []
    for draft in drafts[:target_count]:
        created.append(
            await manager.async_create_experience(
                title=draft.title,
                origin=ExperienceOrigin.AI.value,
                description=draft.description,
                category=draft.category,
                courage_level=draft.courage_level,
                duration_minutes=draft.duration_minutes,
                cost_level=draft.cost_level,
                travel_minutes=draft.travel_minutes,
                family_friendly=draft.family_friendly,
                indoor_outdoor=draft.indoor_outdoor,
                weather_hint=draft.weather_hint,
                notes=draft.notes,
                location=draft.location,
                extra={
                    "estimated_budget_per_person_eur": draft.budget_per_person_eur,
                },
            )
        )

    manager.last_ai_generation = utc_now_iso()
    _LOGGER.info(
        "Generated %s AI suggestions (requested=%s, dropped_missing_location=%s, "
        "dropped_distance=%s, fallback_without_verified_route=%s)",
        len(created),
        target_count,
        dropped_missing_location,
        dropped_distance,
        fallback_without_verified_route,
    )
    return created
