"""NextFirst constants.

Purpose:
- Central place for integration-wide constants.

Input/Output:
- Input: imported by integration modules.
- Output: shared constant values.

Invariants:
- DOMAIN is always `nextfirst`.
- STORAGE schema version increments only on breaking data changes.

Debugging:
- Check this file first when entity IDs, service names, or storage keys mismatch.
"""

from __future__ import annotations

DOMAIN = "nextfirst"
PLATFORMS: list[str] = ["sensor", "button"]

STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1

CONF_AI_ENABLED = "ai_enabled"
CONF_AI_PROVIDER = "ai_provider"
CONF_AI_MODEL = "ai_model"
CONF_AI_SUGGESTION_COUNT = "ai_suggestion_count"
CONF_AI_TEMPERATURE = "ai_temperature"
CONF_AI_MAX_TOKENS = "ai_max_tokens"
CONF_AI_API_KEY = "ai_api_key"
CONF_MAX_TRAVEL_MINUTES = "max_travel_minutes"
CONF_FAMILY_FRIENDLY_ONLY = "family_friendly_only"
CONF_GOOD_WEATHER_ONLY = "good_weather_only"
CONF_PREFERRED_CATEGORIES = "preferred_categories"
CONF_PREFERRED_COURAGE_LEVELS = "preferred_courage_levels"
CONF_CUSTOM_INTERESTS = "custom_interests"
CONF_EXCLUSIONS = "exclusions"

DEFAULT_OPTIONS = {
    CONF_AI_ENABLED: False,
    CONF_AI_PROVIDER: "openai",
    CONF_AI_MODEL: "gpt-4.1-mini",
    CONF_AI_SUGGESTION_COUNT: 5,
    CONF_AI_TEMPERATURE: 0.7,
    CONF_AI_MAX_TOKENS: 600,
    CONF_AI_API_KEY: "",
    CONF_MAX_TRAVEL_MINUTES: 60,
    CONF_FAMILY_FRIENDLY_ONLY: False,
    CONF_GOOD_WEATHER_ONLY: False,
    CONF_PREFERRED_CATEGORIES: [],
    CONF_PREFERRED_COURAGE_LEVELS: [],
    CONF_CUSTOM_INTERESTS: "",
    CONF_EXCLUSIONS: "",
}

SIGNAL_DATA_CHANGED = f"{DOMAIN}_data_changed"

SERVICE_CREATE_EXPERIENCE = "create_experience"
SERVICE_UPDATE_EXPERIENCE = "update_experience"
SERVICE_DELETE_EXPERIENCE = "delete_experience"
SERVICE_MARK_SKIPPED = "mark_skipped"
SERVICE_REACTIVATE_EXPERIENCE = "reactivate_experience"
SERVICE_MARK_EXPERIENCED = "mark_experienced"
SERVICE_ATTACH_MEDIA = "attach_media"
SERVICE_ADD_NOTE = "add_note"
SERVICE_GENERATE_AI_SUGGESTIONS = "generate_ai_suggestions"
SERVICE_GET_STATISTICS = "get_statistics"
SERVICE_GET_ALBUM = "get_album"
