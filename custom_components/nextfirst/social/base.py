"""Provider-neutral social posting contracts.

Purpose:
- Standardize social post requests independent of target platform.

Input/Output:
- Input: SocialPostRequest with text/media metadata.
- Output: SocialPostResult with provider post reference.

Invariants:
- Providers must return deterministic success/failure objects.

Debugging:
- Compare provider_name + external_post_id in result payload.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SocialPostRequest:
    """Internal payload for one social post attempt."""

    text: str
    media_paths: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    source_type: str = "experience"
    source_id: str | None = None


@dataclass(slots=True)
class SocialPostResult:
    """Normalized posting result regardless of provider."""

    ok: bool
    provider_name: str
    external_post_id: str | None = None
    message: str = ""
