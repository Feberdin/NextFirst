"""Media preprocessing contracts.

Purpose:
- Define transformation request/response objects for privacy-safe image handling.

Input/Output:
- Input: image references and prompt for transformation intent.
- Output: transformed image references for social posting.

Invariants:
- Original image references remain untouched by default.

Debugging:
- Check prompt and transformed path mapping in returned response.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class MediaTransformRequest:
    """One preprocessing request for one or more image references."""

    media_paths: list[str] = field(default_factory=list)
    prompt: str = ""


@dataclass(slots=True)
class MediaTransformResult:
    """Result of a preprocessing stage."""

    ok: bool
    transformed_paths: list[str] = field(default_factory=list)
    message: str = ""
