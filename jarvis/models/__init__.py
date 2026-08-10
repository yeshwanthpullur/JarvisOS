"""Provider-neutral, metadata-only model routing foundation."""

from .defaults import build_default_model_registry
from .diagnostics import render_model_command
from .hardware import safe_hardware_summary
from .registry import ModelProviderRegistry, ModelProviderRegistryError
from .router import ModelRouter
from .types import (
    ModelCapability, ModelPrivacyMode, ModelProvider, ModelProviderStatus,
    ModelProviderType, ModelRequest, ModelRiskLevel, ModelRoute,
)

__all__ = [
    "ModelCapability", "ModelPrivacyMode", "ModelProvider", "ModelProviderRegistry",
    "ModelProviderRegistryError", "ModelProviderStatus", "ModelProviderType", "ModelRequest",
    "ModelRiskLevel", "ModelRoute", "ModelRouter", "build_default_model_registry",
    "render_model_command", "safe_hardware_summary",
]
