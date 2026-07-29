"""Command parser."""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ParsedCommand:
    name: str
    arguments: tuple[str, ...] = ()
    flags: dict[str, str | bool] = field(default_factory=dict)
    raw: str = ""
    valid: bool = True
    metadata: dict[str, object] = field(default_factory=dict)


_SUBCOMMANDS = {
    "provider list", "provider status", "provider health", "provider enable", "provider disable", "provider test",
    "plugin list", "plugin status", "agent list", "agent status", "multiagent status", "multiagent list", "multiagent show", "multiagent cancel", "multiagent limits", "multiagent mode",
    "department list", "memory search", "knowledge search", "task list", "task status", "workflow list", "config show", "logs recent",
    "profile show", "profile list", "profile explain", "profile update", "profile forget", "profile confirm", "profile reject",
    "context show", "context recent", "context clear", "context pause", "context resume", "context previous", "objective show",
    "goal show", "goal list", "goal review", "goal progress", "goal next", "goal blockers", "goal evaluate", "goal conflicts", "goal align", "goal portfolio", "goal pause", "goal resume", "goal complete",
    "local status", "local providers", "local models", "local refresh", "local use", "local test", "local explain-selection", "local only",
    "cloud status", "cloud providers", "cloud models", "cloud refresh", "cloud use", "cloud test", "cloud explain-selection", "cloud only",
    "tool list", "tool show", "tool health", "tool match", "tool permissions", "tool dry-run", "tool history", "tool invocation", "tool cancel", "tool mode", "tool limits",
    "plan status", "plan list", "plan show", "plan steps", "plan validate", "plan alternatives", "plan approve", "plan reject", "plan pause", "plan resume", "plan cancel", "plan replan", "plan history", "plan mode", "plan limits",
}


class CommandParser:
    initialized = True

    def parse(self, text: str) -> ParsedCommand:
        stripped = text.strip()
        if stripped.startswith("/"): stripped = stripped[1:]
        if not stripped: return ParsedCommand(name="", raw=text, valid=False)
        parts = tuple(shlex.split(stripped))
        flags: dict[str, str | bool] = {}
        args: list[str] = []
        for part in parts[1:]:
            if part.startswith("--"):
                key, _, value = part[2:].partition("=")
                flags[key] = value if value else True
            else: args.append(part)
        name = parts[0]
        if args and f"{name} {args[0]}" in _SUBCOMMANDS:
            name = f"{name} {args.pop(0)}"
            if name in {"local only", "cloud only"} and args and args[0] in {"on", "off"}:
                name = f"{name} {args.pop(0)}"
        return ParsedCommand(name=name.lower(), arguments=tuple(args), flags=flags, raw=text)
