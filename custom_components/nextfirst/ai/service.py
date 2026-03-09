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
import re
from urllib.parse import urlparse
from typing import Any

from aiohttp import ClientSession

from ..const import (
    CONF_AI_API_KEY,
    CONF_AI_ENABLED,
    CONF_AI_MAX_TOKENS,
    CONF_AI_MODEL,
    CONF_AI_PROVIDER,
    CONF_AI_TEMPERATURE,
    CONF_BUDGET_PER_PERSON_EUR,
    CONF_CUSTOM_INTERESTS,
    CONF_DEBUG_ENABLED,
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
from .providers.openai import OpenAISuggestionProvider, build_openai_prompt_payload

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
) -> tuple[tuple[float, float], str] | None:
    """Resolve a human-readable location to coordinates via Nominatim."""
    query = str(location or "").strip()
    if not query:
        return None
    queries = [query, f"{query}, Deutschland"]
    for candidate in queries:
        try:
            async with session.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": candidate, "format": "jsonv2", "limit": 1},
                headers={"User-Agent": "NextFirst/0.3"},
                timeout=20,
            ) as resp:
                if resp.status >= 400:
                    continue
                payload = await resp.json(content_type=None)
                if not payload:
                    continue
                first = payload[0]
                return ((float(first["lat"]), float(first["lon"])), str(first.get("display_name", "")).strip())
        except Exception:
            continue
    return None


def _looks_like_address(value: str | None) -> bool:
    """Basic heuristic to detect a concrete, googleable address string."""
    text = str(value or "").strip()
    if len(text) < 10:
        return False
    return ("," in text and bool(re.search(r"\d", text))) or bool(re.search(r"\b\d{5}\b", text))


def _normalize_offer_url(url: str | None, title: str, location: str | None) -> str:
    """Return normalized explicit offer URL; no synthetic search fallback allowed."""
    raw = str(url or "").strip()
    if raw and raw.startswith(("http://", "https://")):
        return raw
    if raw and "." in raw and " " not in raw:
        return f"https://{raw}"
    return ""


def _is_blocked_offer_url(url: str) -> bool:
    """Reject generic search/maps URLs that don't identify a concrete offer page."""
    host = (urlparse(url).netloc or "").lower()
    blocked_hosts = {
        "google.com",
        "www.google.com",
        "maps.google.com",
        "duckduckgo.com",
        "www.duckduckgo.com",
        "bing.com",
        "www.bing.com",
    }
    return any(host == blocked or host.endswith(f".{blocked}") for blocked in blocked_hosts)


async def _verify_offer_url(session: ClientSession, url: str) -> bool:
    """Best-effort verification that URL is reachable and looks like a concrete page."""
    if not url or _is_blocked_offer_url(url):
        return False
    headers = {"User-Agent": "NextFirst/0.3"}
    try:
        async with session.get(url, headers=headers, allow_redirects=True, timeout=20) as resp:
            if resp.status >= 400:
                return False
            content_type = str(resp.headers.get("Content-Type", "")).lower()
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                return False
            final_host = (urlparse(str(resp.url)).netloc or "").lower()
            if not final_host:
                return False
            if _is_blocked_offer_url(str(resp.url)):
                return False
            return True
    except Exception:
        return False


def _build_context(options: dict[str, Any], *, suggestion_count: int) -> SuggestionContext:
    """Create normalized suggestion context from options."""
    return SuggestionContext(
        suggestion_count=suggestion_count,
        max_travel_minutes=int(options.get(CONF_MAX_TRAVEL_MINUTES, 60)),
        family_friendly_only=bool(options.get(CONF_FAMILY_FRIENDLY_ONLY, False)),
        good_weather_only=bool(options.get(CONF_GOOD_WEATHER_ONLY, False)),
        budget_per_person_eur=int(options.get(CONF_BUDGET_PER_PERSON_EUR, 0) or 0),
        travel_origin=str(options.get(CONF_TRAVEL_ORIGIN, "") or "").strip(),
        preferred_categories=list(options.get(CONF_PREFERRED_CATEGORIES, [])),
        preferred_courage_levels=list(options.get(CONF_PREFERRED_COURAGE_LEVELS, [])),
        custom_interests=str(options.get(CONF_CUSTOM_INTERESTS, "")),
        exclusions=str(options.get(CONF_EXCLUSIONS, "")),
    )


