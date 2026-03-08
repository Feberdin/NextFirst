"""Social sharing orchestration.

Purpose:
- Validate social-sharing configuration and execute posting workflow.

Input/Output:
- Input: options + prepared social post request.
- Output: normalized posting result dict.

Invariants:
- Sharing is blocked unless explicit opt-in (`social_enabled`) is true.
- Unknown providers fail fast with actionable messages.

Debugging:
- Inspect options snapshot to verify provider and privacy settings.
"""

from __future__ import annotations

from typing import Any

from ..const import (
    CONF_SOCIAL_ENABLED,
    CONF_SOCIAL_PROVIDER,
)
from ..errors import ValidationError
from .base import SocialPostRequest, SocialPostResult


async def post_to_social(options: dict[str, Any], request: SocialPostRequest) -> SocialPostResult:
    """Post content to configured social provider.

    Current phase intentionally returns explicit setup guidance.
    """
    if not bool(options.get(CONF_SOCIAL_ENABLED, False)):
        raise ValidationError(
            "Social sharing is disabled. Fix: enable social sharing in NextFirst options."
        )

    provider = str(options.get(CONF_SOCIAL_PROVIDER, "none")).strip().lower()
    if provider in {"", "none"}:
        raise ValidationError(
            "No social provider configured. Fix: set a social_provider in options."
        )

    # Phase-1 placeholder. Provider adapters (x/facebook/instagram/etc.) follow in next step.
    return SocialPostResult(
        ok=False,
        provider_name=provider,
        external_post_id=None,
        message=(
            f"Provider '{provider}' is not implemented yet. "
            "Roadmap: add provider adapter and API credentials."
        ),
    )
