"""Safe metadata-only model provider registry."""

from __future__ import annotations

from .types import ModelCapability, ModelProvider, ModelProviderStatus


class ModelProviderRegistryError(ValueError):
    pass


class ModelProviderRegistry:
    def __init__(self, providers: tuple[ModelProvider, ...] = (), max_providers: int = 32) -> None:
        self.max_providers = max(1, min(max_providers, 64))
        self._providers: dict[str, ModelProvider] = {}
        for provider in providers:
            self.register_provider(provider)

    def register_provider(self, provider: ModelProvider) -> None:
        if provider.provider_id in self._providers:
            raise ModelProviderRegistryError(f"duplicate_model_provider:{provider.provider_id}")
        if len(self._providers) >= self.max_providers:
            raise ModelProviderRegistryError("model_provider_registry_limit_exceeded")
        self._providers[provider.provider_id] = provider

    def get_provider(self, provider_id: str) -> ModelProvider | None:
        return self._providers.get(provider_id)

    def list_providers(self) -> tuple[ModelProvider, ...]:
        return tuple(self._providers.values())

    def list_capabilities(self) -> tuple[tuple[str, str, str], ...]:
        return tuple((item.provider_id, capability.value, item.status.value) for item in self._providers.values() for capability in item.capabilities)

    def find_by_capability(self, capability: ModelCapability, *, ready_only: bool = True, local_only: bool = True) -> tuple[ModelProvider, ...]:
        return tuple(
            item for item in self._providers.values()
            if capability in item.capabilities
            and (not ready_only or item.status is ModelProviderStatus.READY)
            and (not local_only or item.local)
            and item.enabled
        )

    def provider_status(self, provider_id: str) -> ModelProviderStatus | None:
        provider = self.get_provider(provider_id)
        return provider.status if provider else None

    def registry_summary(self) -> dict[str, int | bool]:
        providers = self.list_providers()
        return {
            "total_providers": len(providers),
            "ready_providers": sum(item.status is ModelProviderStatus.READY for item in providers),
            "unavailable_providers": sum(item.status in {ModelProviderStatus.UNAVAILABLE, ModelProviderStatus.NOT_CONFIGURED, ModelProviderStatus.ERROR} for item in providers),
            "disabled_providers": sum(item.status is ModelProviderStatus.DISABLED for item in providers),
            "local_providers": sum(item.local for item in providers),
            "valid": not self.validate_registry(),
        }

    def validate_registry(self) -> tuple[str, ...]:
        errors = []
        for item in self._providers.values():
            if item.status is ModelProviderStatus.READY and not item.enabled:
                errors.append(f"ready_disabled:{item.provider_id}")
            if not item.local and item.status is ModelProviderStatus.READY:
                errors.append(f"cloud_ready_by_default:{item.provider_id}")
        return tuple(errors[:32])

