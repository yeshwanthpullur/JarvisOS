"""Lifecycle helper for the Executive JARVIS Core."""

from __future__ import annotations

from jarvis.jarvis_state import JarvisState, validate_jarvis_transition


class JarvisLifecycle:
    """Reusable lifecycle state holder."""

    def __init__(self) -> None:
        self.state = JarvisState.CREATED
        self.initialized = True

    def transition_to(self, state: JarvisState) -> None:
        """Validate and apply a transition."""
        validate_jarvis_transition(self.state, state)
        self.state = state

