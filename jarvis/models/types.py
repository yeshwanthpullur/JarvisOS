"""Typed metadata for provider-neutral model routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class ModelProviderType(str, Enum):
    OLLAMA = "ollama"
    LLAMA_CPP = "llama_cpp"
    VLLM = "vllm"
    LITELLM = "litellm"
    NVIDIA_NIM = "nvidia_nim"
    OPENAI_COMPATIBLE = "openai_compatible"
    LOCAL_PROCESS = "local_process"
    STUB = "stub"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class ModelCapability(str, Enum):
    TEXT_GENERATION = "text_generation"
    CHAT = "chat"
    REASONING = "reasoning"
    CODING = "coding"
    VISION = "vision"
    IMAGE_GENERATION = "image_generation"
    VIDEO = "video"
    EMBEDDINGS = "embeddings"
    RERANKING = "reranking"
    SPEECH_TO_TEXT = "speech_to_text"
    TEXT_TO_SPEECH = "text_to_speech"
    TOOL_CALLING = "tool_calling"
    STRUCTURED_OUTPUT = "structured_output"
    UNKNOWN = "unknown"


class ModelProviderStatus(str, Enum):
    READY = "ready"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"
    ERROR = "error"


class ModelPrivacyMode(str, Enum):
    LOCAL_ONLY = "local_only"
    OPTIONAL_CLOUD = "optional_cloud"
    CLOUD_ONLY_BLOCKED = "cloud_only_blocked"
    UNKNOWN = "unknown"


class ModelRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class ModelProvider:
    provider_id: str
    provider_type: ModelProviderType
    display_name: str
    status: ModelProviderStatus
    capabilities: tuple[ModelCapability, ...]
    local: bool = True
    privacy_mode: ModelPrivacyMode = ModelPrivacyMode.LOCAL_ONLY
    endpoint_type: str = "local"
    requires_api_key: bool = False
    requires_gpu: bool = False
    configured: bool = False
    enabled: bool = False
    default_model: str | None = None
    available_models: tuple[str, ...] = ()
    reason: str = ""
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.provider_id or len(self.provider_id) > 80:
            raise ValueError("invalid_model_provider_id")
        if len(self.available_models) > 32 or len(self.reason) > 600:
            raise ValueError("model_provider_metadata_limit_exceeded")
        if self.requires_api_key and self.status is ModelProviderStatus.READY and not self.configured:
            raise ValueError("unconfigured_key_provider_cannot_be_ready")


@dataclass(frozen=True, slots=True)
class ModelRoute:
    task_type: str
    selected_provider: str | None
    selected_model: str | None
    capability: ModelCapability
    status: ModelProviderStatus
    local_only: bool = True
    reason: str = ""
    confidence: float = 0.0
    fallback_routes: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    route_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1 or len(self.reason) > 600 or len(self.fallback_routes) > 8:
            raise ValueError("invalid_model_route")


@dataclass(frozen=True, slots=True)
class ModelRequest:
    task_type: str
    prompt_preview: str = ""
    request_id: str = field(default_factory=lambda: str(uuid4()))
    required_capabilities: tuple[ModelCapability, ...] = ()
    preferred_provider: str | None = None
    preferred_model: str | None = None
    local_only: bool = True
    max_context: int = 0
    risk_level: ModelRiskLevel = ModelRiskLevel.LOW
    created_at: str = "phase3"

    def __post_init__(self) -> None:
        if len(self.prompt_preview) > 300 or len(self.required_capabilities) > 8:
            raise ValueError("model_request_metadata_limit_exceeded")

