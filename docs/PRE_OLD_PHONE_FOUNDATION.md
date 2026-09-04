# Pre-Old-Phone Foundation

Roadmap steps 2-20 add a controlled bridge between Executive JARVIS and optional external coding workers. The bridge discovers metadata, plans work, selects bounded routes, records structured status, and prepares isolated Git worktrees. It does not start autonomous swarms, grant approvals, bypass the Execution Broker, merge branches, read credentials, or begin Phase 7.

## Verified Local Inventory

The implementation detects executables without installation. At the implementation checkpoint, Codex CLI `0.153.0`, Hermes Agent `0.20.4`, Aider `0.86.2`, and OpenCode `1.18.27` were detected and responsive. Codex login status was verified through its metadata-only status command. Claude Code, Gemini CLI, Antigravity, Qwen Code, Copilot CLI, Grok CLI, Kimi CLI, and a callable Munder launcher were unavailable. Availability is refreshed at runtime and is not hardcoded as permanent truth. Executable diagnostics expose launcher names, not private installation paths.

OpenCode model discovery returned seven identifiers: `opencode/big-pickle`, `opencode/ling-3.0-flash-fin-free`, `opencode/mimo-v2.5-free`, `opencode/muse-spark-1.2-contributor-free`, `opencode/muse-spark-1.3-contributor-free`, `opencode/nemotron-3-ultra-free`, and `opencode/nemotron-3.5-lightning-free`. The exact `ox-alpha` identifier was not present, so the alias is recorded as unresolved with source/check time and no successor is guessed. Free status is inferred only from an exact `-free` or `/free` suffix; exact prices remain unknown. A harmless isolated OpenCode smoke check returned exactly `OK`, used no tools, and made no repository change.

## Verification Baseline

Before implementation, the scoped JARVIS suite passed `2,139` tests plus `331` subtests with zero failures, and `pip check` reported no broken requirements. Project-level pytest configuration now limits normal discovery to `tests/` and excludes `installations/`, preserving Hermes installation files and tests untouched. `git diff --check` reported no whitespace errors.

After implementation, `53` focused tests, `362` broader regression tests plus `129` subtests, and the full `2,192` tests plus `331` subtests passed with zero failures. The one collection warning predates this work and concerns an existing test helper class with a constructor.

## Boundaries

- External workers are non-authoritative and execution-disabled by default.
- The common adapter supports detection, health, planning, status, events, context references, approval requests, cancellation, resume, result collection, and finish.
- Adapter task starts accept only `plan_only` and `dry_run`; approved execution must still flow through existing Approval, Policy, Broker, and subsystem executors.
- Local Ollama is preferred only when the existing authoritative provider health check reports it ready. Hybrid routes are explicit; provider-managed/cloud routes are disabled by default and cloud providers are represented by credential references only.
- Work is bounded to two parallel tasks by default, validated as an acyclic dependency graph, and supports cancellation and timeouts.
- Repository-modifying work uses a `jarvis/task-...` worktree plan. Creation and cleanup require delegated authorization, and merge is never automatic.
- Context is shared by opaque reference with scope, provenance, trust, and budgets. Personal references are excluded unless explicitly classified and allowed.
- Completion claims require evidence references and remain unverified until reviewed.

Runtime metadata is stored only under ignored `data/workers/` when work is created. Objectives, source content, credentials, private paths, and personal payloads are not persisted by this layer.

The exact next action is Roadmap Step 21. It has not been started.
