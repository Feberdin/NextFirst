"""Media preprocessing orchestration.

Purpose:
- Guard and execute optional image transformations before social publishing.

Input/Output:
- Input: options + raw media paths.
- Output: paths to use for posting (original or transformed).

Invariants:
- If preprocessing is disabled, original paths are returned unchanged.
- Missing media paths return early with a safe empty result.

Debugging:
- Verify `social_image_preprocess_enabled` and preprocessing prompt in options.
"""

from __future__ import annotations

from typing import Any

from ..const import (
    CONF_SOCIAL_IMAGE_PREPROCESS_ENABLED,
    CONF_SOCIAL_IMAGE_PREPROCESS_PROMPT,
)
from .base import MediaTransformRequest, MediaTransformResult


async def preprocess_social_media(
    options: dict[str, Any],
    media_paths: list[str],
) -> MediaTransformResult:
    """Return posting-safe media paths according to privacy preprocessing settings."""
    if not media_paths:
        return MediaTransformResult(ok=True, transformed_paths=[], message="No media provided.")

    enabled = bool(options.get(CONF_SOCIAL_IMAGE_PREPROCESS_ENABLED, False))
    if not enabled:
        return MediaTransformResult(
            ok=True,
            transformed_paths=media_paths,
            message="Preprocessing disabled; using original media paths.",
        )

    # Phase-1 placeholder: no external transform provider integrated yet.
    _ = MediaTransformRequest(
        media_paths=media_paths,
        prompt=str(options.get(CONF_SOCIAL_IMAGE_PREPROCESS_PROMPT, "")).strip(),
    )
    return MediaTransformResult(
        ok=False,
        transformed_paths=media_paths,
        message=(
            "Image preprocessing provider is not implemented yet. "
            "Roadmap: add AI image transform adapter and safe local cache path."
        ),
    )
