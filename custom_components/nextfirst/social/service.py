"""Social sharing orchestration.

Purpose:
- Validate social-sharing configuration and execute provider-specific posting.

Input/Output:
- Input: options + prepared social post request + HTTP session.
- Output: normalized posting result object.

Invariants:
- Sharing is blocked unless explicit opt-in (`social_enabled`) is true.
- Unknown providers fail fast with actionable messages.

Debugging:
- Inspect provider-specific error message and credentials in options.
"""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientSession

from ..const import (
    CONF_SOCIAL_BLUESKY_APP_PASSWORD,
    CONF_SOCIAL_BLUESKY_HANDLE,
    CONF_SOCIAL_ENABLED,
    CONF_SOCIAL_MASTODON_ACCESS_TOKEN,
    CONF_SOCIAL_MASTODON_BASE_URL,
    CONF_SOCIAL_PROVIDER,
    CONF_SOCIAL_WEBHOOK_URL,
)
from ..errors import ValidationError
from .base import SocialPostRequest, SocialPostResult


async def post_to_social(
    options: dict[str, Any],
    request: SocialPostRequest,
    session: ClientSession,
) -> SocialPostResult:
    """Post content to configured social provider."""
    if not bool(options.get(CONF_SOCIAL_ENABLED, False)):
        raise ValidationError(
            "Social sharing is disabled. Fix: enable social sharing in NextFirst options."
        )

    provider = str(options.get(CONF_SOCIAL_PROVIDER, "none")).strip().lower()
    if provider in {"", "none"}:
        raise ValidationError(
            "No social provider configured. Fix: set a social_provider in options."
        )

    if provider == "webhook":
        return await _post_webhook(options, request, session)
    if provider == "mastodon":
        return await _post_mastodon(options, request, session)
    if provider == "bluesky":
        return await _post_bluesky(options, request, session)

    raise ValidationError(
        f"Unsupported social provider '{provider}'. "
        "Supported: none, webhook, mastodon, bluesky."
    )


async def _post_webhook(
    options: dict[str, Any],
    request: SocialPostRequest,
    session: ClientSession,
) -> SocialPostResult:
    url = str(options.get(CONF_SOCIAL_WEBHOOK_URL, "")).strip()
    if not url:
        raise ValidationError(
            "Webhook URL missing. Fix: set social_webhook_url in options."
        )

    payload = {
        "text": request.text,
        "media_paths": request.media_paths,
        "hashtags": request.hashtags,
        "source_type": request.source_type,
        "source_id": request.source_id,
    }

    try:
        async with session.post(url, json=payload, timeout=30) as response:
            body = await response.text()
            if response.status >= 400:
                return SocialPostResult(
                    ok=False,
                    provider_name="webhook",
                    message=f"Webhook failed status={response.status}: {body[:180]}",
                )
            return SocialPostResult(
                ok=True,
                provider_name="webhook",
                message="Webhook accepted payload.",
            )
    except ClientError as err:
        return SocialPostResult(
            ok=False,
            provider_name="webhook",
            message=f"Webhook network error: {err}",
        )


async def _post_mastodon(
    options: dict[str, Any],
    request: SocialPostRequest,
    session: ClientSession,
) -> SocialPostResult:
    base_url = str(options.get(CONF_SOCIAL_MASTODON_BASE_URL, "")).strip().rstrip("/")
    token = str(options.get(CONF_SOCIAL_MASTODON_ACCESS_TOKEN, "")).strip()
    if not base_url or not token:
        raise ValidationError(
            "Mastodon config incomplete. Fix: set social_mastodon_base_url and "
            "social_mastodon_access_token in options."
        )

    hashtags = " ".join(f"#{tag.lstrip('#')}" for tag in request.hashtags)
    media_note = (
        f"\n\nMedienreferenzen: {', '.join(request.media_paths)}"
        if request.media_paths
        else ""
    )
    status_text = f"{request.text}\n\n{hashtags}{media_note}".strip()

    try:
        async with session.post(
            f"{base_url}/api/v1/statuses",
            headers={"Authorization": f"Bearer {token}"},
            data={"status": status_text},
            timeout=30,
        ) as response:
            body = await response.json(content_type=None)
            if response.status >= 400:
                return SocialPostResult(
                    ok=False,
                    provider_name="mastodon",
                    message=f"Mastodon error status={response.status}: {body}",
                )

            return SocialPostResult(
                ok=True,
                provider_name="mastodon",
                external_post_id=str(body.get("id")) if isinstance(body, dict) else None,
                message="Mastodon post created.",
            )
    except ClientError as err:
        return SocialPostResult(
            ok=False,
            provider_name="mastodon",
            message=f"Mastodon network error: {err}",
        )


async def _post_bluesky(
    options: dict[str, Any],
    request: SocialPostRequest,
    session: ClientSession,
) -> SocialPostResult:
    handle = str(options.get(CONF_SOCIAL_BLUESKY_HANDLE, "")).strip()
    app_password = str(options.get(CONF_SOCIAL_BLUESKY_APP_PASSWORD, "")).strip()

    if not handle or not app_password:
        raise ValidationError(
            "Bluesky config incomplete. Fix: set social_bluesky_handle and "
            "social_bluesky_app_password in options."
        )

    base = "https://bsky.social/xrpc"
    hashtags = " ".join(f"#{tag.lstrip('#')}" for tag in request.hashtags)
    media_note = (
        f"\n\nMedienreferenzen: {', '.join(request.media_paths)}"
        if request.media_paths
        else ""
    )
    post_text = f"{request.text}\n\n{hashtags}{media_note}".strip()

    try:
        # 1) Login to get auth token + DID
        async with session.post(
            f"{base}/com.atproto.server.createSession",
            json={"identifier": handle, "password": app_password},
            timeout=30,
        ) as login_resp:
            login = await login_resp.json(content_type=None)
            if login_resp.status >= 400:
                return SocialPostResult(
                    ok=False,
                    provider_name="bluesky",
                    message=f"Bluesky login failed status={login_resp.status}: {login}",
                )

        access_jwt = str(login.get("accessJwt") or "")
        did = str(login.get("did") or "")
        if not access_jwt or not did:
            return SocialPostResult(
                ok=False,
                provider_name="bluesky",
                message="Bluesky login succeeded but missing access token or DID.",
            )

        # 2) Create post record
        async with session.post(
            f"{base}/com.atproto.repo.createRecord",
            headers={"Authorization": f"Bearer {access_jwt}"},
            json={
                "repo": did,
                "collection": "app.bsky.feed.post",
                "record": {
                    "$type": "app.bsky.feed.post",
                    "text": post_text[:300],
                    "createdAt": __import__("datetime").datetime.utcnow().isoformat() + "Z",
                },
            },
            timeout=30,
        ) as post_resp:
            body = await post_resp.json(content_type=None)
            if post_resp.status >= 400:
                return SocialPostResult(
                    ok=False,
                    provider_name="bluesky",
                    message=f"Bluesky post failed status={post_resp.status}: {body}",
                )

            return SocialPostResult(
                ok=True,
                provider_name="bluesky",
                external_post_id=str(body.get("uri")) if isinstance(body, dict) else None,
                message="Bluesky post created.",
            )

    except ClientError as err:
        return SocialPostResult(
            ok=False,
            provider_name="bluesky",
            message=f"Bluesky network error: {err}",
        )
