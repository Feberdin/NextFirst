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

        system_prompt = (
            "You generate family-friendly and practical first-time activity ideas. "
            "Return strict JSON array. Each item must include title and may include "
            "description, category, courage_level, duration_minutes, cost_level, "
            "travel_minutes, family_friendly, indoor_outdoor, weather_hint, notes."
        )

        user_prompt = {
            "count": context.suggestion_count,
            "max_travel_minutes": context.max_travel_minutes,
            "family_friendly_only": context.family_friendly_only,
            "good_weather_only": context.good_weather_only,
            "preferred_categories": context.preferred_categories,
            "preferred_courage_levels": context.preferred_courage_levels,
            "custom_interests": context.custom_interests,
            "exclusions": context.exclusions,
            "language": "de",
        }

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
            parsed = json.loads(content)
            if isinstance(parsed, dict) and "suggestions" in parsed:
                items = parsed["suggestions"]
            elif isinstance(parsed, list):
                items = parsed
            else:
                raise ValueError("Unsupported JSON shape")
        except Exception as err:
            _LOGGER.debug("Raw AI response: %s", body)
            raise AIProviderError(
                "OpenAI response format invalid. "
                "Fix: reduce prompt complexity or inspect provider logs."
            ) from err

        drafts: list[SuggestionDraft] = []
        for item in items:
            title = str(item.get("title", "")).strip()
            if not title:
                continue
            drafts.append(
                SuggestionDraft(
                    title=title,
                    description=item.get("description"),
                    category=item.get("category"),
                    courage_level=item.get("courage_level"),
                    duration_minutes=item.get("duration_minutes"),
                    cost_level=item.get("cost_level"),
                    travel_minutes=item.get("travel_minutes"),
                    family_friendly=item.get("family_friendly"),
                    indoor_outdoor=item.get("indoor_outdoor"),
                    weather_hint=item.get("weather_hint"),
                    notes=item.get("notes"),
                )
            )

        if not drafts:
            raise AIProviderError(
                "AI returned no usable suggestions. Fix: adjust filters or provider settings."
            )

        return drafts
