"""Truthful default provider metadata for the Phase 3 model registry."""

from __future__ import annotations

from .registry import ModelProviderRegistry
from .types import ModelCapability as C, ModelPrivacyMode as P, ModelProvider as M, ModelProviderStatus as S, ModelProviderType as T


def build_default_model_registry(*, ollama_ready: bool = False, ollama_models: tuple[str, ...] = (), vision_ready: bool = False) -> ModelProviderRegistry:
    ready = S.READY if ollama_ready else S.UNAVAILABLE
    vision_status = S.READY if vision_ready else S.UNAVAILABLE
    providers = (
        M("ollama_text", T.OLLAMA, "Ollama Text", ready, (C.CHAT, C.TEXT_GENERATION, C.REASONING, C.CODING, C.EMBEDDINGS), configured=True, enabled=True, default_model=ollama_models[0] if ollama_models else None, available_models=ollama_models[:32], reason="Existing local Ollama runtime is available." if ollama_ready else "Local Ollama runtime availability has not been verified."),
        M("ollama_vision", T.OLLAMA, "Ollama Vision", vision_status, (C.VISION,), configured=True, enabled=True, default_model="llava", available_models=tuple(item for item in ollama_models if "llava" in item.lower())[:32], reason="Existing local vision route is available." if vision_ready else "A ready local vision model has not been verified."),
        M("local_stub", T.STUB, "Local Test Stub", S.DISABLED, (C.CHAT,), configured=True, enabled=False, reason="Test-only provider; disabled in normal runtime."),
        M("llama_cpp", T.LLAMA_CPP, "llama.cpp", S.NOT_CONFIGURED, (C.CHAT, C.TEXT_GENERATION, C.REASONING, C.CODING), enabled=False, reason="llama.cpp adapter is not configured."),
        M("vllm", T.VLLM, "vLLM", S.NOT_CONFIGURED, (C.CHAT, C.REASONING, C.CODING), enabled=False, requires_gpu=True, reason="vLLM adapter is not configured."),
        M("litellm", T.LITELLM, "LiteLLM", S.DISABLED, (C.CHAT, C.REASONING, C.CODING), local=False, privacy_mode=P.OPTIONAL_CLOUD, endpoint_type="gateway", requires_api_key=True, enabled=False, reason="LiteLLM and cloud routing are disabled by default."),
        M("nvidia_nim", T.NVIDIA_NIM, "NVIDIA NIM", S.NOT_CONFIGURED, (C.CHAT, C.REASONING, C.CODING), local=False, privacy_mode=P.CLOUD_ONLY_BLOCKED, endpoint_type="future", requires_api_key=True, requires_gpu=True, enabled=False, reason="NVIDIA NIM is not configured and cloud use is blocked."),
        M("nemotron", T.NVIDIA_NIM, "Nemotron", S.NOT_CONFIGURED, (C.CHAT, C.REASONING, C.CODING), enabled=False, requires_gpu=True, reason="Nemotron route is planned but not installed or configured."),
    )
    return ModelProviderRegistry(providers)

