"""NextFirst HTTP API views for panel UI.

Purpose:
- Provide authenticated REST-like endpoints for the custom sidebar panel.

Input/Output:
- Input: JSON requests from the in-HA NextFirst panel.
- Output: JSON payloads with list data, mutation results, and clear errors.

Invariants:
- Endpoints always require Home Assistant authentication.
- User input is validated before manager operations are called.

Debugging:
- Use browser devtools network tab on `/api/nextfirst/...` and HA logs together.
"""

from __future__ import annotations

import base64
from pathlib import Path
from uuid import uuid4
from typing import Any

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .ai.service import build_prompt_preview, generate_and_store_suggestions
from .const import CONF_DEBUG_ENABLED, DEFAULT_OPTIONS, DOMAIN
from .errors import NextFirstError
from .manager import NextFirstManager
from .monthly_summary import build_monthly_summary


def _build_share_urls(text: str, share_url: str | None = None) -> dict[str, str]:
    """Create provider URLs for manual one-click social sharing from the UI."""
    from urllib.parse import quote_plus

    encoded = quote_plus(text)
    encoded_url = quote_plus(share_url or "")
    return {
        "x": f"https://twitter.com/intent/tweet?text={encoded}{f'&url={encoded_url}' if share_url else ''}",
        "facebook": (
            f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}"
            if share_url
            else "https://www.facebook.com/sharer/sharer.php"
        ),
        "whatsapp": f"https://api.whatsapp.com/send?text={encoded}{f'%20{encoded_url}' if share_url else ''}",
        "telegram": f"https://t.me/share/url?text={encoded}{f'&url={encoded_url}' if share_url else ''}",
        # Instagram does not support prefilled text via web intent.
        "instagram": "https://www.instagram.com/",
    }


def _get_runtime(hass: HomeAssistant) -> dict[str, Any]:
    domain_data = hass.data.get(DOMAIN, {})
    if not domain_data:
        raise web.HTTPInternalServerError(text="NextFirst runtime not initialized")
    # Single-instance integration: first entry is the active runtime.
    return next(iter(domain_data.values()))


def _get_manager(hass: HomeAssistant) -> NextFirstManager:
    runtime = _get_runtime(hass)
    return runtime["manager"]


def _get_options(hass: HomeAssistant) -> dict[str, Any]:
    runtime = _get_runtime(hass)
    entry = runtime["entry"]
    merged = dict(DEFAULT_OPTIONS)
    merged.update(entry.data)
    merged.update(entry.options)
    return merged


class NextFirstBaseView(HomeAssistantView):
    """Shared helpers for NextFirst API views."""

    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    @staticmethod
    async def _json_body(request: web.Request) -> dict[str, Any]:
        try:
            data = await request.json()
            return dict(data or {})
        except ValueError:
            return {}

    async def _error(self, err: Exception) -> web.Response:
        try:
            manager = _get_manager(self.hass)
            await manager.async_record_protocol_event(
                level="error",
                action="api_error",
                message=str(err),
            )
        except Exception:
            pass
        if isinstance(err, NextFirstError):
            return web.json_response({"ok": False, "error": str(err)}, status=400)
        return web.json_response({"ok": False, "error": f"Unexpected error: {err}"}, status=500)


class NextFirstExperiencesView(NextFirstBaseView):
    """List all experiences and create new entries."""

    url = "/api/nextfirst/experiences"
    name = "api:nextfirst:experiences"

    async def get(self, request: web.Request) -> web.Response:
        manager = _get_manager(self.hass)
        options = _get_options(self.hass)
        return web.json_response(
            {
                "ok": True,
                "items": manager.list_all(),
                "stats": manager.get_statistics(),
                "debug_enabled": bool(options.get(CONF_DEBUG_ENABLED, False)),
            }
        )

    async def post(self, request: web.Request) -> web.Response:
        manager = _get_manager(self.hass)
        body = await self._json_body(request)
        try:
            created = await manager.async_create_experience(
                title=str(body.get("title", "")),
                description=body.get("description"),
                category=body.get("category"),
                courage_level=body.get("courage_level"),
                travel_minutes=body.get("travel_minutes"),
                budget_per_person_eur=body.get("budget_per_person_eur"),
                duration_minutes=body.get("duration_minutes"),
                notes=body.get("notes"),
                location=body.get("location"),
                offer_url=body.get("offer_url"),
            )
            return web.json_response({"ok": True, "item": created})
        except Exception as err:
            return await self._error(err)


