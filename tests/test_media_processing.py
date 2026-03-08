"""Tests for social media preprocessing guardrails.

Purpose:
- Validate children-privacy behavior before social posting.

Input/Output:
- Input: options and media paths.
- Output: transformation result with safe media path behavior.

Invariants:
- Active kids mode without preprocessing strips media from share payload.

Debugging:
- Inspect result.ok + transformed_paths + message for each mode.
"""

from __future__ import annotations

import asyncio

from custom_components.nextfirst.media_processing.service import preprocess_social_media


def test_preprocess_disabled_returns_original_paths() -> None:
    result = asyncio.run(
        preprocess_social_media(
            {
                "social_image_preprocess_enabled": False,
                "social_kids_privacy_mode": "none",
            },
            ["/media/a.jpg", "/media/b.jpg"],
        )
    )

    assert result.ok is True
    assert result.transformed_paths == ["/media/a.jpg", "/media/b.jpg"]


def test_kids_mode_without_preprocessing_removes_media_negative() -> None:
    result = asyncio.run(
        preprocess_social_media(
            {
                "social_image_preprocess_enabled": False,
                "social_kids_privacy_mode": "blur_kids",
            },
            ["/media/kids.jpg"],
        )
    )

    assert result.ok is False
    assert result.transformed_paths == []
    assert "Kids privacy mode" in result.message
