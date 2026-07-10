"""Plugin event model and in-process event bus."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


@dataclass(frozen=True, slots=True)
class PluginEvent:
    """Event emitted by or about a plugin."""

    plugin_id: str
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PluginEventBus:
    """Simple synchronous event bus for plugin lifecycle events."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._subscribers: dict[str, list[Callable[[PluginEvent], None]]] = {}
        self._logger = logger or logging.getLogger(__name__)

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[PluginEvent], None],
    ) -> None:
        """Subscribe to an event type."""
        self._subscribers.setdefault(event_type, []).append(handler)

    def publish(self, event: PluginEvent) -> None:
        """Publish an event to subscribers."""
        self._logger.info(
            "plugin_event plugin_id=%s event_type=%s",
            event.plugin_id,
            event.event_type,
        )
        for handler in self._subscribers.get(event.event_type, ()):
            handler(event)
