# JARVIS OS Master Specification

This document is the constitution of JARVIS OS. Future architecture, code generation, provider integrations, agents, plugins, automation, and documentation must follow this specification unless the project maintainers explicitly revise it.

JARVIS OS must evolve incrementally. Existing working code must not be rewritten merely for style, novelty, or convenience. New capabilities should extend the system through stable interfaces, preserve backward compatibility, and document major decisions.

## Vision

JARVIS OS is an AI Operating System.

It is not a chatbot. A chatbot primarily exchanges messages. JARVIS OS is intended to become a personal intelligence layer that can understand goals, remember context, reason across time, plan work, coordinate specialized agents, interact with local and remote tools, and automate tasks with explicit user approval.

The long-term vision is a trusted personal system that can:

- Learn from user-approved interactions and durable knowledge sources.
- Remember useful information in human-readable and inspectable forms.
- Reason about goals, constraints, risks, tradeoffs, and next actions.
- Plan multi-step work and preserve progress across sessions.
- Coordinate multiple agents with different responsibilities.
- Use replaceable AI providers without depending on one vendor.
- Automate local and external tasks only through permission-based workflows.
- Explain important decisions in language the user can understand.
- Grow through plugins, skills, providers, and platform integrations.

JARVIS OS must be designed as durable infrastructure first. Intelligence should be added through clear contracts, not scattered through unrelated modules.

## Core Principles

### Modular Architecture

Every major capability must live behind a clear module boundary. Modules should expose typed contracts and data models rather than leaking implementation details.

### Local-First Design Where Practical

JARVIS OS should prefer local files, local configuration, local memory, and local execution where practical. Cloud services may be supported, but they must be optional and replaceable.

### Human-Readable Memory

Memory should be inspectable by the user and maintainers. Important stored knowledge, task state, and decisions should be readable without requiring a proprietary AI provider.

### Long-Term Memory

JARVIS OS must preserve useful context across sessions. Long-term memory should support recall, review, correction, and deletion.

### Replaceable AI Providers

The system must never depend on a single AI provider. Provider integrations must implement shared interfaces and be routed through provider-neutral infrastructure.

### Multi-Agent Architecture

Future intelligence should be composed from agents with specific responsibilities. Agents must coordinate through explicit task state, messages, and shared infrastructure rather than hidden global state.

### Security By Default

Sensitive actions must default to safe behavior. Dangerous capabilities, including shell execution, installers, file modification, network access, credential use, and automation, must be gated by configuration and permission checks.

### Permission-Based Automation

Automation must be planned, explainable, auditable, and approved before execution when user data, system state, external accounts, payment, installation, deletion, or irreversible changes are involved.

### Explainable Decisions

Important decisions must be traceable. Provider selection, task planning, agent delegation, automation execution, plugin permission use, and memory writes should be explainable through logs, reports, or task snapshots.

### Extensible Plugin System

External integrations must be plugins. Plugins must be isolated, declare their permissions, and interact with JARVIS OS through stable contracts.

## Architecture

JARVIS OS uses Clean Architecture principles. High-level orchestration must not depend directly on low-level provider SDKs, file formats, installers, network clients, or platform-specific APIs. Those details belong behind interfaces.

### Folder Responsibilities

