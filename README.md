# JARVIS OS

JARVIS OS is currently at **v0.4.0-alpha - Vision and Deployment Foundation**. The supported primary experience is the local CLI started with `python main.py`; the localhost web interface remains optional and experimental.

For an evidence-based snapshot, roadmap, and health scorecard, see [Current Status](docs/CURRENT_STATUS.md), [Project Health](docs/PROJECT_HEALTH.md), and [Roadmap](docs/ROADMAP.md). The same concise summary is available from the CLI with `project status`.

Tool Intelligence provides governed capability matching, schema validation, risk and approval checks, dry runs, bounded execution, normalized results, and command access through the existing Executive path. See [docs/TOOL_INTELLIGENCE.md](docs/TOOL_INTELLIGENCE.md).

Autonomous Planning produces provider-backed, validated, reviewable plans without executing them. See [docs/AUTONOMOUS_PLANNING.md](docs/AUTONOMOUS_PLANNING.md).

Voice Intelligence adds disabled-by-default local Windows speech output, safe audio-file validation, and governed voice sessions without changing text-mode authority. See [docs/VOICE_INTELLIGENCE.md](docs/VOICE_INTELLIGENCE.md).

Vision Intelligence adds safe CLI image validation, metadata, local-only policy, and provider-neutral routing. Semantic analysis remains unavailable until a model explicitly advertises vision input. See [docs/VISION_INTELLIGENCE.md](docs/VISION_INTELLIGENCE.md).

The Vercel deployment is a deliberately limited online status foundation. Root `main.py` remains the local CLI launcher; `api/index.py` serves only the safe root, `/api/health`, and `/api/status` surfaces. The canonical deployment is `jarvis-os`; it does not provide remote chat, sync, tools, automation, or access to local-only features.

The Local Desktop Interface provides real localhost chat, commands, activity, provider, voice, tool, planning, multi-agent, health, safe-log, approval, and settings views without bypassing existing JARVIS authority. See [docs/LOCAL_DESKTOP_INTERFACE.md](docs/LOCAL_DESKTOP_INTERFACE.md).

JARVIS OS is a modular local-first AI assistant foundation written in Python 3.12+. It includes real local Ollama chat, governed provider routing, safe tools, advisory planning, multi-agent coordination foundations, context and goal intelligence, Windows SAPI voice output, and a partial Vision Intelligence foundation. Online sync and web/mobile automation are not implemented yet.

Online Sync now has an optional, disabled-by-default local foundation: a bounded atomic queue, allowlisted summary schemas, conflict records, audit retention, and manual CLI controls. No real remote backend is configured, and the public Vercel status deployment is not writable sync infrastructure. Raw conversations, databases, audio, images, documents, logs, local paths, and credentials are blocked from the queue.

## Goals

- Modular architecture
- Clean, typed Python code
- Centralized logging
- Environment-backed configuration
- Windows-first, cross-platform-friendly paths
- Simple extension points for future agents, skills, plugins, and services
- Permission-aware plugin framework for future external capabilities
- Provider-neutral AI routing foundation for future model integrations
- Intelligent provider execution architecture for provider/model selection, fallback, metrics, and recovery
- Local AI integration for real local-runtime discovery, model inventory, and execution through Provider Router
- Provider-independent agent framework for future execution workflows
- Workflow and orchestration engine for structured execution across conversation, planning, memory, knowledge, tasks, plugins, providers, agents, and departments
- Retrieval layer for precise memory, knowledge, Obsidian, task, workflow, and history lookup
- Executive JARVIS Core as the permanent request entry point
- Conversation and Command engines for the interactive operating interface
- Goal Intelligence layer for goal clarification, decomposition, progress interpretation, conflict detection, and grounded next steps
- Agent Creator Framework for future blueprint-driven agent manufacturing
- Reflection and Learning Framework for post-execution evaluation and improvement
- Adaptive Intelligence Loop for executive-approved learning recommendations
- Personal Intelligence layer for evidence-based user preferences and context
- Context Intelligence layer for active continuity, reference resolution, and grounded continuation

## Folder Structure

