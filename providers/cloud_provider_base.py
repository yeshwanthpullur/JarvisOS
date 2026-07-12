"""Shared HTTP provider implementation for cloud AI adapters."""

from __future__ import annotations

import base64
import ipaddress
import json
import logging
import re
import time
from dataclasses import replace
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from providers.base_provider import BaseProvider, capabilities_for
from providers.provider_context import ProviderContext
from providers.provider_health import ProviderHealth
from providers.provider_types import (
    CostEstimate,
    ModelInfo,
    ProviderCapability,
    ProviderCapabilities,
    ProviderRequest,
    ProviderResponse,
    ProviderUsage,
    utc_now,
)


class CloudProviderBase(BaseProvider):
    """Base adapter for HTTP cloud providers."""

    api_key_envs: tuple[str, ...] = ()
    default_base_url: str | None = None
    models_path: str | None = "/v1/models"
    chat_path: str = "/v1/chat/completions"
    supports_model_listing: bool = True
    supports_streaming: bool = True
    supports_json_mode: bool = True
    supports_embeddings: bool = False
    supports_vision: bool = False
    supports_function_calling: bool = True
    supports_reasoning: bool = True
    supports_coding: bool = True

    def __init__(self, context: ProviderContext) -> None:
        super().__init__(context, self._capability_envelope())
        self._models: tuple[ModelInfo, ...] = ()
        self._last_checked: str | None = None

    def initialize(self) -> None:
        super().initialize()
        self.refresh_inventory()

    def health_check(self) -> ProviderHealth:
        if not self.enabled:
            self.health.available = False
            self.health.message = "Provider is disabled."
            return self.health
        if not self._api_key():
            self.health.mark_failure("API key is missing.")
            return self.health
        start = time.perf_counter()
        try:
            self.refresh_inventory()
            if self._ping():
                self.health.mark_success((time.perf_counter() - start) * 1000)
            else:
                self.health.mark_failure("Provider endpoint is unreachable.")
        except Exception as exc:  # pragma: no cover - defensive
            self.health.mark_failure(self._safe_error(exc))
        return self.health

    def capabilities(self) -> ProviderCapabilities:
        return replace(self._capabilities, models=self._models)

    def estimate_cost(self, request: ProviderRequest) -> CostEstimate:
        usage = self._estimate_usage(request)
        return CostEstimate(
            amount=round(usage.total_tokens * self._cost_per_token(), 6),
            currency="USD",
            confidence=0.5 if self._cost_per_token() > 0 else 0.0,
        )

    def list_models(self) -> tuple[ModelInfo, ...]:
        self.refresh_inventory()
        return self._models

    def refresh_inventory(self) -> tuple[ModelInfo, ...]:
        models = self._discover_models()
        self._models = models
        self._last_checked = utc_now().isoformat()
        return models

    def chat(self, request: ProviderRequest) -> ProviderResponse:
        return self._execute(request)

    async def execute(self, request: ProviderRequest) -> ProviderResponse:
        return self._execute(request)

    def _execute(self, request: ProviderRequest) -> ProviderResponse:
        start = time.perf_counter()
        if self._api_key_required() and not self._api_key():
            return self._error_response(request, "", "API key is missing.", start)
        model = self._select_model(request)
        if not model:
            return self._error_response(request, "", "No usable cloud models were found.", start)
        if request.model and self._models and request.model not in {item.model_id for item in self._models}:
            return self._error_response(request, request.model, "Model missing: the requested cloud model is not available.", start)
        payload = self._chat_payload(request, model)
        timeout = request.timeout_seconds or self.context.config.timeout_seconds or 30
        try:
            raw = self._request_json(self._chat_url(), payload, timeout=timeout)
            content, usage, finish_reason = self._normalize_chat_response(raw)
            latency = (time.perf_counter() - start) * 1000
            self.metrics.record_request(
                usage.prompt_tokens,
                usage.completion_tokens,
                usage.estimated_cost,
                latency,
            )
            self.health.mark_success(latency)
            return ProviderResponse(
                provider_id=self.provider_id,
                model=model,
                content=content,
                usage=usage,
                metadata={
                    "provider_kind": self.kind.value,
                    "latency_ms": latency,
                    "inventory_checked_at": self._last_checked,
                    "estimated_cost": usage.estimated_cost,
                    "cloud": True,
                },
                request_id=request.request_id,
                finish_reason=finish_reason,
                created_at=utc_now(),
            )
        except Exception as exc:
            return self._error_response(request, model, self._safe_error(exc), start, exc)

    def _capability_envelope(self) -> ProviderCapabilities:
        capabilities: list[ProviderCapability] = [ProviderCapability.CHAT]
        if self.supports_reasoning:
            capabilities.append(ProviderCapability.REASONING)
        if self.supports_coding:
            capabilities.append(ProviderCapability.CODING)
        if self.supports_vision:
            capabilities.append(ProviderCapability.VISION)
        if self.supports_embeddings:
            capabilities.append(ProviderCapability.EMBEDDING)
        if self.supports_function_calling:
            capabilities.append(ProviderCapability.FUNCTION_CALLING)
        if self.supports_streaming:
            capabilities.append(ProviderCapability.STREAMING)
        if self.supports_json_mode:
            capabilities.append(ProviderCapability.JSON_MODE)
        return capabilities_for(tuple(dict.fromkeys(capabilities)))

    def _api_key_required(self) -> bool:
        return bool(self.api_key_envs)

    def _api_key(self) -> str:
        for env_name in self.api_key_envs:
            value = self.context.config.metadata.get(env_name)
            if value:
                return str(value)
            from os import getenv

            value = getenv(env_name)
            if value:
                return value
        return ""

    def _base_url(self) -> str:
        base_url = (self.context.config.base_url or self.default_base_url or "").rstrip("/")
        if not base_url:
            raise ValueError("Provider base URL is not configured.")
        if not self._is_local_url(base_url) and self.context.config.local_only:
            raise ValueError("Provider locality could not be verified.")
        return base_url

    def _is_local_url(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        host = parsed.hostname or ""
        if host in {"localhost", "127.0.0.1", "::1"}:
            return True
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            return False
        return ip.is_loopback or ip.is_private

    def _auth_headers(self) -> dict[str, str]:
        key = self._api_key()
        if not key:
            return {}
        return {"Authorization": f"Bearer {key}"}

    def _request_json(self, url: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(url, data=body, method="POST" if body is not None else "GET")
        request.add_header("Content-Type", "application/json")
        for header, value in self._auth_headers().items():
            request.add_header(header, value)
        with urlopen(request, timeout=timeout) as response:
            data = response.read().decode("utf-8")
        return json.loads(data) if data else {}

    def _request_stream(self, url: str, payload: dict[str, Any], timeout: int = 30) -> str:
        body = json.dumps(payload).encode("utf-8")
        request = Request(url, data=body, method="POST")
        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "text/event-stream")
        for header, value in self._auth_headers().items():
            request.add_header(header, value)
        with urlopen(request, timeout=timeout) as response:
            content = response.read().decode("utf-8", errors="replace")
        return content

    def _chat_url(self) -> str:
        return f"{self._base_url()}{self.chat_path}"

    def _models_url(self) -> str:
        if self.models_path is None:
            raise LookupError("Model listing is not supported.")
        return f"{self._base_url()}{self.models_path}"

    def _discover_models(self) -> tuple[ModelInfo, ...]:
        if not self.supports_model_listing or self.models_path is None:
            return self._configured_models()
        try:
            raw = self._request_json(self._models_url(), timeout=self.context.config.timeout_seconds or 30)
        except Exception:
            return self._configured_models()
        models = self._parse_model_list(raw)
        return tuple(models or self._configured_models())

    def _configured_models(self) -> tuple[ModelInfo, ...]:
        models = self.context.config.models
        if models:
            return models
        preferred = self.context.config.preferred_model or self.context.config.default_model or self.context.config.fallback_model
        if preferred:
            return (
                ModelInfo(
                    model_id=preferred,
                    display_name=preferred,
                    capabilities=tuple(self.capabilities().capabilities),
                    metadata={"source": "configuration"},
                ),
            )
        return ()

    def _parse_model_list(self, raw: dict[str, Any]) -> list[ModelInfo]:
        data = raw.get("data") or raw.get("models") or []
        models: list[ModelInfo] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            model_id = str(item.get("id") or item.get("name") or item.get("model") or "").strip()
            if not model_id:
                continue
            models.append(
                ModelInfo(
                    model_id=model_id,
                    display_name=str(item.get("name") or model_id),
                    capabilities=self._model_capabilities(item),
                    context_window=int(item.get("context_window") or item.get("context_length") or item.get("max_context") or 0),
                    max_tokens=int(item.get("max_tokens") or item.get("output_tokens") or 0),
                    metadata={"source": self.kind.value, "raw": item},
                )
            )
        return models

    def _model_capabilities(self, item: dict[str, Any]) -> tuple[ProviderCapability, ...]:
        capabilities = [ProviderCapability.CHAT]
        if self.supports_reasoning:
            capabilities.append(ProviderCapability.REASONING)
        if self.supports_coding:
            capabilities.append(ProviderCapability.CODING)
        if self.supports_vision and item.get("vision", True):
            capabilities.append(ProviderCapability.VISION)
        if self.supports_embeddings and item.get("embedding", True):
            capabilities.append(ProviderCapability.EMBEDDING)
        if self.supports_function_calling and item.get("function_calling", True):
            capabilities.append(ProviderCapability.FUNCTION_CALLING)
        if self.supports_streaming and item.get("streaming", True):
            capabilities.append(ProviderCapability.STREAMING)
        if self.supports_json_mode and item.get("json_mode", True):
            capabilities.append(ProviderCapability.JSON_MODE)
        return tuple(dict.fromkeys(capabilities))

    def _select_model(self, request: ProviderRequest) -> str:
        model = request.model or self.context.config.preferred_model or self.context.config.default_model or self.context.config.fallback_model
        if model:
            return model
        models = self.list_models()
        return models[0].model_id if models else ""

    def _chat_payload(self, request: ProviderRequest, model: str) -> dict[str, Any]:
        messages = []
        if request.system_instructions:
            messages.append({"role": "system", "content": request.system_instructions})
        context_lines = self._selected_context_lines(request)
        if context_lines:
            messages.append({"role": "system", "content": "\n".join(context_lines)})
        messages.append({"role": "user", "content": request.prompt})
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": bool(request.streaming),
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_output_tokens is not None:
            payload["max_tokens"] = request.max_output_tokens
        if request.stop_conditions:
            payload["stop"] = list(request.stop_conditions)
        if request.response_schema is not None:
            payload["response_format"] = {"type": "json_object"}
        return payload

    def _selected_context_lines(self, request: ProviderRequest) -> tuple[str, ...]:
        context = request.selected_context or {}
        lines: list[str] = []
        for key in ("objective", "goal", "context", "summary"):
            value = context.get(key)
            if value:
                lines.append(f"{key}: {value}")
        for evidence in request.retrieved_evidence:
            lines.append(f"evidence: {evidence}")
        if request.local_only:
            lines.append("policy: local-only")
        return tuple(lines)

    def _normalize_chat_response(self, raw: dict[str, Any]) -> tuple[str, ProviderUsage, str | None]:
        if "error" in raw:
            raise RuntimeError(str(raw["error"]))
        choices = raw.get("choices", [])
        if not choices:
            raise RuntimeError("Malformed cloud response: no choices returned.")
        choice = choices[0] if isinstance(choices[0], dict) else {}
        message = choice.get("message") or {}
        content = str(message.get("content") or choice.get("text") or "").strip()
        usage_raw = raw.get("usage") or {}
        usage = ProviderUsage(
            prompt_tokens=int(usage_raw.get("prompt_tokens") or usage_raw.get("input_tokens") or 0),
            completion_tokens=int(usage_raw.get("completion_tokens") or usage_raw.get("output_tokens") or 0),
            total_tokens=int(usage_raw.get("total_tokens") or 0),
        )
        finish_reason = choice.get("finish_reason") or choice.get("finishReason")
        return content, usage, str(finish_reason) if finish_reason is not None else None

    def _ping(self) -> bool:
        try:
            self._request_json(self._models_url(), timeout=min(5, self.context.config.timeout_seconds or 5))
            return True
        except Exception:
            return False

    def _estimate_usage(self, request: ProviderRequest) -> ProviderUsage:
        prompt_tokens = max(1, len(request.prompt) // 4) if request.prompt else 0
        completion_tokens = request.max_output_tokens or 0
        total_tokens = prompt_tokens + completion_tokens
        return ProviderUsage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, total_tokens=total_tokens)

    def _cost_per_token(self) -> float:
        return float(self.context.config.metadata.get("cost_per_token", 0.0) or 0.0)

    def _safe_error(self, exc: Exception) -> str:
        if isinstance(exc, HTTPError):
            try:
                body = exc.read().decode("utf-8", errors="replace")
            except Exception:
                body = ""
            reason = body or exc.reason or exc.msg or "HTTP error"
            return f"{exc.code}: {reason}"[:240]
        if isinstance(exc, URLError):
            return str(getattr(exc, "reason", exc))[:240]
        return str(exc).splitlines()[0][:240]

    def _error_response(
        self,
        request: ProviderRequest,
        model: str,
        message: str,
        start: float,
        exc: Exception | None = None,
    ) -> ProviderResponse:
        self.metrics.record_failure()
        if exc is not None:
            self.health.mark_failure(self._safe_error(exc))
        else:
            self.health.mark_failure(message)
        return ProviderResponse(
            provider_id=self.provider_id,
            model=model,
            content="",
            metadata={
                "cloud": True,
                "provider_kind": self.kind.value,
                "inventory_checked_at": self._last_checked,
                "latency_ms": (time.perf_counter() - start) * 1000,
            },
            request_id=request.request_id,
            finish_reason="error",
            error=message,
            retryable=bool(exc and self._is_retryable(exc)),
            created_at=utc_now(),
        )

    def _is_retryable(self, exc: Exception) -> bool:
        text = self._safe_error(exc).lower()
        return any(marker in text for marker in ("timeout", "timed out", "connection", "busy", "temporar", "rate limit", "429"))

    def _normalize_error_message(self, message: str) -> str:
        return re.sub(r"[A-Za-z]:\\\\[^ ]+", "[redacted-path]", message)
