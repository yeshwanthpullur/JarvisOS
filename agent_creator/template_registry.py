"""Template registry for Agent Creator."""

from __future__ import annotations

from agent_creator.exceptions import RegistryError
from agent_creator.template_engine import BaseTemplate


class TemplateRegistry:
    """Tracks available templates."""

    def __init__(self) -> None:
        self._templates: dict[str, BaseTemplate] = {}
        self.initialized = True

    def register(self, template: BaseTemplate) -> None:
        """Register a template."""
        if template.template_id in self._templates:
            raise RegistryError(f"Template already registered: {template.template_id}")
        self._templates[template.template_id] = template

    def get(self, template_id: str) -> BaseTemplate | None:
        """Return a template by ID."""
        return self._templates.get(template_id)

    def require(self, template_id: str) -> BaseTemplate:
        """Return a template or raise."""
        template = self.get(template_id)
        if template is None:
            raise RegistryError(f"Template not registered: {template_id}")
        return template

    def list_templates(self) -> tuple[BaseTemplate, ...]:
        """List templates."""
        return tuple(self._templates.values())

    def search(self, text: str) -> tuple[BaseTemplate, ...]:
        """Search template metadata."""
        needle = text.lower()
        return tuple(
            item
            for item in self._templates.values()
            if needle in item.name.lower() or needle in item.description.lower()
        )

