"""Ollama provider integration."""

from __future__ import annotations

import ipaddress
import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from providers.base_provider import BaseProvider, capabilities_for
from providers.provider_context import ProviderContext
from providers.provider_health import ProviderHealth
from providers.provider_types import (
    ModelInfo,
    ProviderCapability,
    ProviderCapabilities,
    ProviderRequest,
    ProviderResponse,
    ProviderUsage,
    utc_now,
)


class OllamaProvider(BaseProvider):
    """Provider contract for a trusted Ollama local runtime."""

    def __init__(self, context: ProviderContext) -> None:
        super().__init__(
            context,
            capabilities_for(
                (
                    ProviderCapability.CHAT,
                    ProviderCapability.REASONING,
                    ProviderCapability.CODING,
                    ProviderCapability.EMBEDDING,
                    ProviderCapability.STREAMING,
                    ProviderCapability.JSON_MODE,
                )
            ),
        )
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
        start = time.perf_counter()
        try:
            self.refresh_inventory()
            reachable = self._ping()
            if reachable:
                self.health.mark_success((time.perf_counter() - start) * 1000)
            else:
                self.health.mark_failure("Ollama service is unreachable.")
        except Exception as exc:  # pragma: no cover - safety net
            self.health.mark_failure(self._safe_error(exc))
        return self.health

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            capabilities=self._capabilities.capabilities,
            models=self._models,
            context_window=self._capabilities.context_window,
            max_tokens=self._capabilities.max_tokens,
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
        return self._execute_chat(request)

    async def execute(self, request: ProviderRequest) -> ProviderResponse:
        return self._execute_chat(request)

    def _execute_chat(self, request: ProviderRequest) -> ProviderResponse:
        start = time.perf_counter()
        models = self.list_models()
        model = request.model or self.context.config.preferred_model or self.context.config.default_model
        if model and models and model not in {item.model_id for item in models}:
            return self._error_response(request, model, "Model missing: the requested Ollama model is not available.", start)
        if not model:
            model = self._first_model_id()
        if not model:
            return self._error_response(request, "", "No usable Ollama models were found.", start)
        timeout = request.timeout_seconds or self.context.config.timeout_seconds or 30
        payload = self._chat_payload(request, model)
        try:
            raw = self._request_json(f"{self._base_url()}/api/chat", payload, timeout=timeout)
            content, usage, finish_reason = self._normalize_chat_response(raw)
            self.metrics.record_request(
                usage.prompt_tokens,
                usage.completion_tokens,
                usage.estimated_cost,
                (time.perf_counter() - start) * 1000,
            )
            self.health.mark_success((time.perf_counter() - start) * 1000)
            return ProviderResponse(
                provider_id=self.provider_id,
                model=model or "",
                content=content,
                usage=usage,
                metadata={
                    "local_only": True,
                    "provider_kind": self.kind.value,
                    "inventory_checked_at": self._last_checked,
                },
                request_id=request.request_id,
                finish_reason=finish_reason,
                created_at=utc_now(),
            )
        except Exception as exc:
            return self._error_response(request, model or "", self._safe_error(exc), start, exc)

    def _discover_models(self) -> tuple[ModelInfo, ...]:
        try:
            raw = self._request_json(f"{self._base_url()}/api/tags", timeout=self.context.config.timeout_seconds or 30)
        except Exception:
            return self._configured_models()
        models: list[ModelInfo] = []
        for item in raw.get("models", []) if isinstance(raw, dict) else []:
            if not isinstance(item, dict):
                continue
            model_id = str(item.get("name") or item.get("model") or "").strip()
            if not model_id:
                continue
            models.append(
                ModelInfo(
                    model_id=model_id,
                    display_name=str(item.get("name") or model_id),
                    capabilities=self._model_capabilities(item),
                    context_window=int(item.get("context_length") or item.get("context_window") or 0),
                    metadata={"source": "ollama", "raw": item},
                )
            )
        return tuple(models or self._configured_models())

    def _configured_models(self) -> tuple[ModelInfo, ...]:
        models = self.context.config.models
        if models:
            return models
        preferred = self.context.config.preferred_model or self.context.config.default_model
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

    def _first_model_id(self) -> str:
        models = self.list_models()
        return models[0].model_id if models else ""

    def _ping(self) -> bool:
        try:
            self._request_json(f"{self._base_url()}/api/tags", timeout=min(5, self.context.config.timeout_seconds or 5))
            return True
        except Exception:
            return False

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
            payload["options"] = {"temperature": request.temperature}
        if request.max_output_tokens is not None:
            payload["options"] = dict(payload.get("options", {}), num_predict=request.max_output_tokens)
        if request.stop_conditions:
            payload["options"] = dict(payload.get("options", {}), stop=list(request.stop_conditions))
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
        message = raw.get("message") or {}
        content = str(message.get("content") or "").strip()
        usage_raw = raw.get("usage") or {}
        usage = ProviderUsage(
            prompt_tokens=int(usage_raw.get("prompt_eval_count") or usage_raw.get("prompt_tokens") or 0),
            completion_tokens=int(usage_raw.get("eval_count") or usage_raw.get("completion_tokens") or 0),
            total_tokens=int(usage_raw.get("total_tokens") or 0),
        )
        finish_reason = raw.get("done_reason") or raw.get("finish_reason")
        return content, usage, str(finish_reason) if finish_reason is not None else None

    def _request_json(self, url: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(url, data=body, method="POST" if body is not None else "GET")
        request.add_header("Content-Type", "application/json")
        with urlopen(request, timeout=timeout) as response:
            data = response.read().decode("utf-8")
        return json.loads(data) if data else {}

    def _base_url(self) -> str:
        base_url = (self.context.config.base_url or "http://127.0.0.1:11434").rstrip("/")
        if not self._is_local_url(base_url):
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

    def _model_capabilities(self, item: dict[str, Any]) -> tuple[ProviderCapability, ...]:
        capabilities = [ProviderCapability.CHAT, ProviderCapability.REASONING]
        if item.get("streaming", True):
            capabilities.append(ProviderCapability.STREAMING)
        return tuple(dict.fromkeys(capabilities))

    def _safe_error(self, exc: Exception) -> str:
        return str(exc).splitlines()[0][:240]

    def _is_retryable(self, exc: Exception) -> bool:
        text = self._safe_error(exc).lower()
        return any(marker in text for marker in ("timeout", "timed out", "connection", "busy", "temporar"))

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
                "local_only": True,
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