class NextFirstExperienceDetailView(NextFirstBaseView):
    """Update and delete one experience by ID."""

    url = "/api/nextfirst/experiences/{experience_id}"
    name = "api:nextfirst:experience_detail"

    async def patch(self, request: web.Request, experience_id: str) -> web.Response:
        manager = _get_manager(self.hass)
        body = await self._json_body(request)
        try:
            updated = await manager.async_update_experience(experience_id, body)
            return web.json_response({"ok": True, "item": updated})
        except Exception as err:
            return await self._error(err)

    async def delete(self, request: web.Request, experience_id: str) -> web.Response:
        manager = _get_manager(self.hass)
        try:
            await manager.async_delete_experience(experience_id)
            return web.json_response({"ok": True})
        except Exception as err:
            return await self._error(err)


class NextFirstActionView(NextFirstBaseView):
    """Apply status-changing and enrichment actions for one experience."""

    url = "/api/nextfirst/experiences/{experience_id}/{action}"
    name = "api:nextfirst:experience_action"

    async def post(self, request: web.Request, experience_id: str, action: str) -> web.Response:
        manager = _get_manager(self.hass)
        body = await self._json_body(request)

        try:
            if action == "skip":
                item = await manager.async_mark_skipped(experience_id)
            elif action == "reactivate":
                item = await manager.async_reactivate_experience(experience_id)
            elif action == "experience":
                item = await manager.async_mark_experienced(
                    experience_id,
                    note=body.get("note"),
                    rating=body.get("rating"),
                    would_repeat=body.get("would_repeat"),
                    location=body.get("location"),
                )
            elif action == "archive":
                item = await manager.async_archive_experience(experience_id)
            elif action == "note":
                item = await manager.async_add_note(experience_id, str(body.get("note", "")))
            elif action == "media":
                item = await manager.async_attach_media(
                    experience_id=experience_id,
                    path=str(body.get("path", "")),
                    thumbnail_path=body.get("thumbnail_path"),
                    captured_at=body.get("captured_at"),
                    metadata=body.get("metadata") if isinstance(body.get("metadata"), dict) else {},
                )
            else:
                return web.json_response(
                    {
                        "ok": False,
                        "error": f"Unsupported action '{action}'.",
                    },
                    status=404,
                )

            return web.json_response({"ok": True, "item": item})
        except Exception as err:
            return await self._error(err)


class NextFirstAIGenerateView(NextFirstBaseView):
    """Generate AI suggestions and persist them as open entries."""

    url = "/api/nextfirst/ai/generate"
    name = "api:nextfirst:ai_generate"

    async def post(self, request: web.Request) -> web.Response:
        manager = _get_manager(self.hass)
        session = aiohttp_client.async_get_clientsession(self.hass)

        try:
            created = await generate_and_store_suggestions(
                manager=manager,
                session=session,
                options=_get_options(self.hass),
                count_override=1,
            )
            return web.json_response({"ok": True, "created": created, "count": len(created)})
        except Exception as err:
            return await self._error(err)


class NextFirstAIPromptPreviewView(NextFirstBaseView):
    """Return AI prompt preview for debugging before generation."""

    url = "/api/nextfirst/ai/prompt_preview"
    name = "api:nextfirst:ai_prompt_preview"

    async def get(self, request: web.Request) -> web.Response:
        try:
            options = _get_options(self.hass)
            preview = build_prompt_preview(options)
            return web.json_response({"ok": True, "preview": preview})
        except Exception as err:
            return await self._error(err)


