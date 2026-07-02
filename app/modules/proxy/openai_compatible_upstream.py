from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Mapping

import aiohttp

from app.core.config.settings import get_settings
from app.core.openai.requests import ResponsesRequest
from app.core.openai_compatible import normalize_openai_compatible_base_url
from app.core.utils.sse import format_sse_event
from app.modules.proxy.schemas import CodexModelsResponse, ModelListItem

logger = logging.getLogger(__name__)

_HOP_BY_HOP_HEADERS = {
    "connection",
    "content-encoding",
    "content-length",
    "host",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


def normalize_openai_compatible_model_prefix(prefix: str | None) -> str | None:
    if prefix is None:
        return None
    stripped = prefix.strip().strip("/")
    return stripped or None


def _openai_compatible_v1_url(base_url: str, path: str) -> str:
    root = normalize_openai_compatible_base_url(base_url)
    return f"{root}/v1/{path.lstrip('/')}"


def namespaced_openai_compatible_model(model: str, model_prefix: str | None = None) -> str:
    stripped = model.strip()
    prefix = normalize_openai_compatible_model_prefix(model_prefix)
    if not prefix or stripped.startswith(f"{prefix}/"):
        return stripped
    return f"{prefix}/{stripped}"


def openai_compatible_upstream_model(model: str | None, model_prefix: str | None = None) -> str | None:
    if not model:
        return None
    upstream = model.strip()
    prefix = normalize_openai_compatible_model_prefix(model_prefix)
    if prefix and upstream.startswith(f"{prefix}/"):
        upstream = upstream.removeprefix(f"{prefix}/")
    return upstream or None


def openai_compatible_display_model(
    upstream_model: str,
    upstream_models: set[str],
    model_prefix: str | None = None,
) -> str | None:
    return namespaced_openai_compatible_model(upstream_model, model_prefix)


async def fetch_openai_compatible_models(
    *,
    api_key: str,
    base_url: str,
    created: int | None = None,
    owned_by: str = "openai-compatible",
) -> list[ModelListItem]:
    timeout = aiohttp.ClientTimeout(total=get_settings().upstream_connect_timeout_seconds)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    url = _openai_compatible_v1_url(base_url, "models")
    try:
        async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status >= 400:
                    logger.warning(
                        "OpenAI-compatible models request failed base_url=%s status=%s",
                        base_url,
                        resp.status,
                    )
                    return []
                payload = await resp.json()
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as exc:
        logger.warning("OpenAI-compatible models request failed base_url=%s error=%s", base_url, exc)
        return []

    payload_models: object
    if isinstance(payload, Mapping):
        payload_models = payload.get("data", payload.get("models", []))
    else:
        payload_models = []
    if not isinstance(payload_models, list):
        return []

    resolved_created = created if created is not None else int(time.time())
    models: list[ModelListItem] = []
    seen: set[str] = set()
    for entry in payload_models:
        item_payload: dict[str, object]
        if isinstance(entry, str):
            model_id = entry.strip()
            item_payload = {"id": model_id}
        elif isinstance(entry, Mapping):
            raw_id = entry.get("id") or entry.get("slug") or entry.get("name")
            model_id = raw_id.strip() if isinstance(raw_id, str) else ""
            item_payload = dict(entry)
            item_payload["id"] = model_id
        else:
            continue
        if not model_id or model_id in seen:
            continue
        seen.add(model_id)
        item_payload.setdefault("object", "model")
        item_payload.setdefault("created", resolved_created)
        item_payload.setdefault("owned_by", owned_by)
        try:
            models.append(ModelListItem.model_validate(item_payload))
        except ValueError:
            logger.warning("Skipping invalid OpenAI-compatible model entry base_url=%s model=%s", base_url, model_id)
    return models


async def fetch_openai_compatible_codex_models(
    *,
    api_key: str,
    base_url: str,
) -> CodexModelsResponse | None:
    timeout = aiohttp.ClientTimeout(total=get_settings().upstream_connect_timeout_seconds)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    url = _openai_compatible_codex_models_url(base_url)
    try:
        async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 404:
                    return None
                if resp.status >= 400:
                    logger.warning(
                        "OpenAI-compatible Codex models request failed base_url=%s status=%s",
                        base_url,
                        resp.status,
                    )
                    return None
                payload = await resp.json()
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as exc:
        logger.warning("OpenAI-compatible Codex models request failed base_url=%s error=%s", base_url, exc)
        return None

    try:
        return CodexModelsResponse.model_validate(payload)
    except ValueError:
        logger.warning("Skipping invalid OpenAI-compatible Codex model catalog base_url=%s", base_url)
        return None


def _openai_compatible_codex_models_url(base_url: str) -> str:
    root = normalize_openai_compatible_base_url(base_url)
    return f"{root}/backend-api/codex/models"


async def stream_openai_compatible_responses(
    *,
    payload: ResponsesRequest,
    headers: Mapping[str, str],
    api_key: str,
    base_url: str,
    model_prefix: str | None = None,
) -> AsyncIterator[str]:
    payload_dict = dict(payload.to_payload())
    payload_dict["model"] = (
        openai_compatible_upstream_model(payload.model, model_prefix=model_prefix) or payload.model
    )
    payload_dict["stream"] = True
    timeout = aiohttp.ClientTimeout(total=get_settings().stream_idle_timeout_seconds)
    request_headers = _openai_compatible_headers(headers, api_key)
    async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
        async with session.post(
            _openai_compatible_v1_url(base_url, "responses"),
            json=payload_dict,
            headers=request_headers,
        ) as resp:
            if resp.status >= 400:
                try:
                    error_payload = await resp.json()
                except Exception:
                    error_text = await resp.text()
                    error_payload = {
                        "error": {
                            "message": error_text or f"OpenAI-compatible upstream returned HTTP {resp.status}",
                            "type": "server_error",
                            "code": "openai_compatible_upstream_error",
                        }
                    }
                yield format_sse_event({"type": "error", "error": error_payload.get("error", error_payload)})
                return
            async for chunk in resp.content:
                if not chunk:
                    continue
                yield chunk.decode("utf-8", errors="replace")


def _openai_compatible_headers(headers: Mapping[str, str], api_key: str) -> dict[str, str]:
    forwarded: dict[str, str] = {}
    for key, value in headers.items():
        lower = key.lower()
        if lower in _HOP_BY_HOP_HEADERS or lower == "authorization" or lower == "host":
            continue
        if lower.startswith("x-codex-lb-"):
            continue
        forwarded[key] = value
    forwarded["Authorization"] = f"Bearer {api_key}"
    forwarded["Accept"] = "text/event-stream"
    forwarded["Content-Type"] = "application/json"
    return forwarded
