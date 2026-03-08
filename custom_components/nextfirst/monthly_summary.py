"""Monthly summary generation for NextFirst.

Purpose:
- Build deterministic monthly summary text from existing experiences.

Input/Output:
- Input: serialized experience list and a target month (YYYY-MM).
- Output: summary dict with metrics and a human-readable German summary text.

Invariants:
- Missing or malformed items are ignored defensively.
- Function is pure and has no side effects.

Debugging:
- Compare `experienced_items` count with expected completed_at timestamps.
"""

from __future__ import annotations

from collections import Counter
from typing import Any


def build_monthly_summary(experiences: list[dict[str, Any]], month_key: str) -> dict[str, Any]:
    """Create a compact monthly summary from experienced entries.

    Example:
    - Input month: `2026-03`
    - Output summary: metric block + text for UI/social preview.
    """
    experienced_items: list[dict[str, Any]] = []

    for item in experiences:
        completed_at = str(item.get("completed_at") or "")
        if not completed_at.startswith(month_key):
            continue

        status = str(item.get("status") or "")
        if status not in {"experienced", "archived"}:
            continue

        experienced_items.append(item)

    total = len(experienced_items)
    categories = Counter(
        str(item.get("category") or "Unkategorisiert") for item in experienced_items
    )
    top_category = categories.most_common(1)[0][0] if categories else "-"

    repeat_yes = sum(1 for item in experienced_items if item.get("would_repeat") is True)
    with_media = sum(1 for item in experienced_items if (item.get("media") or []))

    if total == 0:
        text = (
            f"Monatsrückblick {month_key}: Diesen Monat wurden noch keine "
            "Erlebnisse als 'erlebt' abgeschlossen."
        )
    else:
        text = (
            f"Monatsrückblick {month_key}: {total} neue Erlebnisse abgeschlossen. "
            f"Top-Kategorie: {top_category}. "
            f"{with_media} Einträge mit Bildern. "
            f"{repeat_yes} Aktivitäten würdet ihr wiederholen."
        )

    return {
        "month": month_key,
        "total_experienced": total,
        "top_category": top_category,
        "with_media": with_media,
        "would_repeat_count": repeat_yes,
        "categories": dict(categories),
        "summary_text": text,
    }