| Folder | Responsibility |
| --- | --- |
| `agents/` | Future autonomous workers and role-specific agents. Agents coordinate goals but should depend on contracts, not concrete infrastructure. |
| `automation/` | Future scheduled, event-driven, or user-approved workflows. Automation must remain permission-based and auditable. |
| `brain/` | Future high-level reasoning and orchestration layer. The brain decides how to decompose goals and coordinate agents. |
| `config/` | Central configuration. Owns defaults, `config.yaml`, `.env` overrides, typed settings, and logging setup. |
| `data/` | Local runtime data. Generated or user-specific data should not be committed by default. |
| `desktop/` | Desktop integrations, Windows first. Platform-specific behavior must be isolated here or behind interfaces. |
| `docs/` | Engineering documentation, architecture notes, provider guides, and long-term design records. |
| `documents/` | Documentation reader contracts for Markdown, PDF, HTML, DOCX, and TXT. Future parsers must implement these contracts. |
| `downloads/` | Download manager contracts for files, GitHub repositories, datasets, and documentation. Download behavior must support progress, integrity checks, queueing, and organization. |
| `installers/` | Installer framework contracts for inspection, planning, execution, verification, rollback, and reporting. |
| `logs/` | Runtime logs. Logs are operational artifacts and should not be committed. |
| `memory/` | Future memory systems, including working memory, long-term memory, semantic memory, skill memory, conversation memory, and knowledge graph storage. |
| `mobile/` | Future mobile companion integrations. Mobile behavior must remain separate from core orchestration. |
| `models/` | Future model metadata, model-selection helpers, and provider-neutral model capability definitions. |
| `plugins/` | External integrations and optional extensions. Plugins must be isolated and permission-declared. |
| `providers/` | Provider interfaces, provider placeholders, provider request and response envelopes, cost models, capability models, and provider routing. |
| `server/` | Future local or remote API surfaces, such as HTTP, WebSocket, or IPC services. |
| `skills/` | Reusable abilities future agents can call. Skills must be composable and permission-aware. |
| `tasks/` | Task snapshot and persistence contracts for resumable work. Task state must remain provider-neutral. |
| `tests/` | Automated tests for core modules and future behavior. |
| `utils/` | Shared helpers only when genuinely cross-cutting. Domain-specific helpers belong in their domain module. |

### Module Communication

Modules communicate through typed data objects, abstract base classes, and dependency injection.

Agents and orchestration modules should receive dependencies such as `AppSettings`, `ProviderRouter`, `TaskPersistence`, `DownloadManager`, `Installer`, and `DocumentationReader` from composition code. They should not create provider clients, read environment variables, parse configuration files, or reach into unrelated modules directly.

The intended communication model is:

1. `main.py` or a future application composition layer loads `AppSettings`.
2. Logging is configured once from settings.
3. Concrete infrastructure implementations are constructed at the application boundary.
4. Agents and brain services receive interfaces.
5. Agents save progress through task persistence.
6. Provider usage flows through `ProviderRouter`.
7. External actions flow through permission-aware download, installer, plugin, and automation interfaces.

### Dependency Rules

- High-level policy must not depend on low-level implementation details.
- Agents may depend on provider, task, memory, document, download, installer, and plugin interfaces.
- Agents must not depend directly on a provider SDK.
- Provider implementations must depend on `BaseProvider`, not on agents.
- Plugins must depend on public contracts, not private module internals.
- Platform-specific code must not leak into core modules.
- Configuration must be loaded centrally; modules must not parse `.env` or `config.yaml` directly.
- Logging must use standard logging hooks and module loggers.
- Runtime data, logs, secrets, and generated files must remain outside committed source unless explicitly intended.

## Coding Standards

JARVIS OS code must follow these standards:

- Use Python 3.12 or newer.
- Use type hints everywhere practical.
- Follow SOLID principles.
- Follow Clean Architecture boundaries.
- Include comprehensive docstrings for public modules, classes, and methods.
- Use structured logging through the logging system, not print statements.
- Write unit tests for core modules and all non-trivial behavior.
- Never hardcode secrets, tokens, credentials, or user-specific paths.
- Prefer configuration-driven behavior over hardcoded decisions.
- Keep functions and classes focused on one responsibility.
- Prefer immutable data models for shared state snapshots.
- Preserve backward compatibility when extending public contracts.
- Raise explicit exceptions for invalid configuration or unsupported behavior.
- Avoid duplicate code; extract shared logic only when the duplication is real and stable.
- Keep provider-specific code inside provider implementations.
- Keep platform-specific code inside platform modules or adapters.

## Memory Philosophy

Memory is a first-class subsystem. JARVIS OS should remember only what is useful, inspectable, permission-appropriate, and correctable.

### Working Memory

Working memory stores short-lived context for the active task or session. It exists so agents can coordinate current goals, recent decisions, open questions, temporary constraints, and immediate next steps without treating them as permanent facts.

Working memory should be easy to clear and should not automatically become long-term memory.

### Long-Term Memory

Long-term memory stores durable user-approved information that remains useful across sessions. It exists so JARVIS OS can become more personal and capable over time without repeatedly asking for the same context.

Long-term memory must support review, correction, deletion, and provenance.

### Semantic Memory

Semantic memory stores concepts, facts, summaries, preferences, and relationships in a form that can be searched and reasoned over. It exists so the system can recall meaning rather than only raw transcripts.

