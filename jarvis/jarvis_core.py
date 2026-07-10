"""Executive JARVIS Core public facade."""

from __future__ import annotations

from jarvis.jarvis_context import JarvisContext
from jarvis.jarvis_manager import JarvisExecutiveStatistics, JarvisManager
from jarvis.jarvis_request import JarvisRequest
from jarvis.jarvis_response import JarvisResponse


class JarvisCore:
    """Permanent Executive entry point for JARVIS OS."""

    def __init__(self, manager: JarvisManager | None = None, context: JarvisContext | None = None) -> None:
        self.manager = manager or JarvisManager(context=context)
        self.initialized = False

    def initialize(self) -> JarvisExecutiveStatistics:
        """Initialize the executive manager."""
        stats = self.manager.initialize()
        self.initialized = True
        return stats

    def handle(self, request: JarvisRequest) -> JarvisResponse:
        """Handle a request through JARVIS first."""
        return self.manager.handle_request(request)

    def shutdown(self) -> None:
        """Shutdown JARVIS."""
        self.manager.shutdown()
        self.initialized = False

    def statistics(self) -> JarvisExecutiveStatistics:
        """Return executive statistics."""
        return self.manager.statistics()

