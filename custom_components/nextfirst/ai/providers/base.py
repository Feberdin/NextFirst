"""AI provider interfaces.

Purpose:
- Keep AI integration provider-neutral through a stable internal contract.

Input/Output:
- Input: SuggestionContext with user preferences and optional system context.
- Output: list of SuggestionDraft objects.

Invariants:
- Provider returns parsed drafts, never raw model output.

Debugging:
- If suggestions fail, inspect provider implementation and parser path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(slots=True)
class SuggestionContext:
    """Normalized input for AI suggestion generation."""

    suggestion_count: int
    max_travel_minutes: int
    family_friendly_only: bool
    good_weather_only: bool
    budget_per_person_eur: int = 0
    travel_origin: str = ""
    preferred_categories: list[str] = field(default_factory=list)
    preferred_courage_levels: list[str] = field(default_factory=list)
    custom_interests: str = ""
    exclusions: str = ""


@dataclass(slots=True)
class SuggestionDraft:
    """Provider-agnostic suggestion draft mapped to internal fields."""

    title: str
    description: str | None = None
    category: str | None = None
    courage_level: str | None = None
    duration_minutes: int | None = None
    cost_level: str | None = None
    travel_minutes: int | None = None
    family_friendly: bool | None = None
    indoor_outdoor: str | None = None
    weather_hint: str | None = None
    notes: str | None = None
    location: str | None = None
    offer_url: str | None = None
    budget_per_person_eur: int | None = None


class SuggestionProvider(Protocol):
    """Contract for all AI providers."""

    async def generate(self, context: SuggestionContext) -> list[SuggestionDraft]:
        """Generate suggestion drafts using one provider backend."""
