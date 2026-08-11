# CLI Guide

Prompt 81 diagnostics: `orchestrator status`, `sessions`, `show`, `graph`, `trace`, `metrics`, `events`, `health`, `cancel`, `budget`, `agents`, and `providers`. Output is bounded metadata without context payloads, credentials, private paths, or stack traces.

Prompt 79 research commands include `research providers`, `research provider-health`, `research budget`, `research quick <question>`, `research standard <question>`, `research deep <question>`, `research search <query>`, `research verify <claim>`, `research citations <id>`, `research contradictions <id>`, and `research knowledge-candidates <id>`. Live search reports unavailable until governed configuration exists.

Prompt 80 adds `knowledge status`, `knowledge sources`, source metadata, registration/ingestion/reindex/removal plans, `knowledge search`, provenance, embedding/backend health, and metadata-only history. It intentionally omits ingest-everything, crawling, trust-all, and all-repository indexing.

Advanced runtime commands include `model runtime-status`, `model runtimes`, runtime/profile/alias inspection, hardware and compatibility plans, route explanations, fallback/circuit status, and non-executing start/stop/download plans. Existing model commands remain supported.

The `plugin` namespace provides bounded status, inspection, capability, permission, dependency, health, integrity, and history commands. Lifecycle commands produce safe plans or require exact approval; installation and executable external runtimes remain disabled.

The `mcp` namespace exposes bounded status, server/tool/resource/prompt metadata, health, classification, lifecycle plans, guarded call plans/dry-runs/calls, and metadata-only history. It has no unrestricted install command.

GitHub service commands use the `github` namespace for status/auth/health/scope, bounded reads, write plans, guarded create actions, and metadata-only history. They do not replace local Git commands.

Prompt 73 adds `telegram status`, `help`, `capabilities`, `identity`, `auth-status`, `pair`, `pair-status`, `unpair`, `chats`, `validate-chat`, `polling-status`, `start`, `stop`, `send-plan`, `send-dry-run`, `send`, `rate-status`, `history`, and `health`. Status never exposes the token, and `send` never bypasses scoped approval and Broker dispatch.

Prompt 74 adds parallel `discord`, `email`, and `slack` namespaces for status, help, health, explicit destination validation, send planning/dry-run, approved send entry points, rate status, and bounded history. CLI output contains no credential values or recipient lists.

## Prompt 71 External Integration Controls

Use `integration status`, `integration policy`, `provider show <id>`, `provider capabilities`, `provider health <id>`, `provider policy`, `provider validate <id>`, `provider history`, `credential status <id>`, and `credential required`. These commands display bounded metadata only. They never reveal credential values, contact a provider, enable paid/cloud execution, launch MCP/plugins, or replace Phase 4 approvals and Broker authority.

## Phase 3 Batch 2

Use `document`, `browser`, `scheduler`, `communication`, `adapter`, `model advanced`, and `evaluation` command groups for bounded diagnostics and planning. None installs, sends, schedules, starts a provider, launches MCP, performs interactive browsing, or exports telemetry.

The interactive `Jarvis >` prompt is the current primary JARVIS experience. It is backed by the Conversation and Command engines; ordinary messages use Executive JARVIS and Provider Router, while registered commands remain on the command path.

Start with `python main.py`. Use `help` for the focused command guide and `project status` for the current release, MVP readiness, and next milestone. Common operating commands include `local only on/off`, `local use <model>`, `provider status`, `tools status`, `voice status`, `voice output on/off`, `voice say <text>`, and `exit`.

## Phase 4 Controlled Execution

Use `execution status`, `approval status`, and `broker status` to inspect the safe execution boundary. Dedicated commands are grouped under `file-exec`, `command`, `git-exec`, `notification`, `browser`, and `scheduler`. Planning and dry-run commands do not create side effects. Actual supported operations require an exact approval and broker validation; critical or unsupported operations remain blocked.

## Conversation Intelligence

