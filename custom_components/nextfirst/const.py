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
CONF_BUDGET_PER_PERSON_EUR = "budget_per_person_eur"
CONF_AI_TEMPERATURE = "ai_temperature"
CONF_AI_MAX_TOKENS = "ai_max_tokens"
CONF_AI_API_KEY = "ai_api_key"
CONF_MAX_TRAVEL_MINUTES = "max_travel_minutes"
CONF_TRAVEL_ORIGIN = "travel_origin"
CONF_FAMILY_FRIENDLY_ONLY = "family_friendly_only"
CONF_GOOD_WEATHER_ONLY = "good_weather_only"
CONF_PREFERRED_CATEGORIES = "preferred_categories"
CONF_PREFERRED_COURAGE_LEVELS = "preferred_courage_levels"
CONF_CUSTOM_INTERESTS = "custom_interests"
CONF_EXCLUSIONS = "exclusions"
CONF_SOCIAL_ENABLED = "social_enabled"
CONF_SOCIAL_PROVIDER = "social_provider"
CONF_SOCIAL_WEBHOOK_URL = "social_webhook_url"
CONF_SOCIAL_MASTODON_BASE_URL = "social_mastodon_base_url"
CONF_SOCIAL_MASTODON_ACCESS_TOKEN = "social_mastodon_access_token"
CONF_SOCIAL_BLUESKY_HANDLE = "social_bluesky_handle"
CONF_SOCIAL_BLUESKY_APP_PASSWORD = "social_bluesky_app_password"
CONF_SOCIAL_AUTO_SHARE_MONTHLY = "social_auto_share_monthly"
CONF_SOCIAL_DEFAULT_HASHTAGS = "social_default_hashtags"
CONF_SOCIAL_INCLUDE_AI_TEXT = "social_include_ai_text"
CONF_SOCIAL_KIDS_PRIVACY_MODE = "social_kids_privacy_mode"
CONF_SOCIAL_IMAGE_PREPROCESS_ENABLED = "social_image_preprocess_enabled"
CONF_SOCIAL_IMAGE_PREPROCESS_PROMPT = "social_image_preprocess_prompt"
CONF_MONTHLY_SUMMARY_ENABLED = "monthly_summary_enabled"
CONF_MONTHLY_SUMMARY_DAY = "monthly_summary_day"
CONF_MONTHLY_SUMMARY_HOUR = "monthly_summary_hour"
CONF_DEBUG_ENABLED = "debug_enabled"

DEFAULT_OPTIONS = {
    CONF_AI_ENABLED: False,
    CONF_AI_PROVIDER: "openai",
    CONF_AI_MODEL: "gpt-4.1-mini",
    CONF_AI_SUGGESTION_COUNT: 2,
    CONF_BUDGET_PER_PERSON_EUR: 50,
    CONF_AI_TEMPERATURE: 0.7,
    CONF_AI_MAX_TOKENS: 600,
    CONF_AI_API_KEY: "",
    CONF_MAX_TRAVEL_MINUTES: 60,
    CONF_TRAVEL_ORIGIN: "zone.home",
    CONF_FAMILY_FRIENDLY_ONLY: False,
    CONF_GOOD_WEATHER_ONLY: False,
    CONF_PREFERRED_CATEGORIES: ["Natur", "Ausflug", "Kreativ"],
    CONF_PREFERRED_COURAGE_LEVELS: ["leicht", "mittel"],
    CONF_CUSTOM_INTERESTS: "Familie, Natur, Ausfluege, Kreativitaet",
    CONF_EXCLUSIONS: "",
    CONF_SOCIAL_ENABLED: False,
    CONF_SOCIAL_PROVIDER: "none",
    CONF_SOCIAL_WEBHOOK_URL: "",
    CONF_SOCIAL_MASTODON_BASE_URL: "",
    CONF_SOCIAL_MASTODON_ACCESS_TOKEN: "",
    CONF_SOCIAL_BLUESKY_HANDLE: "",
    CONF_SOCIAL_BLUESKY_APP_PASSWORD: "",
    CONF_SOCIAL_AUTO_SHARE_MONTHLY: False,
    CONF_SOCIAL_DEFAULT_HASHTAGS: "NextFirstHA",
    CONF_SOCIAL_INCLUDE_AI_TEXT: False,
    CONF_SOCIAL_KIDS_PRIVACY_MODE: "none",
    CONF_SOCIAL_IMAGE_PREPROCESS_ENABLED: False,
    CONF_SOCIAL_IMAGE_PREPROCESS_PROMPT: "Mache alle Kinder unkenntlich.",
    CONF_MONTHLY_SUMMARY_ENABLED: False,
    CONF_MONTHLY_SUMMARY_DAY: 1,
    CONF_MONTHLY_SUMMARY_HOUR: 9,
    CONF_DEBUG_ENABLED: False,
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
SERVICE_PREVIEW_MONTHLY_SUMMARY = "preview_monthly_summary"
SERVICE_SHARE_EXPERIENCE = "share_experience"
SERVICE_SHARE_MONTHLY_SUMMARY = "share_monthly_summary"
SERVICE_GET_SHARE_HISTORY = "get_share_history"
