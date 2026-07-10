"""Response formatter for Executive JARVIS."""

from __future__ import annotations

from jarvis.jarvis_response import JarvisResponse


class JarvisResponseFormatter:
    """Formats executive responses for user-facing channels."""

    initialized = True

    def format(self, response: JarvisResponse) -> str:
        """Return response content."""
        return response.content