Plain text supports bounded multi-turn follow-ups such as `Explain more`, `Go deeper`, `Simplify`, `Give examples`, `Compare`, `Summarize`, `Repeat`, `Continue`, `Why?`, and `How?`. Clear references such as `it`, `that`, `former`, and `latter` use the active topic or comparison; ambiguous references produce one clarification question instead of a guess.

Use `conversation status`, `conversation topic`, `conversation confidence`, `conversation mode`, `conversation summary`, and `conversation reset`. Context is in memory and bounded. `conversation reset` does not delete persistent memories; `memory forget <id>` remains the explicit deletion authority. `voice listen send` and `voice interrupt` submit through this same conversation path without automatically storing transcripts.

## Mobile Planning Foundation

Use `mobile status`, `mobile policy`, `mobile capabilities`, `mobile setup`, `mobile plan <task>`, `mobile audit`, and `mobile close`. These commands do not connect to or control a phone. Requests involving messages, calls, notifications, contacts, photos, sensors, device input, apps, settings, purchases, login, unlock, or background monitoring are blocked.

`project status` shows fixed, still-open, intentionally restricted, and externally blocked limitation counts. Use `limitations status`, `limitations open`, `limitations fixed`, `limitations show <id>`, `limitations category <category>`, or `limitations next` for bounded evidence and ownership. The full review is in `docs/LIMITATIONS_REVIEW_PROMPT_40.md`.

## Memory Commands

Use `memory status`, `memory help`, `memory list`, `memory search <text>`, `memory show <id>`, `memory remember <title> | <content>`, `memory forget <id>`, `memory update <id> <content>`, `memory archive <id>`, `memory recent`, `memory preferences`, `memory projects`, `memory audit`, `memory cleanup`, and `memory consolidate`. Memory stays local, secret-aware, and bounded. The memory layer can feed safe context back into chat, but it does not sync anywhere and it does not replace command or conversation authority.

Web inspection commands are `web status`, `web policy`, `web session`, `web open <https-url>`, `web title`, `web url`, `web snapshot`, `web audit`, and `web close`. They use the governed Web Automation Manager and a bounded standard-library adapter. `web open` reads safe public HTML/text metadata and a sanitized preview; it does not launch or control a browser. Local/internal targets, sensitive query fields, credential URLs, unsafe schemes, and unsafe categories are rejected. Interactive and sensitive actions remain unavailable.

Vision commands are `vision status`, `vision models`, `vision analyze <image_path>`, `vision describe <image_path>`, `vision ask <image_path> <question>`, `vision audit`, and `vision cleanup`. Quote paths containing spaces. PNG, JPEG, and WebP images are validated before any provider request. Analysis is local-only through the registered Ollama provider, and audit stores metadata rather than image bytes, base64, prompts, or full paths.

## Image Generation Workflow

Use `image status`, `image help`, `image providers`, `image plan <prompt>`, `image safety <prompt>`, `image generate <prompt>`, `image generate <prompt> --dry-run`, `image history`, and `image show <job_id>`. The workflow is local-first, bounded, and truthful: it validates prompt size, blocks unsafe categories before provider dispatch, and reports unavailable when no real local provider is configured. Dry runs do not create output files. Runtime metadata stays under ignored local storage. See [`IMAGE_GENERATION.md`](IMAGE_GENERATION.md).

## Video Editing Workflow

Use `video status`, `video help`, `video providers`, `video plan <prompt>`, `video safety <prompt>`, `video history`, and `video show <plan_id>`. The workflow is local-first, bounded, and truthful: it validates prompt size, blocks unsafe categories before provider dispatch, and reports unavailable when no real local provider is configured. Plans are non-destructive and dry-run oriented. Runtime metadata stays under ignored local storage. See [`VIDEO_EDITING.md`](VIDEO_EDITING.md).

## Local Voice Input Setup

Voice input is manually verified with Vosk, `sounddevice`, a microphone, and a local Indian-English model. Keep the model outside Git and configure `JARVIS_VOSK_MODEL_PATH` or `voice.stt_model_path`. Run `voice input status`, `voice input on`, and then `voice listen`. Use `voice listen send` only when the transcript should enter the normal JARVIS command/chat flow. `voice input test` performs one explicit test capture. Missing local prerequisites are reported truthfully without hidden recording. See [`VOICE_INPUT.md`](VOICE_INPUT.md).