class NextFirstMediaUploadView(NextFirstBaseView):
    """Upload one media file and attach it to an experience."""

    url = "/api/nextfirst/experiences/{experience_id}/media/upload"
    name = "api:nextfirst:media_upload"

    async def post(self, request: web.Request, experience_id: str) -> web.Response:
        manager = _get_manager(self.hass)
        try:
            reader = await request.multipart()
            field = await reader.next()
            if field is None or field.name != "file":
                raise web.HTTPBadRequest(text="Missing multipart field 'file'.")

            filename = str(getattr(field, "filename", "") or "upload.jpg")
            suffix = Path(filename).suffix.lower() or ".jpg"
            target_dir = Path(self.hass.config.path("www", "nextfirst_uploads"))
            target_dir.mkdir(parents=True, exist_ok=True)
            stored_name = f"{uuid4()}{suffix}"
            target_file = target_dir / stored_name

            with target_file.open("wb") as handle:
                while True:
                    chunk = await field.read_chunk()
                    if not chunk:
                        break
                    handle.write(chunk)

            public_path = f"/local/nextfirst_uploads/{stored_name}"
            media = await manager.async_attach_media(
                experience_id=experience_id,
                path=public_path,
                metadata={"original_filename": filename},
            )
            return web.json_response({"ok": True, "media": media})
        except Exception as err:
            return await self._error(err)


class NextFirstMediaUploadJsonView(NextFirstBaseView):
    """Upload one media file via JSON payload (base64 content)."""

    url = "/api/nextfirst/experiences/{experience_id}/media/upload_json"
    name = "api:nextfirst:media_upload_json"

    async def post(self, request: web.Request, experience_id: str) -> web.Response:
        manager = _get_manager(self.hass)
        body = await self._json_body(request)
        try:
            filename = str(body.get("filename") or "upload.jpg")
            content_b64 = str(body.get("content_base64") or "")
            if not content_b64:
                return web.json_response({"ok": False, "error": "content_base64 is required."}, status=400)

            suffix = Path(filename).suffix.lower() or ".jpg"
            target_dir = Path(self.hass.config.path("www", "nextfirst_uploads"))
            target_dir.mkdir(parents=True, exist_ok=True)
            stored_name = f"{uuid4()}{suffix}"
            target_file = target_dir / stored_name

            binary = base64.b64decode(content_b64.encode("ascii"), validate=False)
            target_file.write_bytes(binary)

            public_path = f"/local/nextfirst_uploads/{stored_name}"
            media = await manager.async_attach_media(
                experience_id=experience_id,
                path=public_path,
                metadata={"original_filename": filename, "upload_mode": "json_base64"},
            )
            return web.json_response({"ok": True, "media": media})
        except Exception as err:
            return await self._error(err)


class NextFirstMonthlySummaryPreviewView(NextFirstBaseView):
    """Return monthly summary preview payload for UI and automations."""

    url = "/api/nextfirst/monthly_summary/preview"
    name = "api:nextfirst:monthly_summary_preview"

    async def get(self, request: web.Request) -> web.Response:
        manager = _get_manager(self.hass)
        month = request.query.get("month") or __import__("datetime").datetime.utcnow().strftime("%Y-%m")
        try:
            summary = build_monthly_summary(manager.list_all(), str(month))
            return web.json_response({"ok": True, "summary": summary})
        except Exception as err:
            return await self._error(err)


