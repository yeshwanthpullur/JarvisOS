"""Event bus for Executive JARVIS."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Callable

from jarvis.jarvis_events import JarvisEvent, JarvisEventType


class JarvisEventBus:
    """In-process event bus for executive events."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._handlers: dict[str, list[Callable[[JarvisEvent], None]]] = defaultdict(list)
        self._history: list[JarvisEvent] = []
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = True

    def subscribe(self, event_type: JarvisEventType, handler: Callable[[JarvisEvent], None]) -> None:
        """Subscribe to one event type."""
        self._handlers[event_type.value].append(handler)

    def unsubscribe(self, event_type: JarvisEventType, handler: Callable[[JarvisEvent], None]) -> None:
        """Unsubscribe from one event type."""
        if handler in self._handlers[event_type.value]:
            self._handlers[event_type.value].remove(handler)

    def publish(self, event: JarvisEvent) -> None:
        """Publish an event."""
        self._history.append(event)
        for handler in tuple(self._handlers[event.event_type.value]):
            handler(event)
        self._logger.debug("jarvis_event event_type=%s source=%s", event.event_type.value, event.source)

    def broadcast(self, event: JarvisEvent) -> None:
        """Broadcast an event to subscribers."""
        self.publish(event)

    def history(self) -> tuple[JarvisEvent, ...]:
        """Return event history."""
        return tuple(self._history)

