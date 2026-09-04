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
    "provider list", "provider status", "provider health", "provider inspect", "provider current", "provider enable", "provider disable", "provider test", "provider show", "provider capabilities", "provider policy", "provider validate", "provider history",
    "environment status", "environment audit", "tool status", "tool audit", "tool environments", "tool inspect", "tool environment-show",
    "integration status", "integration policy", "credential status", "credential required",
    *{f"plugin {x}" for x in ("status","help","list","show","inspect","capabilities","permissions","dependencies","health","history","enable-plan","enable","disable-plan","disable","install-plan","update-plan","uninstall-plan","verify")}, *{f"orchestrator {x}" for x in ("status","sessions","show","graph","trace","metrics","events","health","cancel","budget","agents","providers")}, "agent list", "agent status", "agent capabilities", "agent show", "agent find", "agent diagnostics", "agent ready", "agent unavailable", "agent future", "agent risks", "agent approvals", "multiagent status", "multiagent list", "multiagent show", "multiagent cancel", "multiagent limits", "multiagent mode",
    "department list", "memory status", "memory help", "memory list", "memory search", "memory show", "memory remember", "memory forget", "memory update", "memory archive", "memory recent", "memory preferences", "memory projects", "memory audit", "memory cleanup", "memory consolidate", "memory count", "memory export", "memory import", "knowledge search", "task list", "task status", *{f"workflow {x}" for x in ("status","list","show","graph","trace","events","checkpoints","checkpoint-show","pause","resume","cancel","simulate","health","metrics","cleanup-plan","artifact-list","artifact-show")}, "config show", "logs recent", "project status",
    "profile show", "profile list", "profile explain", "profile update", "profile forget", "profile confirm", "profile reject",
    "context show", "context recent", "context clear", "context pause", "context resume", "context previous", "objective show",
    "goal show", "goal status", "goal route-check", "goal list", "goal review", "goal progress", "goal next", "goal blockers", "goal evaluate", "goal conflicts", "goal align", "goal portfolio", "goal pause", "goal resume", "goal complete",
    "local status", "local providers", "local models", "local refresh", "local use", "local test", "local explain-selection", "local only",
    "cloud status", "cloud providers", "cloud models", "cloud refresh", "cloud use", "cloud test", "cloud explain-selection", "cloud only",
    "tool list", "tool show", "tool health", "tool match", "tool permissions", "tool dry-run", "tool history", "tool invocation", "tool cancel", "tool mode", "tool limits", "tools status",
    "plan status", "plan list", "plan show", "plan steps", "plan validate", "plan alternatives", "plan approve", "plan reject", "plan pause", "plan resume", "plan cancel", "plan replan", "plan history", "plan mode", "plan limits",
    "voice status", "voice on", "voice off", "voice listen", "voice cleanup", "voice stop", "voice pause", "voice resume", "voice speaking", "voice speaking status", "voice repeat", "voice replay", "voice correction", "voice cancel", "voice interrupt", "voice session", "voice sessions", "voice session-inspect", "voice devices", "voice backend", "voice device", "voice input", "voice output", "voice say", "voice transcribe", "voice mode", "voice privacy", "voice language", "voice rate", "voice volume", "voice raw-audio", "voice limits", "voice health", "voice stt", "voice tts", "voice test-input", "voice test-output",
    "vision status", "vision health", "vision models", "vision inspect", "vision analyze", "vision describe", "vision ask", "vision audit", "vision cleanup",
    "ocr extract", "camera status", "camera devices", "camera start", "camera stop", "camera session", "camera session-inspect",
    "image status", "image help", "image providers", "image generate", "image plan", "image safety", "image history", "image show", "image config",
    "video status", "video help", "video providers", "video plan", "video safety", "video history", "video show", "video config",
    "sync status", "sync on", "sync off", "sync queue", "sync add", "sync inspect", "sync cancel", "sync retry", "sync cleanup", "sync run", "sync conflicts",
    "web status", "web open", "web title", "web url", "web snapshot", "web close", "web audit", "web policy", "web session",
    "mobile status", "mobile policy", "mobile capabilities", "mobile setup", "mobile plan", "mobile audit", "mobile close", "mobile devices", "mobile session",
    "conversation status", "conversation diagnostics", "conversation route", "conversation reset", "conversation summary", "conversation mode", "conversation confidence", "conversation topic", "route inspect",
    "research status", "research help", "research providers", "research provider-health", "research budget", "research plan", "research safety", "research search", "research sources", "research quick", "research standard", "research deep", "research verify", "research summarize", "research evidence", "research contradictions", "research citations", "research knowledge-candidates", "research show", "research history",
    "knowledge status","knowledge help","knowledge sources","knowledge source-show","knowledge source-status","knowledge register-plan","knowledge ingest-plan","knowledge search","knowledge show","knowledge provenance","knowledge reindex-plan","knowledge remove-plan","knowledge embedding-status","knowledge backend-status","knowledge health","knowledge history",
    "coding status", "coding health", "coding tools", "coding tool", "coding tool-inspect", "coding help", "coding inspect", "coding plan", "coding risk", "coding diff", "coding review", "coding tests", "coding apply", "coding cancel", "coding audit", "coding show", "coding history",
    "git status", "git diff", "git history", "git verify", "system status", "system health", "system processes", "system disks", "system memory", "system gpu", "app status", "app list", "app open", "app close", "file status", "file read", "file write", "file move", "file copy", "file delete", "automation status", "automation permissions", "scheduler list", "scheduler inspect",
    "connector status", "connector list", "connector health", "connector inspect", "connector capabilities", "connector permissions", "connector test", "connector audit",
    "performance status", "performance startup", "performance providers", "performance models", "performance memory", "performance voice", "operations status", "operations alerts", "operations audit", "phase6 status", "phase6 candidate", "phase6 checklist",
    "document status", "document health", "document help", "document plan", "document safety", "document types", "document parse", "document inspect", "document extract", "document summarize", "document ask", "document chunks", "document sources", "document audit", "document clear-session", "document show", "document history",
    "ocr status", "ocr health", "ocr parse", "knowledge ingest-document", "knowledge source", "knowledge source-inspect",
    "browser status", "browser health", "browser help", "browser plan", "browser safety", "browser capabilities", "browser permissions", "browser test", "browser session", "browser session-list", "browser session-inspect", "browser session-close", "browser sources", "browser summarize", "browser show", "browser history",
    "crawl status", "crawl health", "crawl plan", "crawl run", "crawl inspect", "research health", "research source", "research source-list", "research source-inspect", "research audit", "research clear-session",
    "memory health", "memory inspect", "memory conflicts", "vector status", "vector health", "vector collections", "vector inspect", "graph status", "graph health", "graph inspect", "embedding status", "embedding health", "embedding models",
    "scheduler status", "scheduler help", "scheduler plan", "scheduler safety", "scheduler validate", "scheduler preview", "scheduler capabilities", "scheduler show", "scheduler history",
    "communication status", "communication help", "communication providers", "communication plan", "communication safety", "communication draft", "communication notify-plan", "communication show", "communication history", "communication provider-status", "communication provider-show", "communication provider-health", "communication destination-validate", "communication send-plan", "communication send-safety", "communication send-dry-run", "communication attachment-check", "communication rate-status",
    *{f"telegram {x}" for x in ("status","help","capabilities","identity","auth-status","pair","pair-status","unpair","chats","validate-chat","polling-status","start","stop","send-plan","send-dry-run","send","rate-status","history","health")},
    *{f"discord {x}" for x in ("status","help","health","destinations","validate-destination","send-plan","send-dry-run","send","rate-status","history")},
    *{f"email {x}" for x in ("status","help","providers","health","validate-address","send-plan","send-dry-run","send","rate-status","history")},
    *{f"slack {x}" for x in ("status","help","health","destinations","validate-destination","send-plan","send-dry-run","send","rate-status","history")},
    *{f"github {x}" for x in ("status","help","auth-status","health","repo","branch","commits","capabilities","rate-status","issues","issue-show","issue-plan","issue-create","prs","pr-show","pr-plan","pr-create","releases","release-show","release-plan","release-create","workflows","checks","history")},
    *{f"mcp {x}" for x in ("status","help","servers","server-show","server-health","discover","tools","tool-show","classify","capabilities","resources","resource-show","resource-read","prompts","start","stop","call-plan","call-dry-run","call","history")},
    "adapter status", "adapter help", "adapter list", "adapter show", "adapter plan", "adapter safety", "adapter permissions", "adapter capabilities", "adapter show-job", "adapter history",
    "model advanced",
    *{f"model {x}" for x in ("runtime-status","runtimes","runtime-show","runtime-health","profiles","profile-show","provider-health","compatibility","resource-plan","route-explain","start-plan","start","stop","download-plan","download-status","fallback-status","circuit-status","aliases","alias-show")},
    "evaluation status", "evaluation help", "evaluation run", "evaluation routing", "evaluation safety", "evaluation truthfulness", "evaluation observability", "evaluation show", "evaluation history",
    "release-readiness status", "release-readiness help", "release-readiness gates", "release-readiness contracts", "release-readiness missing", "release-readiness candidate", "release-readiness matrix", "release-readiness scenarios", "release-readiness scorecard", "release-readiness checklist", "release-readiness verify",
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
    *{f"runtime {x}" for x in ("status","health","components","dependencies","metrics","traces","diagnostics","alerts","providers","models","queues","resources","breakers","circuits","recovery-plan","recovery-history","events","dashboard","profile","capacity","verify")},
    *{f"security {x}" for x in ("status","health","identities","permissions","policies","trust","incidents","audit","compliance","risks","governance","events","metrics","dashboard","validate","verify","policy-show","incident-show","audit-show","trust-show")},
    "prime status", "prime route", "prime plan", "prime risk", "prime explain",
    *{f"worker {x}" for x in ("status", "list", "show", "health", "inventory", "models", "model-refresh", "providers", "route", "select", "task-plan")},
    *{f"work {x}" for x in ("status", "plan", "show", "graph", "worktree-plan", "context", "messages")},
    "model status", "model providers", "model capabilities", "model route", "model explain", "model hardware", "model policy", "model list", "model health", "model inspect", "model roles", "model select", "model test",
    "skill status", "skill list", "skill capabilities", "skill show", "skill find", "skill permissions", "skill diagnostics",
    "research status", "research help", "research providers", "research provider-health", "research budget", "research plan", "research safety", "research search", "research sources", "research quick", "research standard", "research deep", "research verify", "research summarize", "research evidence", "research contradictions", "research citations", "research knowledge-candidates", "research show", "research history",
    "knowledge status","knowledge help","knowledge sources","knowledge source-show","knowledge source-status","knowledge register-plan","knowledge ingest-plan","knowledge search","knowledge show","knowledge provenance","knowledge reindex-plan","knowledge remove-plan","knowledge embedding-status","knowledge backend-status","knowledge health","knowledge history",
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
            if name in {"browser session", "research source", "knowledge source"} and args and args[0] in {"list", "inspect", "close"}:
                name = f"{name.split()[0]} {name.split()[1]}-{args.pop(0)}"
            if name in {"camera session", "coding tool", "voice session"} and args and args[0] == "inspect":
                name = f"{name.split()[0]} {name.split()[1]}-inspect"
        return ParsedCommand(name=name.lower(), arguments=tuple(args), flags=flags, raw=text)