class NextFirstShareExperienceView(NextFirstBaseView):
    """Create manual share URLs for one experience."""

    url = "/api/nextfirst/share/experience/{experience_id}"
    name = "api:nextfirst:share_experience"

    async def post(self, request: web.Request, experience_id: str) -> web.Response:
        manager = _get_manager(self.hass)
        body = await self._json_body(request)
        entry = next((item for item in manager.list_all() if item.get("id") == experience_id), None)
        if entry is None:
            return web.json_response({"ok": False, "error": "Experience not found."}, status=404)

        text = str(body.get("text") or f"Neues NextFirst Erlebnis: {entry.get('title', 'Unbenannt')}")
        hashtags = [f"#{t.strip().lstrip('#')}" for t in str(body.get("hashtags", "")).split(",") if t.strip()]
        full_text = f"{text}\n\n{' '.join(hashtags)}".strip()
        try:
            event = await manager.async_record_share_event(
                source_type="experience",
                source_id=experience_id,
                provider="local_share",
                ok=True,
                message="Share URLs generated for manual posting.",
            )
            return web.json_response(
                {
                    "ok": True,
                    "share_urls": _build_share_urls(full_text, share_url=str(request.url.origin())),
                    "text": full_text,
                    "event": event,
                }
            )
        except Exception as err:
            return await self._error(err)


class NextFirstShareMonthlyView(NextFirstBaseView):
    """Create manual share URLs for monthly summary."""

    url = "/api/nextfirst/share/monthly"
    name = "api:nextfirst:share_monthly"

    async def post(self, request: web.Request) -> web.Response:
        manager = _get_manager(self.hass)
        body = await self._json_body(request)
        month = str(body.get("month") or __import__("datetime").datetime.utcnow().strftime("%Y-%m"))
        summary = build_monthly_summary(manager.list_all(), month)
        text = str(body.get("text") or summary["summary_text"])
        hashtags = [f"#{t.strip().lstrip('#')}" for t in str(body.get("hashtags", "")).split(",") if t.strip()]
        full_text = f"{text}\n\n{' '.join(hashtags)}".strip()
        try:
            event = await manager.async_record_share_event(
                source_type="monthly_summary",
                source_id=month,
                provider="local_share",
                ok=True,
                message="Share URLs generated for manual posting.",
            )
            return web.json_response(
                {
                    "ok": True,
                    "share_urls": _build_share_urls(full_text, share_url=str(request.url.origin())),
                    "text": full_text,
                    "event": event,
                }
            )
        except Exception as err:
            return await self._error(err)


class NextFirstShareHistoryView(NextFirstBaseView):
    """Return social share history for UI timeline/debugging."""

    url = "/api/nextfirst/share/history"
    name = "api:nextfirst:share_history"

    async def get(self, request: web.Request) -> web.Response:
        manager = _get_manager(self.hass)
        try:
            limit = int(request.query.get("limit", "50"))
            return web.json_response({"ok": True, "history": manager.get_share_history(limit=limit)})
        except Exception as err:
            return await self._error(err)


class NextFirstProtocolHistoryView(NextFirstBaseView):
    """Return NextFirst-only protocol events."""

    url = "/api/nextfirst/protocol"
    name = "api:nextfirst:protocol"

    async def get(self, request: web.Request) -> web.Response:
        manager = _get_manager(self.hass)
        try:
            limit = int(request.query.get("limit", "200"))
            return web.json_response({"ok": True, "history": manager.get_protocol_history(limit=limit)})
        except Exception as err:
            return await self._error(err)


async def async_register_http_api(hass: HomeAssistant) -> None:
    """Register all HTTP views for the NextFirst panel."""
    # Idempotent registration avoids reload crashes when routes already exist.
    for view in (
        NextFirstExperiencesView(hass),
        NextFirstExperienceDetailView(hass),
        NextFirstActionView(hass),
        NextFirstAIGenerateView(hass),
        NextFirstAIPromptPreviewView(hass),
        NextFirstMediaUploadView(hass),
        NextFirstMediaUploadJsonView(hass),
        NextFirstMonthlySummaryPreviewView(hass),
        NextFirstShareExperienceView(hass),
        NextFirstShareMonthlyView(hass),
        NextFirstShareHistoryView(hass),
        NextFirstProtocolHistoryView(hass),
    ):
        try:
            hass.http.register_view(view)
        except Exception:
            continue
