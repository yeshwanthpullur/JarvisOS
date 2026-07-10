"""Blueprint registry for the Agent Creator Framework."""

from __future__ import annotations

import logging

from agent_creator.blueprint import BaseBlueprint
from agent_creator.exceptions import RegistryError
from agent_creator.state import BlueprintState


class BlueprintRegistry:
    """Single source of truth for available blueprints."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._blueprints: dict[str, BaseBlueprint] = {}
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = True

    def register(self, blueprint: BaseBlueprint) -> None:
        """Register a blueprint."""
        if blueprint.blueprint_id in self._blueprints:
            raise RegistryError(f"Blueprint already registered: {blueprint.blueprint_id}")
        blueprint.transition_to(BlueprintState.REGISTERED)
        self._blueprints[blueprint.blueprint_id] = blueprint
        self._logger.info("blueprint_registered blueprint_id=%s", blueprint.blueprint_id)

    def load_defaults(self, blueprints: tuple[BaseBlueprint, ...]) -> None:
        """Register default blueprints."""
        for blueprint in blueprints:
            if blueprint.blueprint_id not in self._blueprints:
                self.register(blueprint)

    def get(self, blueprint_id: str) -> BaseBlueprint | None:
        """Return a blueprint by ID."""
        return self._blueprints.get(blueprint_id)

    def require(self, blueprint_id: str) -> BaseBlueprint:
        """Return a blueprint or raise."""
        blueprint = self.get(blueprint_id)
        if blueprint is None:
            raise RegistryError(f"Blueprint not registered: {blueprint_id}")
        return blueprint

    def unregister(self, blueprint_id: str) -> None:
        """Remove a blueprint."""
        blueprint = self.require(blueprint_id)
        blueprint.state = BlueprintState.REMOVED
        self._blueprints.pop(blueprint_id)

    def search(self, text: str) -> tuple[BaseBlueprint, ...]:
        """Search blueprints by metadata."""
        needle = text.lower()
        return tuple(
            blueprint
            for blueprint in self._blueprints.values()
            if needle in blueprint.name.lower()
            or needle in blueprint.description.lower()
            or needle in blueprint.category.lower()
            or needle in " ".join(blueprint.tags).lower()
        )

    def list_blueprints(self) -> tuple[BaseBlueprint, ...]:
        """List registered blueprints."""
        return tuple(self._blueprints.values())

    def by_category(self, category: str) -> tuple[BaseBlueprint, ...]:
        """Filter blueprints by category."""
        return tuple(item for item in self._blueprints.values() if item.category == category)