| Path | Purpose |
| --- | --- |
| `agents/` | Agent Framework: lifecycle, registry, factory, bus, router, scheduler, supervisor, orchestrator, metrics, health, and example agents. |
| `agent_creator/` | Agent Creator Framework for future blueprint-driven agent generation. |
| `jarvis/` | Executive JARVIS Core: request pipeline, intent, decision, planning, dispatch, coordination, response, metrics, health, and diagnostics. |
| `conversation/` | Conversation Engine: sessions, context, history, routing, metrics, recovery, and Executive coordination. |
| `commands/` | Command Engine: parser, registry, dispatcher, aliases, validation, history, help, and built-in commands. |
| `agent_creator/` | Agent Creator Framework: blueprints, templates, manifests, validation, generation, installation, rollback, catalog, departments, policy, and audit. |
| `automation/` | Future workflow automation, scheduled jobs, and task runners. |
| `brain/` | Future high-level orchestration and reasoning coordination. |
| `config/` | Settings loading and application logging configuration. |
| `data/` | Local runtime data that should not be committed by default. |
| `data/sync/` | Ignored local sync queue, anonymous installation identifier, conflicts, and bounded audit state. |
| `desktop/` | Dependency-free responsive browser interface assets for local Windows use. |
| `docs/` | Project documentation and architectural notes. |
| `logs/` | Runtime log output. Log files are ignored by Git. |
| `memory/` | Future memory storage, indexing, and recall services. |
| `mobile/` | Future mobile companion integrations. |
| `models/` | Future model adapters and provider integrations. |
| `provider_execution/` | Intelligent provider execution framework for provider/model selection, health, metrics, fallback, recovery, diagnostics, and execution history. |
| `workflow/` | Workflow and orchestration engine for workflow creation, validation, scheduling, execution, checkpoints, recovery, history, metrics, and diagnostics. |
| `retrieval/` | Retrieval layer for memory, knowledge, Obsidian, history, cache, ranking, diagnostics, and context-aware lookup. |
| `personal_intelligence/` | Evidence-based personal context layer built on top of Memory and Retrieval. |
| `task_intelligence/` | Project, goal, milestone, priority, scheduling, progress, dashboard, and reporting intelligence above the task engine. |
| `research/` | Research intelligence and learning engine for structured research, knowledge building, and learning plans. |
| `reasoning/` | Executive reasoning and decision engine for evaluating alternatives, plans, confidence, and decisions before execution. |
| `reflection/` | Reflection and learning engine for post-execution analysis, improvement metadata, and pattern capture. |
| `adaptive/` | Adaptive intelligence loop for executive-approved learning recommendations and adaptation queues. |
| `goal_intelligence/` | Goal intelligence layer for goal clarification, quality evaluation, decomposition, progress, conflicts, and next-step recommendations. |
| `plugins/` | Official extension framework, plugin manifests, lifecycle, permissions, and example plugins. |
| `server/` | Localhost-only interface service and future bounded network interfaces. |
| `api/` | Status-only Vercel entrypoint; it is separate from the local CLI runtime. |
| `skills/` | Reusable abilities that future agents can call. |
| `tests/` | Automated tests for the foundation and future modules. |
| `utils/` | Shared helpers that are truly cross-cutting. |

## Files

| File | Purpose |
| --- | --- |
| `main.py` | Application entry point. Loads settings, configures logging, and starts the foundation runtime. |
| `vercel.json` | Restricts Vercel builds and routes to the status-only `api/index.py` function. |
| `requirements.txt` | Runtime dependency list. The foundation is standard-library first; optional packages are kept minimal. |
| `.env.example` | Example environment configuration. Copy to `.env` for local overrides. |
| `.gitignore` | Professional Python ignore rules for environments, caches, logs, data, and build outputs. |
| `config/settings.py` | Typed immutable settings loader backed by environment variables and `.env`. |
| `config/logging.py` | Central logging setup with console and rotating file handlers. |
| `docs/ARCHITECTURE.md` | High-level architecture notes and extension points. |
| `docs/PLUGIN_FRAMEWORK.md` | Plugin framework lifecycle, manifest, permissions, and dependency guide. |
| `docs/PROVIDER_ROUTER.md` | Provider router architecture, lifecycle, capabilities, and implementation guide. |
| `docs/PROVIDER_EXECUTION.md` | Provider execution framework architecture, provider/model selection, fallback, recovery, diagnostics, and extension guide. |
| `docs/LOCAL_AI_INTEGRATION.md` | Local runtime discovery, local model inventory, local-only policy, and Provider Router integration guide. |
| `docs/WORKFLOW_ENGINE.md` | Workflow engine architecture, workflow types, scheduling, checkpoints, recovery, execution graph, and extension guide. |
| `docs/RETRIEVAL_ENGINE.md` | Retrieval architecture, strategies, selector, ranker, cache, diagnostics, and extension guide. |
| `docs/AGENT_FRAMEWORK.md` | Agent framework architecture, lifecycle, communication, scheduling, health, and extension guide. |
| `docs/JARVIS_EXECUTIVE.md` | Executive JARVIS architecture and responsibilities. |
| `docs/AGENT_CREATOR.md` | Agent Creator Framework overview and extension model. |
| `docs/CONTEXT_INTELLIGENCE.md` | Context continuity, ambiguity handling, active objectives, and continuation behavior. |

