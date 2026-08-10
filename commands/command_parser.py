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
    "provider list", "provider status", "provider health", "provider enable", "provider disable", "provider test", "provider show", "provider capabilities", "provider policy", "provider validate", "provider history",
    "integration status", "integration policy", "credential status", "credential required",
    "plugin list", "plugin status", "agent list", "agent status", "agent capabilities", "agent show", "agent find", "agent diagnostics", "agent ready", "agent unavailable", "agent future", "agent risks", "agent approvals", "multiagent status", "multiagent list", "multiagent show", "multiagent cancel", "multiagent limits", "multiagent mode",
    "department list", "memory status", "memory help", "memory list", "memory search", "memory show", "memory remember", "memory forget", "memory update", "memory archive", "memory recent", "memory preferences", "memory projects", "memory audit", "memory cleanup", "memory consolidate", "memory count", "memory export", "memory import", "knowledge search", "task list", "task status", "workflow list", "config show", "logs recent", "project status",
    "profile show", "profile list", "profile explain", "profile update", "profile forget", "profile confirm", "profile reject",
    "context show", "context recent", "context clear", "context pause", "context resume", "context previous", "objective show",
    "goal show", "goal list", "goal review", "goal progress", "goal next", "goal blockers", "goal evaluate", "goal conflicts", "goal align", "goal portfolio", "goal pause", "goal resume", "goal complete",
    "local status", "local providers", "local models", "local refresh", "local use", "local test", "local explain-selection", "local only",
    "cloud status", "cloud providers", "cloud models", "cloud refresh", "cloud use", "cloud test", "cloud explain-selection", "cloud only",
    "tool list", "tool show", "tool health", "tool match", "tool permissions", "tool dry-run", "tool history", "tool invocation", "tool cancel", "tool mode", "tool limits", "tools status",
    "plan status", "plan list", "plan show", "plan steps", "plan validate", "plan alternatives", "plan approve", "plan reject", "plan pause", "plan resume", "plan cancel", "plan replan", "plan history", "plan mode", "plan limits",
    "voice status", "voice on", "voice off", "voice listen", "voice cleanup", "voice stop", "voice pause", "voice resume", "voice speaking", "voice speaking status", "voice repeat", "voice replay", "voice correction", "voice cancel", "voice interrupt", "voice session", "voice devices", "voice backend", "voice device", "voice input", "voice output", "voice say", "voice transcribe", "voice mode", "voice privacy", "voice language", "voice rate", "voice volume", "voice raw-audio", "voice limits", "voice health",
    "vision status", "vision models", "vision analyze", "vision describe", "vision ask", "vision audit", "vision cleanup",
    "image status", "image help", "image providers", "image generate", "image plan", "image safety", "image history", "image show", "image config",
    "video status", "video help", "video providers", "video plan", "video safety", "video history", "video show", "video config",
    "sync status", "sync on", "sync off", "sync queue", "sync add", "sync inspect", "sync cancel", "sync retry", "sync cleanup", "sync run", "sync conflicts",
    "web status", "web open", "web title", "web url", "web snapshot", "web close", "web audit", "web policy", "web session",
    "mobile status", "mobile policy", "mobile capabilities", "mobile setup", "mobile plan", "mobile audit", "mobile close", "mobile devices", "mobile session",
    "conversation status", "conversation reset", "conversation summary", "conversation mode", "conversation confidence", "conversation topic",
    "research status", "research help", "research plan", "research safety", "research sources", "research summarize", "research evidence", "research show", "research history",
    "coding status", "coding help", "coding inspect", "coding plan", "coding risk", "coding diff", "coding review", "coding tests", "coding show", "coding history",
    "document status", "document help", "document plan", "document safety", "document types", "document inspect", "document extract", "document summarize", "document ask", "document show", "document history",
    "browser status", "browser help", "browser plan", "browser safety", "browser capabilities", "browser sources", "browser summarize", "browser show", "browser history",
    "scheduler status", "scheduler help", "scheduler plan", "scheduler safety", "scheduler validate", "scheduler preview", "scheduler capabilities", "scheduler show", "scheduler history",
    "communication status", "communication help", "communication providers", "communication plan", "communication safety", "communication draft", "communication notify-plan", "communication show", "communication history",
    "adapter status", "adapter help", "adapter list", "adapter show", "adapter plan", "adapter safety", "adapter permissions", "adapter capabilities", "adapter show-job", "adapter history",
    "model advanced",
    "evaluation status", "evaluation help", "evaluation run", "evaluation routing", "evaluation safety", "evaluation truthfulness", "evaluation observability", "evaluation show", "evaluation history",
    "release-readiness status", "release-readiness help", "release-readiness gates", "release-readiness contracts", "release-readiness missing", "release-readiness candidate",
    *{f"execution {x}" for x in ("status","help","policy","permissions","readiness","risk","plan","capabilities","show","history")},
    *{f"approval {x}" for x in ("status","help","request","pending","list","show","approve","deny","cancel","revoke","expire","validate")},
    *{f"broker {x}" for x in ("status","help","capabilities","plan","validate","dry-run","execute","show","history")},
    *{f"file-exec {x}" for x in ("status","help","policy","validate","plan","dry-run","create","write","append","mkdir","rename","move","delete","rollback","show","history")},
    *{f"command {x}" for x in ("status","help","policy","allowlist","validate","plan","dry-run","execute","show","history")},
    *{f"git-exec {x}" for x in ("status","help","policy","inspect","files","validate","plan","dry-run","stage","unstage","commit","push","show","history")},
    *{f"notification {x}" for x in ("status","help","providers","policy","plan","validate","dry-run","send","test","show","history")},
    *{f"scheduler {x}" for x in ("runtime-status","jobs","due","create","run","run-due","pause","resume","cancel","runs","runtime-policy")},
    *{f"browser {x}" for x in ("policy","validate","dry-run","read","read-show","read-history")},
    "limitations status", "limitations list", "limitations open", "limitations fixed", "limitations show", "limitations category", "limitations next", "limitations summary",
    "prime status", "prime route", "prime plan", "prime risk", "prime explain",
    "model status", "model providers", "model capabilities", "model route", "model explain", "model hardware", "model policy",
    "skill status", "skill list", "skill capabilities", "skill show", "skill find", "skill permissions", "skill diagnostics",
    "research status", "research help", "research plan", "research safety", "research sources", "research summarize", "research evidence", "research show", "research history",
}


class CommandParser:
    initialized = True

    def parse(self, text: str) -> ParsedCommand:
        stripped = text.strip()
        if stripped.startswith("/"): stripped = stripped[1:]
        if not stripped: return ParsedCommand(name="", raw=text, valid=False)
        lexer = shlex.shlex(stripped, posix=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        lexer.escape = ""
        try:
            parts = tuple(lexer)
        except ValueError as exc:
            parse_error = "unmatched_quotation" if "quotation" in str(exc).lower() else "invalid_syntax"
            return ParsedCommand(
                name="",
                raw=text,
                valid=False,
                metadata={"parse_error": parse_error},
            )
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
            if name == "sync queue" and args and args[0] == "summary":
                name = "sync queue summary"
                args.pop(0)
            if name == "model advanced" and args and args[0] in {"status", "providers", "show", "plan", "compare", "hardware", "route", "safety", "checklist", "history"}:
                name = f"{name} {args.pop(0)}"
        return ParsedCommand(name=name.lower(), arguments=tuple(args), flags=flags, raw=text)
