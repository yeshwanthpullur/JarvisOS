"""Google Gemini provider interface."""

from __future__ import annotations

import json
import time
from typing import Any

from providers.cloud_provider_base import CloudProviderBase
from providers.provider_types import ProviderRequest, ProviderResponse, ProviderUsage
from providers.provider_types import ModelInfo, ProviderCapability, utc_now


class GoogleProvider(CloudProviderBase):
    """Provider contract for Gemini."""

    api_key_envs = ("GOOGLE_API_KEY", "GEMINI_API_KEY")
    default_base_url = "https://generativelanguage.googleapis.com"
    models_path = "/v1beta/models"
    chat_path = "/v1beta/models/{model}:generateContent"
    supports_json_mode = False
    supports_embeddings = True
    supports_vision = True
    supports_streaming = True

    def _auth_headers(self) -> dict[str, str]:
        return {}

    def _api_key_query(self) -> str:
        key = self._api_key()
        if not key:
            return ""
        return f"?key={key}"

    def _chat_url_for_model(self, model: str) -> str:
        return f"{self._base_url()}{self.chat_path.format(model=model)}{self._api_key_query()}"

    def _request_json(self, url: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
        from urllib.request import Request, urlopen

        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(url, data=body, method="POST" if body is not None else "GET")
        request.add_header("Content-Type", "application/json")
        if key := self._api_key():
            request.add_header("x-goog-api-key", key)
        with urlopen(request, timeout=timeout) as response:
            data = response.read().decode("utf-8")
        return json.loads(data) if data else {}

    def _chat_payload(self, request: ProviderRequest, model: str) -> dict[str, Any]:
        parts = []
        if request.system_instructions:
            parts.append({"text": request.system_instructions})
        context_lines = self._selected_context_lines(request)
        if context_lines:
            parts.append({"text": "\n".join(context_lines)})
        parts.append({"text": request.prompt})
        payload: dict[str, Any] = {
            "contents": [{"parts": parts}],
            "generationConfig": {},
        }
        if request.temperature is not None:
            payload["generationConfig"]["temperature"] = request.temperature
        if request.max_output_tokens is not None:
            payload["generationConfig"]["maxOutputTokens"] = request.max_output_tokens
        if request.stop_conditions:
            payload["generationConfig"]["stopSequences"] = list(request.stop_conditions)
        return payload

    def _discover_models(self) -> tuple[ModelInfo, ...]:
        if not self._api_key():
            return self._configured_models()
        try:
            raw = self._request_json(f"{self._base_url()}{self.models_path}{self._api_key_query()}", timeout=self.context.config.timeout_seconds or 30)
        except Exception:
            return self._configured_models()
        models = []
        for item in raw.get("models", []) if isinstance(raw, dict) else []:
            if not isinstance(item, dict):
                continue
            model_id = str(item.get("name") or item.get("baseModelId") or "").strip()
            if not model_id:
                continue
            supported = tuple(
                capability
                for capability in (
                    ProviderCapability.CHAT,
                    ProviderCapability.REASONING,
                    ProviderCapability.CODING,
                    ProviderCapability.VISION,
                    ProviderCapability.EMBEDDING,
                    ProviderCapability.FUNCTION_CALLING,
                    ProviderCapability.STREAMING,
                )
            )
            models.append(
                ModelInfo(
                    model_id=model_id,
                    display_name=str(item.get("displayName") or model_id),
                    capabilities=supported,
                    context_window=int(item.get("inputTokenLimit") or 0),
                    max_tokens=int(item.get("outputTokenLimit") or 0),
                    metadata={"source": "gemini", "raw": item},
                )
            )
        return tuple(models or self._configured_models())

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
            raw = self._request_json(self._chat_url_for_model(model), payload, timeout=timeout)
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

    def _normalize_chat_response(self, raw: dict[str, Any]) -> tuple[str, ProviderUsage, str | None]:
        if "error" in raw:
            raise RuntimeError(str(raw["error"]))
        candidates = raw.get("candidates") or []
        content = ""
        finish_reason = None
        if candidates and isinstance(candidates[0], dict):
            parts = candidates[0].get("content", {}).get("parts", []) if isinstance(candidates[0].get("content"), dict) else []
            content = "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict)).strip()
            finish_reason = candidates[0].get("finishReason")
        usage_raw = raw.get("usageMetadata") or {}
        usage = ProviderUsage(
            prompt_tokens=int(usage_raw.get("promptTokenCount") or 0),
            completion_tokens=int(usage_raw.get("candidatesTokenCount") or 0),
            total_tokens=int(usage_raw.get("totalTokenCount") or 0),
        )
        return content, usage, str(finish_reason) if finish_reason is not None else None