## Quick Start

```powershell
cd JarvisOS
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python main.py
```

The CLI is the recommended mode. Start the experimental local desktop interface at `http://127.0.0.1:8765` only when needed:

```powershell
python main.py --ui
# or
.\start_jarvis_ui.ps1
```

Use `--no-browser` to print the URL without opening a browser. The interface is disabled unless explicitly started and does not enable remote access.

No additional packages are required for the interface or core runtime. When dependencies become necessary, add only production-required packages to `requirements.txt`.

Manual sync-foundation commands include `sync status`, `sync on/off`, `sync add project_status`, `sync queue summary`, `sync run`, `sync conflicts`, and `sync cleanup`. `sync on` enables only manual/local queue mode; it never enables background upload.

## Agent Framework

The Agent Framework is the execution-layer foundation for future JARVIS OS capabilities. It provides `BaseAgent`, lifecycle state validation, profiles, capabilities, permissions, registry, factory, loader, message bus, router, scheduler, executor, supervisor, orchestrator, teams, sessions, checkpoints, metrics, health, and compile-safe example agents.

Agents do not implement AI yet. Future agents must communicate with providers only through `ProviderRouter` and should access memory, knowledge, tasks, plugins, and the Obsidian Brain through `AgentContext`.

## Executive JARVIS

JARVIS is the Executive Intelligence layer, not an agent. Every future user request enters JARVIS first, then flows through intent detection, decision metadata, planning, dispatch, existing systems, and response composition. JARVIS never calls providers directly; future AI work must use `ProviderRouter`.

Structured workflows are created by JARVIS and executed by the Workflow Engine. Provider work inside a workflow still routes only through `ProviderRouter` and the Provider Execution Framework.

Retrieval is the precision layer above storage. JARVIS decides what information is needed, and the Retrieval Engine determines how to obtain it from memory, knowledge, Obsidian, and history sources without duplicating storage.

Reflection is the post-execution counterpart to reasoning. Reasoning decides before execution; reflection evaluates afterward and prepares learning metadata for future executive judgment. It never replaces Executive JARVIS or the Provider Router.

Adaptive Intelligence sits after reflection. It prepares validated learning recommendations and keeps Executive JARVIS as the only authority that can approve adaptation.

Personal Intelligence sits on top of Memory and Retrieval. It captures durable user preferences and explainable context, but it does not create a second profile store or override current explicit instructions.

Goal Intelligence sits above Task Intelligence. It analyzes goals, milestones, progress, blockers, and next steps, but Task Intelligence remains the authoritative record owner for goals, milestones, and task state.

Local AI executes only through Provider Router. It discovers real local runtimes, inventories available local models, and preserves local-only policy without introducing a second provider gateway.

Multi-Agent Intelligence extends the existing Agent Framework with Executive-approved planner/reviewer collaboration, bounded parallel or sequential dispatch, evidence-aware synthesis, cancellation, persistence, and user-visible status. Simple conversation continues through the normal provider path, and agent output has no tool or mutation authority.

## Conversation And Commands

The `Jarvis >` prompt now routes through the Conversation Engine and Command Engine. Commands are registered through `CommandRegistry`, while normal text requests continue into Executive JARVIS.

## Agent Creator Framework

The Agent Creator Framework is the official manufacturing system for future JARVIS OS agents. It uses blueprints, templates, manifests, validators, installers, rollback metadata, catalogs, departments, security policies, and audit records to create provider-independent agents that conform to the Agent Framework.

Agent creation remains architecture-focused and separate from Multi-Agent Intelligence. It does not autonomously generate code, install agents, browse, automate the desktop, or grant execution authority.

## Configuration

Configuration can be provided through environment variables or a local `.env` file.

```text
JARVIS_APP_NAME="JARVIS OS"
JARVIS_ENVIRONMENT=development
JARVIS_DEBUG=false
JARVIS_LOG_LEVEL=INFO
```

Environment variables take precedence over values in `.env`.

## Development Notes

- Keep AI-specific behavior out of the foundation until clear interfaces exist.
- Prefer dependency injection when modules need collaborators.
- Keep platform-specific logic isolated in `desktop/` or `mobile/`.
- Add tests with each meaningful behavior change.
- Avoid committing local data, logs, secrets, or virtual environments.