JARVIS does not download a model, activate a microphone in the background, retain captured PCM, persist transcript text in audit, or use cloud speech. Wake word and continuous listening remain unavailable.

## Voice Playback Controls

Spoken replies run in one ordered background queue. Use `voice speaking status` to inspect progress, `voice pause` for a safe-boundary pause, `voice stop` to interrupt immediately while retaining unspoken speech, and `voice resume` to continue. Because Windows SAPI cannot report the exact word reached when its process is terminated, resuming after `voice stop` restarts the interrupted chunk from its beginning; already completed chunks are not replayed. Use `voice cancel` to interrupt immediately and permanently discard the retained queue. Starting a new response replaces and cancels any older resumable speech.

## Local Vision Setup

Install a vision-capable Ollama model outside JARVIS, set `vision.model` to its name, then run `vision models` and `vision status`. Local LLaVA analysis and image Q&A are manually verified on the current machine. The model must advertise vision input; a name alone is not accepted as proof, and `llama3.2:1b` is not silently treated as vision-capable. JARVIS does not download models and reports unavailable truthfully when Ollama or the configured model is absent.

## Sync Commands

```text
sync status
sync on
sync off
sync add project_status
sync queue
sync queue summary
sync inspect <sync_item_id>
sync cancel <sync_item_id>
sync retry <sync_item_id>
sync run
sync conflicts
sync cleanup
```

Sync starts disabled. `sync on` enables a manual local queue only; it does not enable background or remote uploading. `sync add project_status` queues a compact allowlisted health snapshot. `sync run` truthfully returns unavailable until an authenticated encrypted remote adapter exists. The Vercel status endpoint is not a sync backend.

## Multi-Agent OS Foundation

Phase 3 commands inspect metadata and create plan-only routing decisions. They do not execute agents, skills, model calls, external plugins, or side effects.

```text
agent status
agent list
agent capabilities
agent show <agent_name>
agent find <capability>
agent diagnostics
agent ready
agent unavailable
agent future
agent risks
agent approvals

prime status
prime route "<request>"
prime plan "<request>"
prime risk "<request>"
prime explain "<request>"

model status
model providers
model capabilities
model route "<task>"
model explain "<task>"
model hardware
model policy

skill status
skill list
skill capabilities
skill show <skill_id>
skill find <capability_or_category>
skill permissions <skill_id>
skill diagnostics
```

Future agents and skills appear in diagnostics so missing dependencies and safety restrictions are visible. They remain disabled or unavailable. Cloud providers, external plugins, and MCP are disabled by default; Nemotron is listed as not configured rather than installed. High-risk capabilities declare approval requirements, critical future actions are blocked, and `plan_only` is the default execution mode.

## Research Agent

Research commands create bounded plans and metadata-only history. They do not perform browser side effects, call external search APIs, invent citations, or write Persistent Memory.

```text
research status
research help
research plan "<query>"
research safety "<query>"
research sources "<query>"
research summarize "<query>"
research evidence <research_id>
research show <research_id>
research history
```

`research summarize` is honest when no evidence was supplied. Restricted medical, legal, financial, safety-critical engineering, robotics, drone, and chemical requests remain high-level and may require explicit confirmation for action-oriented workflows. Private-person targeting and operational wrongdoing are blocked.

## Coding Agent

Coding commands inspect bounded Git metadata and produce plans. They do not modify files, run commands, install dependencies, commit, push, deploy, or access secrets.

```text
coding status
coding help
coding inspect
coding plan "<request>"
coding risk "<request>"
coding diff
coding review
coding tests "<request>"
coding show <coding_job_id>
coding history
```

`coding diff` and `coding review` report bounded file/count metadata, risks, and test recommendations without printing full diffs. High-risk write or remote actions remain plan-only and approval-required. Critical destructive or secret-access requests are blocked.
