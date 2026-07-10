"""CLI facade for future Executive JARVIS commands."""

from __future__ import annotations

from jarvis.jarvis_core import JarvisCore
from jarvis.jarvis_request import JarvisRequest


class JarvisCLI:
    """Minimal CLI adapter that keeps requests flowing through JARVIS."""

    def __init__(self, core: JarvisCore) -> None:
        self.core = core
        self.initialized = True

    def submit(self, text: str) -> str:
        """Submit text to JARVIS and return response content."""
        return self.core.handle(JarvisRequest(content=text)).content

