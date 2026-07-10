"""Provider Router integration adapter for Executive JARVIS."""

from __future__ import annotations

from typing import Any


class JarvisProviders:
    """Routes future provider work through the existing Provider Router only."""

    initialized = True

    def __init__(
        self,
        provider_router: Any | None = None,
        provider_manager: Any | None = None,
        provider_execution_manager: Any | None = None,
    ) -> None:
        self.provider_router = provider_router
        self.provider_manager = provider_manager
        self.provider_execution_manager = provider_execution_manager

    def is_available(self) -> bool:
        """Return whether a provider router is attached."""
        return self.provider_router is not None

    def prepare_execution(self, intent: str, goal: str, **metadata: Any) -> Any:
        """Prepare provider execution through the execution framework when available."""
        if self.provider_execution_manager is None:
            raise RuntimeError("Provider Execution Framework is not available.")
        request = self.provider_execution_manager.build_execution_request(intent, goal, **metadata)
        return self.provider_execution_manager.execute_through_provider_router(request)

    def statistics(self) -> dict[str, object]:
        """Return provider statistics if available."""
        results: dict[str, object] = {}
        if self.provider_manager is not None and hasattr(self.provider_manager, "statistics"):
            stats = self.provider_manager.statistics()
            results["registered_providers"] = getattr(stats, "registered_providers", 0)
        if self.provider_execution_manager is not None and hasattr(self.provider_execution_manager, "statistics"):
            execution_stats = self.provider_execution_manager.statistics()
            results["provider_execution_status"] = getattr(execution_stats, "status", "unknown")
            results["provider_execution_records"] = getattr(execution_stats, "registered_providers", 0)
        return results
