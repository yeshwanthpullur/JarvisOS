"""Normalized local provider and model-role metadata for Phase 6."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import shutil
from urllib.request import Request, urlopen


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


MODEL_ROLES = (
    "general_chat", "reasoning", "coding", "summarization", "document_qa",
    "research_synthesis", "vision", "fast_response", "fallback", "embedding",
)


@dataclass(frozen=True, slots=True)
class ProviderSnapshot:
    provider_id: str
    provider_name: str
    runtime: str
    local_or_cloud: str
    configured: bool
    detected: bool
    enabled: bool
    policy_allowed: bool
    approval_required: bool
    healthy: bool
    current_model: str
    available_models: tuple[str, ...]
    last_checked_at: str
    last_error: str = ""


@dataclass(frozen=True, slots=True)
class ModelRecord:
    model_id: str
    model_name: str
    provider_id: str
    runtime: str
    roles: tuple[str, ...]
    context_window: int = 0
    supports_tools: bool = False
    supports_vision: bool = False
    supports_embeddings: bool = False
    supports_streaming: bool = True
    supports_json: bool = False
    enabled: bool = True
    policy_allowed: bool = True
    downloaded: bool = False
    available: bool = False
    healthy: bool = False
    last_checked_at: str = ""
    last_error: str = ""


class LocalModelCatalog:
    """Local-only inventory and routing metadata; no model calls or downloads."""

    def __init__(self, *, base_url: str = "http://127.0.0.1:11434", timeout: float = 2.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = min(max(timeout, 0.2), 5.0)
        self._providers: dict[str, ProviderSnapshot] = {}
        self._models: dict[str, ModelRecord] = {}
        self._role_selection: dict[str, str] = {}
        self.refresh(probe=False)

    def refresh(self, *, probe: bool = True) -> ProviderSnapshot:
        executable = shutil.which("ollama")
        models: tuple[str, ...] = ()
        healthy = False
        error = ""
        if probe:
            try:
                request = Request(f"{self.base_url}/api/tags", method="GET")
                with urlopen(request, timeout=self.timeout) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                models = tuple(str(item.get("name") or item.get("model")) for item in payload.get("models", ()) if item.get("name") or item.get("model"))[:32]
                healthy = True
            except Exception as exc:
                error = f"Local Ollama health check failed: {type(exc).__name__}."[:240]
        checked = _now()
        snapshot = ProviderSnapshot("ollama", "Ollama", "ollama", "local", True, bool(executable) or healthy, True, True, False, healthy, "", models, checked, error)
        self._providers = {
            "ollama": snapshot,
            "llama_cpp": ProviderSnapshot("llama_cpp", "llama.cpp", "llama.cpp", "local", False, bool(shutil.which("llama-cli")), False, True, True, False, "", (), checked, "Backup adapter is not configured."),
            "litellm": ProviderSnapshot("litellm", "LiteLLM", "gateway", "local_gateway", False, bool(shutil.which("litellm")), False, False, True, False, "", (), checked, "Disabled by default; it cannot bypass JARVIS provider policy."),
            "vllm": ProviderSnapshot("vllm", "vLLM", "vllm", "local_linux", False, False, False, False, True, False, "", (), checked, "Deferred: Linux/CUDA runtime required."),
        }
        self._models = {name: self._model(name, healthy, checked) for name in models}
        return snapshot

    def _model(self, name: str, healthy: bool, checked: str) -> ModelRecord:
        lowered = name.lower()
        vision = any(marker in lowered for marker in ("llava", "vision", "vl"))
        embed = any(marker in lowered for marker in ("embed", "bge", "nomic"))
        coding = any(marker in lowered for marker in ("code", "coder"))
        roles: list[str] = []
        if vision:
            roles.append("vision")
        elif embed:
            roles.append("embedding")
        else:
            roles.extend(("general_chat", "fast_response", "fallback", "summarization", "document_qa", "research_synthesis"))
            if coding:
                roles.append("coding")
            roles.append("reasoning")
        return ModelRecord(name, name, "ollama", "ollama", tuple(dict.fromkeys(roles)), supports_vision=vision, supports_embeddings=embed, supports_json=not vision, downloaded=True, available=True, healthy=healthy, last_checked_at=checked)

    def providers(self) -> tuple[ProviderSnapshot, ...]:
        return tuple(self._providers[key] for key in sorted(self._providers))

    def provider(self, provider_id: str) -> ProviderSnapshot | None:
        return self._providers.get(provider_id)

    def models(self) -> tuple[ModelRecord, ...]:
        return tuple(self._models[key] for key in sorted(self._models))

    def model(self, model_id: str) -> ModelRecord | None:
        return self._models.get(model_id)

    def select(self, role: str, model_id: str) -> bool:
        if role not in MODEL_ROLES:
            raise ValueError("unknown_model_role")
        record = self.model(model_id)
        if record is None or role not in record.roles or not record.available or not record.policy_allowed:
            return False
        self._role_selection[role] = model_id
        return True

    def route(self, role: str) -> ModelRecord | None:
        selected = self._role_selection.get(role)
        if selected:
            return self.model(selected)
        return next((item for item in self.models() if role in item.roles and item.enabled and item.policy_allowed and item.healthy), None)

    def summary(self) -> dict[str, object]:
        providers = self.providers()
        models = self.models()
        return {"providers": len(providers), "healthy_providers": sum(item.healthy for item in providers), "models": len(models), "healthy_models": sum(item.healthy for item in models), "local_only": True, "cloud_fallback": False, "downloads_automatic": False}
