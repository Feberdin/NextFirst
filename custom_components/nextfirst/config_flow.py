"""Config flow and options flow for NextFirst.

Purpose:
- Provide setup UX in Home Assistant and editable runtime options.

Input/Output:
- Input: user form entries from config/options UI.
- Output: ConfigEntry and updated options dict.

Invariants:
- Single instance by default.
- Safe defaults keep integration usable without AI.

Debugging:
- If options are not applied, inspect entry.options and merged defaults in __init__.py.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_AI_API_KEY,
    CONF_AI_ENABLED,
    CONF_AI_MAX_TOKENS,
    CONF_AI_MODEL,
    CONF_AI_PROVIDER,
    CONF_AI_SUGGESTION_COUNT,
    CONF_AI_TEMPERATURE,
    CONF_CUSTOM_INTERESTS,
    CONF_DEBUG_ENABLED,
    CONF_EXCLUSIONS,
    CONF_FAMILY_FRIENDLY_ONLY,
    CONF_GOOD_WEATHER_ONLY,
    CONF_MAX_TRAVEL_MINUTES,
    CONF_MONTHLY_SUMMARY_DAY,
    CONF_MONTHLY_SUMMARY_ENABLED,
    CONF_MONTHLY_SUMMARY_HOUR,
    CONF_PREFERRED_CATEGORIES,
    CONF_PREFERRED_COURAGE_LEVELS,
    CONF_SOCIAL_AUTO_SHARE_MONTHLY,
    CONF_SOCIAL_BLUESKY_APP_PASSWORD,
    CONF_SOCIAL_BLUESKY_HANDLE,
    CONF_SOCIAL_DEFAULT_HASHTAGS,
    CONF_SOCIAL_ENABLED,
    CONF_SOCIAL_IMAGE_PREPROCESS_ENABLED,
    CONF_SOCIAL_IMAGE_PREPROCESS_PROMPT,
    CONF_SOCIAL_INCLUDE_AI_TEXT,
    CONF_SOCIAL_KIDS_PRIVACY_MODE,
    CONF_SOCIAL_MASTODON_ACCESS_TOKEN,
    CONF_SOCIAL_MASTODON_BASE_URL,
    CONF_SOCIAL_PROVIDER,
    CONF_SOCIAL_WEBHOOK_URL,
    DEFAULT_OPTIONS,
    DOMAIN,
)


class NextFirstConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle setup flow for NextFirst."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Create a single integration instance."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            title = user_input.get("title") or "NextFirst"
            # Keep initial AI settings in config-entry data for first-setup usability.
            return self.async_create_entry(
                title=title,
                data={
                    CONF_AI_ENABLED: bool(user_input.get(CONF_AI_ENABLED, False)),
                    CONF_AI_API_KEY: str(user_input.get(CONF_AI_API_KEY, "")),
                },
            )

        schema = vol.Schema(
            {
                vol.Optional("title", default="NextFirst"): str,
                vol.Optional(CONF_AI_ENABLED, default=False): bool,
                vol.Optional(CONF_AI_API_KEY, default=""): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return NextFirstOptionsFlow(config_entry)


class NextFirstOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for NextFirst runtime settings."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Edit integration options with safe defaults."""
        if user_input is not None:
            normalized = dict(user_input)
            normalized[CONF_PREFERRED_CATEGORIES] = _split_csv(
                str(user_input.get(CONF_PREFERRED_CATEGORIES, ""))
            )
            normalized[CONF_PREFERRED_COURAGE_LEVELS] = _split_csv(
                str(user_input.get(CONF_PREFERRED_COURAGE_LEVELS, ""))
            )
            return self.async_create_entry(title="", data=normalized)

        current = dict(DEFAULT_OPTIONS)
        current.update(self.config_entry.options)

        schema = vol.Schema(
            {
                vol.Optional(CONF_AI_ENABLED, default=current[CONF_AI_ENABLED]): bool,
                vol.Optional(CONF_AI_PROVIDER, default=current[CONF_AI_PROVIDER]): str,
                vol.Optional(CONF_AI_MODEL, default=current[CONF_AI_MODEL]): str,
                vol.Optional(
                    CONF_AI_SUGGESTION_COUNT,
                    default=current[CONF_AI_SUGGESTION_COUNT],
                ): vol.All(int, vol.Range(min=1, max=20)),
                vol.Optional(CONF_AI_TEMPERATURE, default=current[CONF_AI_TEMPERATURE]): vol.All(
                    float, vol.Range(min=0.0, max=2.0)
                ),
                vol.Optional(CONF_AI_MAX_TOKENS, default=current[CONF_AI_MAX_TOKENS]): vol.All(
                    int, vol.Range(min=100, max=4000)
                ),
                vol.Optional(CONF_AI_API_KEY, default=current[CONF_AI_API_KEY]): str,
                vol.Optional(
                    CONF_MAX_TRAVEL_MINUTES,
                    default=current[CONF_MAX_TRAVEL_MINUTES],
                ): vol.All(int, vol.Range(min=0, max=300)),
                vol.Optional(
                    CONF_FAMILY_FRIENDLY_ONLY,
                    default=current[CONF_FAMILY_FRIENDLY_ONLY],
                ): bool,
                vol.Optional(
                    CONF_GOOD_WEATHER_ONLY,
                    default=current[CONF_GOOD_WEATHER_ONLY],
                ): bool,
                vol.Optional(
                    CONF_PREFERRED_CATEGORIES,
                    default=",".join(current[CONF_PREFERRED_CATEGORIES]),
                ): str,
                vol.Optional(
                    CONF_PREFERRED_COURAGE_LEVELS,
                    default=",".join(current[CONF_PREFERRED_COURAGE_LEVELS]),
                ): str,
                vol.Optional(CONF_CUSTOM_INTERESTS, default=current[CONF_CUSTOM_INTERESTS]): str,
                vol.Optional(CONF_EXCLUSIONS, default=current[CONF_EXCLUSIONS]): str,
                vol.Optional(CONF_SOCIAL_ENABLED, default=current[CONF_SOCIAL_ENABLED]): bool,
                vol.Optional(CONF_SOCIAL_PROVIDER, default=current[CONF_SOCIAL_PROVIDER]): vol.In(
                    ["none", "webhook", "mastodon", "bluesky"]
                ),
                vol.Optional(
                    CONF_SOCIAL_AUTO_SHARE_MONTHLY,
                    default=current[CONF_SOCIAL_AUTO_SHARE_MONTHLY],
                ): bool,
                vol.Optional(
                    CONF_SOCIAL_DEFAULT_HASHTAGS,
                    default=current[CONF_SOCIAL_DEFAULT_HASHTAGS],
                ): str,
                vol.Optional(
                    CONF_SOCIAL_INCLUDE_AI_TEXT,
                    default=current[CONF_SOCIAL_INCLUDE_AI_TEXT],
                ): bool,
                vol.Optional(
                    CONF_SOCIAL_KIDS_PRIVACY_MODE,
                    default=current[CONF_SOCIAL_KIDS_PRIVACY_MODE],
                ): vol.In(["none", "blur_kids", "ai_stylize"]),
                vol.Optional(
                    CONF_SOCIAL_IMAGE_PREPROCESS_ENABLED,
                    default=current[CONF_SOCIAL_IMAGE_PREPROCESS_ENABLED],
                ): bool,
                vol.Optional(
                    CONF_SOCIAL_IMAGE_PREPROCESS_PROMPT,
                    default=current[CONF_SOCIAL_IMAGE_PREPROCESS_PROMPT],
                ): str,
                vol.Optional(
                    CONF_MONTHLY_SUMMARY_ENABLED,
                    default=current[CONF_MONTHLY_SUMMARY_ENABLED],
                ): bool,
                vol.Optional(
                    CONF_MONTHLY_SUMMARY_DAY,
                    default=current[CONF_MONTHLY_SUMMARY_DAY],
                ): vol.All(int, vol.Range(min=1, max=28)),
                vol.Optional(
                    CONF_MONTHLY_SUMMARY_HOUR,
                    default=current[CONF_MONTHLY_SUMMARY_HOUR],
                ): vol.All(int, vol.Range(min=0, max=23)),
                vol.Optional(CONF_SOCIAL_WEBHOOK_URL, default=current[CONF_SOCIAL_WEBHOOK_URL]): str,
                vol.Optional(
                    CONF_SOCIAL_MASTODON_BASE_URL,
                    default=current[CONF_SOCIAL_MASTODON_BASE_URL],
                ): str,
                vol.Optional(
                    CONF_SOCIAL_MASTODON_ACCESS_TOKEN,
                    default=current[CONF_SOCIAL_MASTODON_ACCESS_TOKEN],
                ): str,
                vol.Optional(
                    CONF_SOCIAL_BLUESKY_HANDLE,
                    default=current[CONF_SOCIAL_BLUESKY_HANDLE],
                ): str,
                vol.Optional(
                    CONF_SOCIAL_BLUESKY_APP_PASSWORD,
                    default=current[CONF_SOCIAL_BLUESKY_APP_PASSWORD],
                ): str,
                vol.Optional(CONF_DEBUG_ENABLED, default=current[CONF_DEBUG_ENABLED]): bool,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)


def _split_csv(value: str) -> list[str]:
    """Convert comma-separated text to clean list values."""
    return [item.strip() for item in value.split(",") if item.strip()]