def build_prompt_preview(options: dict[str, Any]) -> dict[str, Any]:
    """Build human-readable debug preview of the OpenAI prompt payload."""
    provider_name = str(options.get(CONF_AI_PROVIDER, "openai"))
    if provider_name != "openai":
        raise AIProviderError(
            f"Unsupported AI provider '{provider_name}'. Fix: use provider 'openai'."
        )
    context = _build_context(options, suggestion_count=1)
    system_prompt, user_prompt = build_openai_prompt_payload(context)
    return {
        "provider": provider_name,
        "model": str(options.get(CONF_AI_MODEL, "gpt-4.1-mini")),
        "debug_enabled": bool(options.get(CONF_DEBUG_ENABLED, False)),
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
    }


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

    # Product decision: exactly one suggestion per user action.
    target_count = 1
    context = _build_context(options, suggestion_count=target_count)
    if not context.travel_origin or context.travel_origin.lower().startswith("zone."):
        raise ValidationError(
            "Wohnort/Startadresse fehlt. Fix: In NextFirst Optionen eine echte Adresse eintragen "
            "(z. B. Musterstr. 1, 12345 Musterstadt) statt zone.home."
        )
    origin_coords = _resolve_origin_coordinates(manager, context.travel_origin)
    if origin_coords is None and context.travel_origin:
        geocode_origin = await _geocode_location(session, context.travel_origin)
        if geocode_origin is not None:
            origin_coords = geocode_origin[0]

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
    dropped_missing_offer_url = 0
    dropped_unverified_offer_url = 0
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
            # Fallback query with title improves hit rate for generic place names.
            location_query = str(draft.location)
            geocode_result = await _geocode_location(session, f"{draft.title}, {location_query}") or await _geocode_location(session, location_query)
            if geocode_result is not None:
                coords, normalized_address = geocode_result
                if _looks_like_address(normalized_address):
                    draft.location = normalized_address
            elif not _looks_like_address(draft.location):
                dropped_missing_location += 1
                continue
            if origin_coords is not None:
                if geocode_result is not None:
                    coords, normalized_address = geocode_result
                    drive_minutes = await _estimate_drive_minutes(session, origin_coords, coords)
                    if drive_minutes is not None:
                        if drive_minutes > context.max_travel_minutes:
                            dropped_distance += 1
                            continue
                        draft.travel_minutes = drive_minutes
                    if _looks_like_address(normalized_address):
                        draft.location = normalized_address
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
            draft.offer_url = _normalize_offer_url(draft.offer_url, draft.title, draft.location)
            if not draft.offer_url:
                dropped_missing_offer_url += 1
                continue
            if not await _verify_offer_url(session, draft.offer_url):
                dropped_unverified_offer_url += 1
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
                offer_url=draft.offer_url,
                extra={
                    "estimated_budget_per_person_eur": draft.budget_per_person_eur,
                },
            )
        )

    manager.last_ai_generation = utc_now_iso()
    _LOGGER.info(
        "Generated %s AI suggestions (requested=%s, dropped_missing_location=%s, "
        "dropped_missing_offer_url=%s, dropped_unverified_offer_url=%s, dropped_distance=%s, "
        "fallback_without_verified_route=%s, count_override=%s)",
        len(created),
        target_count,
        dropped_missing_location,
        dropped_missing_offer_url,
        dropped_unverified_offer_url,
        dropped_distance,
        fallback_without_verified_route,
        count_override,
    )
    return created
