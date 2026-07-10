"""Command alias resolver."""

from __future__ import annotations


class CommandAliases:
    """Resolves command aliases."""

    def __init__(self) -> None:
        self._aliases: dict[str, str] = {"quit": "exit", "?": "help"}
        self.initialized = True

    def resolve(self, command: str) -> str:
        """Resolve an alias."""
        return self._aliases.get(command, command)

