"""Anthropic provider interface."""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.error import HTTPError, URLError

from providers.cloud_provider_base import CloudProviderBase
from providers.provider_context import ProviderContext
from providers.provider_types import ProviderRequest, ProviderResponse, ProviderUsage


class AnthropicProvider(CloudProviderBase):
    """Provider contract for Anthropic."""

    api_key_envs = ("ANTHROPIC_API_KEY",)
    default_base_url = "https://api.anthropic.com"
    models_path = "/v1/models"
    chat_path = "/v1/messages"
    supports_embeddings = False
    supports_json_mode = False
    supports_vision = True
    supports_coding = True
    supports_streaming = True

    def _auth_headers(self) -> dict[str, str]:
        key = self._api_key()
        if not key:
            return {}
        return {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    def _chat_payload(self, request: ProviderRequest, model: str) -> dict[str, Any]:
        payload = super()._chat_payload(request, model)
        messages = payload.pop("messages", [])
        system_prompt = ""
        if messages and messages[0].get("role") == "system":
            system_prompt = str(messages.pop(0).get("content") or "")
        if messages and messages[0].get("role") == "system" and not system_prompt:
            system_prompt = str(messages.pop(0).get("content") or "")
        anthropic_messages = [
            {"role": "user" if message["role"] == "user" else "assistant", "content": message["content"]}
            for message in messages
            if message.get("role") in {"user", "assistant"}
        ]
        anthropic: dict[str, Any] = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": request.max_output_tokens or 1024,
            "stream": bool(request.streaming),
        }
        if system_prompt:
            anthropic["system"] = system_prompt
        if request.temperature is not None:
            anthropic["temperature"] = request.temperature
        if request.stop_conditions:
            anthropic["stop_sequences"] = list(request.stop_conditions)
        return anthropic

    def _normalize_chat_response(self, raw: dict[str, Any]) -> tuple[str, ProviderUsage, str | None]:
        if "error" in raw:
            raise RuntimeError(str(raw["error"]))
        content = ""
        if isinstance(raw.get("content"), list):
            content = "".join(
                str(part.get("text", ""))
                for part in raw["content"]
                if isinstance(part, dict)
            ).strip()
        usage_raw = raw.get("usage") or {}
        usage = ProviderUsage(
            prompt_tokens=int(usage_raw.get("input_tokens") or usage_raw.get("prompt_tokens") or 0),
            completion_tokens=int(usage_raw.get("output_tokens") or usage_raw.get("completion_tokens") or 0),
            total_tokens=int(usage_raw.get("total_tokens") or 0),
        )
        finish_reason = raw.get("stop_reason") or raw.get("finish_reason")
        return content, usage, str(finish_reason) if finish_reason is not None else None
