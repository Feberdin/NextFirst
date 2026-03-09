"""OpenAI provider implementation for NextFirst suggestions.

Purpose:
- Call OpenAI Chat Completions API and map response into SuggestionDraft list.

Input/Output:
- Input: SuggestionContext and provider options (api_key/model/temperature/max_tokens).
- Output: normalized SuggestionDraft entries.

Invariants:
- Network/API errors raise AIProviderError with actionable context.
- Parser returns only non-empty titles.

Debugging:
- Enable DEBUG logging and inspect provider payload (without secrets).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from aiohttp import ClientError, ClientSession

from ...errors import AIProviderError
from .base import SuggestionContext, SuggestionDraft

_LOGGER = logging.getLogger(__name__)


class OpenAISuggestionProvider:
    """Suggestion provider backed by OpenAI Chat Completions."""

    def __init__(
        self,
        session: ClientSession,
        api_key: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> None:
        self._session = session
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    async def generate(self, context: SuggestionContext) -> list[SuggestionDraft]:
        """Generate drafts and parse strict JSON response.

        Example model response format expected:
        [
          {"title": "Barfuss-Park besuchen", "category": "Natur", "courage_level": "leicht"}
        ]
        """
        if not self._api_key:
            raise AIProviderError(
                "AI API key missing. Fix: set ai_api_key in NextFirst options."
            )

        system_prompt, user_prompt = build_openai_prompt_payload(context)

        payload = {
            "model": self._model,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=True)},
            ],
            "response_format": {"type": "json_object"},
        }

        try:
            async with self._session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=45,
            ) as response:
                body = await response.text()
                if response.status >= 400:
                    raise AIProviderError(
                        f"OpenAI request failed (status={response.status}). "
                        "Fix: verify API key, model name, and internet connectivity."
                    )

        except ClientError as err:
            raise AIProviderError(
                f"OpenAI request failed due to network error: {err}. "
                "Fix: check Home Assistant network access."
            ) from err

        try:
            top = json.loads(body)
            content = top["choices"][0]["message"]["content"]
            parsed = _parse_content_json(content)
            items = _extract_items(parsed)
        except Exception as err:
            _LOGGER.debug("Raw AI response: %s", body)
            raise AIProviderError(
                "OpenAI response format invalid. "
                "Fix: reduce prompt complexity or inspect provider logs."
            ) from err

        drafts: list[SuggestionDraft] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "")).strip()
            if not title:
                continue
            drafts.append(
                SuggestionDraft(
                    title=title,
                    description=item.get("description"),
                    category=item.get("category"),
                    courage_level=_normalize_courage_level(item.get("courage_level")),
                    duration_minutes=item.get("duration_minutes"),
                    cost_level=item.get("cost_level"),
                    travel_minutes=item.get("travel_minutes"),
                    family_friendly=item.get("family_friendly"),
                    indoor_outdoor=item.get("indoor_outdoor"),
                    weather_hint=item.get("weather_hint"),
                    notes=item.get("notes"),
                    location=(
                        item.get("location")
                        or item.get("location_address")
                        or item.get("address")
                        or item.get("place")
                        or item.get("venue")
                        or item.get("ort")
                    ),
                    offer_url=(
                        item.get("offer_url")
                        or item.get("website_url")
                        or item.get("booking_url")
                        or item.get("url")
                    ),
                    budget_per_person_eur=_to_int(item.get("budget_per_person_eur")),
                )
            )

        if not drafts:
            raise AIProviderError(
                "AI returned no usable suggestions. Fix: adjust filters or provider settings."
            )

        return drafts


def build_openai_prompt_payload(context: SuggestionContext) -> tuple[str, dict[str, Any]]:
    """Build system and user prompt payload for generation and debug preview."""
    system_prompt = (
        "You generate family-friendly and practical first-time activity ideas. "
        "Return strict JSON with exactly the requested number of ideas. "
        "Use either a JSON array or object key 'suggestions'. "
        "Each item must include title and a concrete location with a googleable full address. "
        "Each item must include a real website URL where the offer/activity can be found. "
        "Never invent offers, workshops, events, or venue-specific claims. "
        "Only use offers that are plausibly real and have a concrete public URL. "
        "If uncertain, return no suggestion for that item. "
        "Avoid generic ideas without place names. "
        "Prefer nearby places that satisfy max_travel_minutes from travel_origin. "
        "Each item may include "
        "description, category, courage_level, duration_minutes, cost_level, "
        "travel_minutes, family_friendly, indoor_outdoor, weather_hint, notes, "
        "location, location_address, offer_url, website_url, budget_per_person_eur."
    )

    user_prompt = {
        "count": context.suggestion_count,
        "max_travel_minutes": context.max_travel_minutes,
        "travel_origin": context.travel_origin,
        "family_friendly_only": context.family_friendly_only,
        "good_weather_only": context.good_weather_only,
        "budget_per_person_eur": context.budget_per_person_eur,
        "preferred_categories": context.preferred_categories,
        "preferred_courage_levels": context.preferred_courage_levels,
        "custom_interests": context.custom_interests,
        "exclusions": context.exclusions,
        "language": "de",
        "location_format": "name, street, postal_code city, country",
        "offer_url_required": True,
    }
    return system_prompt, user_prompt


def _parse_content_json(content: Any) -> Any:
    """Parse model content into JSON, tolerating markdown fences and whitespace."""
    if isinstance(content, list):
        content = "".join(
            str(part.get("text", ""))
            for part in content
            if isinstance(part, dict)
        )
    text = str(content or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    return json.loads(text)


def _extract_items(parsed: Any) -> list[dict[str, Any]]:
    """Normalize varying provider payload shapes to list-of-item dicts."""
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    if isinstance(parsed, dict):
        for key in ("suggestions", "activities", "items", "results"):
            value = parsed.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if "title" in parsed:
            return [parsed]
    raise ValueError("Unsupported AI JSON shape")


def _normalize_courage_level(value: Any) -> str | None:
    """Map numeric courage values to friendly labels used in NextFirst filters."""
    if value is None:
        return None
    if isinstance(value, int):
        return {1: "leicht", 2: "mittel", 3: "mutig", 4: "verrueckt"}.get(value, str(value))
    raw = str(value).strip().lower()
    if raw in {"leicht", "mittel", "mutig", "verrueckt", "verrückt"}:
        return "verrueckt" if raw == "verrückt" else raw
    return raw or None


def _to_int(value: Any) -> int | None:
    """Convert loosely typed numeric model output to int."""
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None
