"""History store for Executive JARVIS."""

from __future__ import annotations

from jarvis.jarvis_response import JarvisResponse


class JarvisHistory:
    """In-memory request/response history."""

    def __init__(self) -> None:
        self._responses: list[JarvisResponse] = []
        self.initialized = True

    def add(self, response: JarvisResponse) -> None:
        """Record a response."""
        self._responses.append(response)

    def list_responses(self) -> tuple[JarvisResponse, ...]:
        """List responses."""
        return tuple(self._responses)

