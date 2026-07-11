"""Command parser."""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ParsedCommand:
    """Parsed command object."""

    name: str
    arguments: tuple[str, ...] = ()
    flags: dict[str, str | bool] = field(default_factory=dict)
    raw: str = ""
    valid: bool = True
    metadata: dict[str, object] = field(default_factory=dict)


class CommandParser:
    """Parses commands, arguments, flags, quoted strings, and subcommands."""

    initialized = True

    def parse(self, text: str) -> ParsedCommand:
        """Parse input into a command object."""
        stripped = text.strip()
        if stripped.startswith("/"):
            stripped = stripped[1:]
        if not stripped:
            return ParsedCommand(name="", raw=text, valid=False)
        parts = tuple(shlex.split(stripped))
        flags: dict[str, str | bool] = {}
        args: list[str] = []
        for part in parts[1:]:
            if part.startswith("--"):
                key, _, value = part[2:].partition("=")
                flags[key] = value if value else True
            else:
                args.append(part)
        name = parts[0]
        if args and f"{name} {args[0]}" in {"provider list", "provider status", "provider health", "plugin list", "plugin status", "agent list", "agent status", "department list", "memory search", "knowledge search", "task list", "task status", "workflow list", "config show", "logs recent", "profile show", "profile list", "profile explain", "profile update", "profile forget", "profile confirm", "profile reject", "context show", "context recent", "context clear", "context pause", "context resume", "context previous", "objective show", "goal show", "goal list", "goal review", "goal progress", "goal next", "goal blockers", "goal evaluate", "goal conflicts", "goal align", "goal portfolio", "goal pause", "goal resume", "goal complete"}:
            name = f"{name} {args.pop(0)}"
        return ParsedCommand(name=name.lower(), arguments=tuple(args), flags=flags, raw=text)
