"""Constants for the JARVIS OS Agent Creator Framework."""

from __future__ import annotations

from typing import Final


AGENT_CREATOR_VERSION: Final[str] = "0.1.0"
MANIFEST_VERSION: Final[str] = "0.1"
COMPATIBILITY_VERSION: Final[str] = "0.1"
DEFAULT_TEMPLATE_ID: Final[str] = "core_agent"
DEFAULT_BLUEPRINT_ID: Final[str] = "custom"

REQUIRED_AGENT_FILES: Final[tuple[str, ...]] = (
    "__init__.py",
    "agent.py",
    "manifest.json",
    "README.md",
)