Semantic memory should record source references and confidence where practical.

### Skill Memory

Skill memory stores reusable procedures, patterns, commands, workflows, and implementation lessons. It exists so JARVIS OS can improve at repeated tasks without embedding all behavior into static code.

Skill memory must not bypass permissions. Remembering how to do something is not permission to do it.

### Conversation Memory

Conversation memory stores relevant interaction history. It exists to preserve continuity, user preferences, unresolved tasks, and prior decisions.

Conversation memory should distinguish between user instructions, assistant suggestions, decisions, and temporary discussion.

### Knowledge Graph

The knowledge graph stores entities and relationships: people, projects, files, tasks, tools, providers, plugins, skills, preferences, and dependencies. It exists to support reasoning across connected information.

The graph should be explainable. A future user interface should be able to show why two entities are connected and where that relationship came from.

## Agent Philosophy

Agents are role-specific workers coordinated by the system. They must be accountable, inspectable, and bounded by permissions.

### CEO Agent

The CEO Agent is the future top-level coordinator. It interprets the user goal, decides whether delegation is needed, creates or updates task plans, chooses which specialized agents should help, monitors progress, and ensures final results match the user’s intent.

The CEO Agent must not become a monolith. It coordinates; it does not contain every skill.

### Specialized Agents

Specialized agents own focused responsibilities such as coding, documentation, research, testing, desktop actions, memory management, plugin management, installation planning, or automation planning.

Specialized agents should expose clear capabilities and accept explicit task inputs. They should return results, artifacts, risks, and next-step recommendations.

### Task Delegation

Delegation must be explicit. A task should include:

- A stable task ID
- Goal
- Current progress
- Completed steps
- Remaining steps
- Files involved
- Generated code
- Referenced documents
- Current provider
- Timestamp
- Relevant metadata

Delegated work should be resumable and provider-neutral.

### Agent Communication

Agents should communicate through structured task state, typed messages, shared memory interfaces, and logged decisions. They should not communicate through hidden globals, provider-specific objects, or ad hoc files.

### Task Lifecycle

The expected task lifecycle is:

1. User gives a goal.
2. CEO Agent or orchestration layer creates a task.
3. Task state is saved.
4. Work is decomposed into steps.
5. Specialized agents are assigned.
6. Progress is saved after meaningful changes.
7. Sensitive actions request permission.
8. Results are verified.
9. Final outcome, artifacts, and decisions are recorded.

## Provider Philosophy

JARVIS OS must never depend on a single AI provider.

Providers are adapters behind `BaseProvider`. The system may support OpenAI, Anthropic, Google, OpenRouter, local models, or future providers, but no provider may become architecturally privileged.

Provider requirements:

- Providers must be replaceable.
- Providers must report capabilities.
- Providers must estimate or report cost where practical.
- Providers must be selected through routing, not hardcoded by agents.
- Providers must support future failover policies.
- Providers must support future timeout and retry policies.
- Providers must allow local models in the future.
- Provider secrets must not be committed.
- Provider-specific request details must stay inside provider implementations.

The `ProviderRouter` is the correct place for future provider selection, failover, retries, timeout handling, cost tracking, capability detection, and model selection. Agents should ask the router for provider behavior rather than choosing providers directly.

## Plugin Philosophy

Every external integration must be a plugin unless it is part of the core runtime.

Plugins may integrate with applications, APIs, filesystems, browsers, desktop tools, cloud services, data sources, or specialized runtimes. They must remain isolated and permission-aware.

Plugin requirements:

- Plugins must declare their name, purpose, version, and permissions.
- Plugins must declare sensitive capabilities such as network access, file writes, shell execution, credential use, account access, installation, deletion, or automation.
- Plugins must interact through public contracts.
- Plugins must not import private internals from unrelated modules.
- Plugins must be disableable through configuration.
- Plugin failures must not crash the whole operating system unless the plugin is explicitly required.
- Plugins must log important actions through the shared logging system.
- Plugins must provide enough metadata for audit and troubleshooting.

## Security

Security is a core design concern, not an optional feature.

### Permission System

JARVIS OS must use explicit permissions for sensitive actions. Permissions should be configurable and should support future user confirmation flows.

Sensitive capabilities include:

- Shell execution
- File creation, modification, movement, or deletion
- Installer execution
- Network access
- Credential access
- Plugin activation
- Automation execution
- External account access
- Payment or purchasing actions
- Sending messages or data to third parties
- Reading private user data

### Sensitive Actions

Sensitive actions must be planned before execution. Plans should include intended commands, affected files, network targets, expected outputs, rollback options, and risks where practical.

The user should be able to approve, deny, inspect, or revise sensitive plans before execution.

### Audit Logging

Important actions must be logged in a durable, structured way. Audit logs should capture:

- Timestamp
- Actor or agent
- Action requested
- Permission used
- Files or external systems affected
- Provider used when applicable
- Outcome
- Errors or rollback actions

Audit logs must avoid storing secrets.

### Encryption Support

The architecture must support future encryption for secrets, memory, task snapshots, plugin credentials, and sensitive local data. Encryption details are not implemented yet, but storage contracts must allow encryption adapters.

### Configuration Validation

Configuration must be validated before use. Invalid log levels, malformed provider definitions, unsafe paths, missing required settings, and unsupported permission values should fail clearly.

Security-related configuration must default to safer behavior. For example, shell execution and automation should remain disabled unless explicitly enabled.

## Development Rules

These rules govern future work:

- Never rewrite working code without a clear architectural or correctness reason.
- Extend incrementally.
- Keep backward compatibility for public contracts whenever practical.
- Document all major architectural decisions.
- Add tests for core behavior.
- Add interfaces before concrete implementations when a capability must be replaceable.
- Keep AI behavior out of infrastructure modules.
- Keep provider-specific code out of agents.
- Keep plugin-specific code out of core orchestration.
- Keep platform-specific code out of provider, memory, and task contracts.
- Do not hardcode secrets or user-specific values.
- Do not add dependencies casually; each dependency must serve a clear purpose.
- Do not implement automation that bypasses permissions.
- Do not store memory without a future path for inspection and deletion.
- Prefer small, stable modules over large multipurpose classes.
- Prefer explicit typed data over loose dictionaries for public boundaries.

## Roadmap

### Version 0.1

Goal: Establish the foundation.

- Project structure
- Central configuration
- Structured logging
- Provider interfaces
- Provider router contract
- Task persistence contract
- Download manager contract
- Installer framework contract
- Documentation reader contract
- Master specification
- Basic tests for core configuration
- No AI behavior
- No automation execution

### Version 0.5

Goal: Implement usable local infrastructure.

- File-backed task persistence
- Human-readable memory storage
- Basic working memory
- Basic long-term memory
- Provider registry and router selection policy
- First real provider implementation behind `BaseProvider`
- Local model adapter prototype if practical
- Documentation reader implementations for Markdown and TXT
- Download queue implementation with progress reporting
- Installer planning without automatic execution
- Plugin manifest format and permission declarations
- Expanded configuration validation
- Audit log foundation

### Version 1.0

Goal: Deliver a dependable personal AI operating system core.

- Stable multi-agent orchestration
- CEO Agent
- Specialized coding, documentation, research, testing, and memory agents
- Provider failover and retry support
- Cost and usage tracking
- Long-term memory with review and deletion
- Semantic memory search
- Skill memory
- Conversation memory
- Permission-based automation framework
- Plugin loading and isolation
- Installer execution with confirmation, verification, rollback, and reports
- Documentation readers for Markdown, TXT, HTML, PDF, and DOCX
- Local desktop integration for Windows
- Comprehensive tests for core modules
- Security review of sensitive action flows

### Version 2.0

Goal: Mature into an extensible personal intelligence platform.

- Knowledge graph
- Advanced planning and task decomposition
- Multi-agent collaboration with structured message passing
- Local-first model support where practical
- Cross-provider optimization
- Cross-device memory and task continuity
- Mobile companion support
- Plugin marketplace or registry
- Encrypted memory and secrets support
- Rich audit and explainability UI
- Advanced automation with policy controls
- Enterprise-grade configuration profiles
- Stable public extension APIs
- Long-term backward compatibility guarantees

## Authority

When future prompts, generated code, or implementation suggestions conflict with this document, this document wins unless maintainers intentionally update it.

The purpose of JARVIS OS is not to accumulate features quickly. The purpose is to build a durable, secure, modular intelligence operating system that can grow for years without collapsing under its own complexity.
