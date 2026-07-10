# JARVIS OS

JARVIS OS is the foundation for a modular AI Operating System written in Python 3.12+. This repository currently provides architecture, configuration, logging, memory, knowledge, task, Obsidian Brain, plugin, provider-routing, provider-execution, agent-framework, agent-creator, and Executive JARVIS infrastructure. AI behavior is intentionally not implemented yet.

## Goals

- Modular architecture
- Clean, typed Python code
- Centralized logging
- Environment-backed configuration
- Windows-first, cross-platform-friendly paths
- Simple extension points for future agents, skills, plugins, and services
- Permission-aware plugin framework for future external capabilities
- Provider-neutral AI routing foundation for future model integrations
- Intelligent provider execution architecture for future provider/model selection, fallback, metrics, and recovery
- Provider-independent agent framework for future execution workflows
- Workflow and orchestration engine for structured execution across conversation, planning, memory, knowledge, tasks, plugins, providers, agents, and departments
- Retrieval layer for precise memory, knowledge, Obsidian, task, workflow, and history lookup
- Executive JARVIS Core as the permanent request entry point
- Conversation and Command engines for the interactive operating interface
- Agent Creator Framework for future blueprint-driven agent manufacturing

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
| `desktop/` | Desktop integrations, with Windows support as the first priority. |
| `docs/` | Project documentation and architectural notes. |
| `logs/` | Runtime log output. Log files are ignored by Git. |
| `memory/` | Future memory storage, indexing, and recall services. |
| `mobile/` | Future mobile companion integrations. |
| `models/` | Future model adapters and provider integrations. |
| `provider_execution/` | Intelligent provider execution framework for provider/model selection, health, metrics, fallback, recovery, diagnostics, and execution history. |
| `workflow/` | Workflow and orchestration engine for workflow creation, validation, scheduling, execution, checkpoints, recovery, history, metrics, and diagnostics. |
| `retrieval/` | Retrieval layer for memory, knowledge, Obsidian, history, cache, ranking, diagnostics, and context-aware lookup. |
| `task_intelligence/` | Project, goal, milestone, priority, scheduling, progress, dashboard, and reporting intelligence above the task engine. |
| `research/` | Research intelligence and learning engine for structured research, knowledge building, and learning plans. |
| `reasoning/` | Executive reasoning and decision engine for evaluating alternatives, plans, confidence, and decisions before execution. |
| `plugins/` | Official extension framework, plugin manifests, lifecycle, permissions, and example plugins. |
| `server/` | Future API server, background services, and network interfaces. |
| `skills/` | Reusable abilities that future agents can call. |
| `tests/` | Automated tests for the foundation and future modules. |
| `utils/` | Shared helpers that are truly cross-cutting. |

## Files

| File | Purpose |
| --- | --- |
| `main.py` | Application entry point. Loads settings, configures logging, and starts the foundation runtime. |
| `requirements.txt` | Runtime dependency list. The foundation is standard-library first; optional packages are kept minimal. |
| `.env.example` | Example environment configuration. Copy to `.env` for local overrides. |
| `.gitignore` | Professional Python ignore rules for environments, caches, logs, data, and build outputs. |
| `config/settings.py` | Typed immutable settings loader backed by environment variables and `.env`. |
| `config/logging.py` | Central logging setup with console and rotating file handlers. |
| `docs/ARCHITECTURE.md` | High-level architecture notes and extension points. |
| `docs/PLUGIN_FRAMEWORK.md` | Plugin framework lifecycle, manifest, permissions, and dependency guide. |
| `docs/PROVIDER_ROUTER.md` | Provider router architecture, lifecycle, capabilities, and implementation guide. |
| `docs/PROVIDER_EXECUTION.md` | Provider execution framework architecture, provider/model selection, fallback, recovery, diagnostics, and extension guide. |
| `docs/WORKFLOW_ENGINE.md` | Workflow engine architecture, workflow types, scheduling, checkpoints, recovery, execution graph, and extension guide. |
| `docs/RETRIEVAL_ENGINE.md` | Retrieval architecture, strategies, selector, ranker, cache, diagnostics, and extension guide. |
| `docs/AGENT_FRAMEWORK.md` | Agent framework architecture, lifecycle, communication, scheduling, health, and extension guide. |
| `docs/JARVIS_EXECUTIVE.md` | Executive JARVIS architecture and responsibilities. |
| `docs/AGENT_CREATOR.md` | Agent Creator Framework overview and extension model. |

## Quick Start

```powershell
cd JarvisOS
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python main.py
```

No packages are required yet. When dependencies become necessary, add only production-required packages to `requirements.txt`.

## Agent Framework

The Agent Framework is the execution-layer foundation for future JARVIS OS capabilities. It provides `BaseAgent`, lifecycle state validation, profiles, capabilities, permissions, registry, factory, loader, message bus, router, scheduler, executor, supervisor, orchestrator, teams, sessions, checkpoints, metrics, health, and compile-safe example agents.

Agents do not implement AI yet. Future agents must communicate with providers only through `ProviderRouter` and should access memory, knowledge, tasks, plugins, and the Obsidian Brain through `AgentContext`.

## Executive JARVIS

JARVIS is the Executive Intelligence layer, not an agent. Every future user request enters JARVIS first, then flows through intent detection, decision metadata, planning, dispatch, existing systems, and response composition. JARVIS never calls providers directly; future AI work must use `ProviderRouter`.

Structured workflows are created by JARVIS and executed by the Workflow Engine. Provider work inside a workflow still routes only through `ProviderRouter` and the Provider Execution Framework.

Retrieval is the precision layer above storage. JARVIS decides what information is needed, and the Retrieval Engine determines how to obtain it from memory, knowledge, Obsidian, and history sources without duplicating storage.

## Conversation And Commands

The `Jarvis >` prompt now routes through the Conversation Engine and Command Engine. Commands are registered through `CommandRegistry`, while normal text requests continue into Executive JARVIS.

## Agent Creator Framework

The Agent Creator Framework is the official manufacturing system for future JARVIS OS agents. It uses blueprints, templates, manifests, validators, installers, rollback metadata, catalogs, departments, security policies, and audit records to create provider-independent agents that conform to the Agent Framework.

The current implementation is architecture-only. It does not implement AI-assisted generation, autonomous code editing, marketplace networking, browser automation, desktop automation, voice, vision, or provider calls.

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
