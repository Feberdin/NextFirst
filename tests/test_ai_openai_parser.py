"""Tests for OpenAI response parsing robustness.

Purpose:
- Validate that NextFirst accepts real-world response shapes from OpenAI.

Input/Output:
- Input: raw JSON-ish message content variants.
- Output: normalized list of suggestion items.
"""

from custom_components.nextfirst.ai.providers.openai import _extract_items, _parse_content_json


def test_parse_accepts_activities_wrapper() -> None:
    parsed = _parse_content_json('{"activities":[{"title":"Spaziergang"}]}')
    items = _extract_items(parsed)
    assert len(items) == 1
    assert items[0]["title"] == "Spaziergang"


def test_parse_accepts_single_object() -> None:
    parsed = _parse_content_json('{"title":"Picknick"}')
    items = _extract_items(parsed)
    assert len(items) == 1
    assert items[0]["title"] == "Picknick"


def test_parse_accepts_markdown_json_block() -> None:
    parsed = _parse_content_json('```json\n[{"title":"Museum"}]\n```')
    items = _extract_items(parsed)
    assert len(items) == 1
    assert items[0]["title"] == "Museum"
