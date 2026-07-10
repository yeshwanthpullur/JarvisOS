"""Conversation recovery architecture."""

from __future__ import annotations


class ConversationRecovery:
    """Metadata-only recovery helper."""

    initialized = True

    def recover(self) -> dict[str, object]:
        """Return recovery metadata."""
        return {"recovered": True}

