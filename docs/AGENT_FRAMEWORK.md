# Agent Framework

## Overview

The Agent Framework is the execution-layer foundation for JARVIS OS. It defines how future agents are created, registered, configured, supervised, messaged, scheduled, and observed.

This framework does not implement AI, automation, browser control, provider calls, or autonomous execution. It provides production-ready interfaces so those capabilities can be added later without redesigning the core.

## Architecture

The framework lives in `agents/` and is centered around `BaseAgent`, `AgentManager`, `AgentRegistry`, `AgentFactory`, `AgentLoader`, `AgentBus`, `AgentRouter`, `AgentScheduler`, `AgentExecutor`, `AgentSupervisor`, and `AgentOrchestrator`.

Each component has a narrow responsibility:

- `BaseAgent` defines the standard lifecycle and runtime interface.
- `AgentManager` coordinates the framework services.
- `AgentRegistry` is the source of truth for available agents.
- `AgentFactory` validates and instantiates agents.
- `AgentLoader` loads definitions in dependency-safe order.
- `AgentBus` provides in-process message and event routing.
- `AgentRouter` selects destination agents by ID or capability.
- `AgentScheduler` stores future execution metadata without running work.
- `AgentExecutor` validates execution requests and records placeholder results.
- `AgentSupervisor` reports health and recovery candidates.
- `AgentOrchestrator` accepts objectives and returns empty plan shells.

## Goals

The framework is modular, provider independent, plugin friendly, observable, recoverable, testable, and distributed-ready. It favors dependency injection and metadata contracts over direct subsystem coupling.

## Design Philosophy

Agents must never call AI providers directly. Future model work flows through `ProviderRouter`. Agents must also interact with memory, knowledge, tasks, plugins, and the Obsidian Brain through manager interfaces carried by `AgentContext`.

## Folder Structure

`agents/` contains framework primitives and `agents/examples/` contains compile-safe examples for planner, research, memory, knowledge, task, coding, browser, vision, phone, conversation, and system agents.

## Lifecycle

Every agent inherits `BaseAgent` and supports:

`initialize`, `configure`, `start`, `pause`, `resume`, `stop`, `shutdown`, `restart`, `heartbeat`, `health`, `checkpoint`, `restore`, `cleanup`, `execute`, `validate`, `load`, `unload`, `sleep`, `wake`, `on_event`, and `on_message`.

## State Machine

Lifecycle state is represented by `AgentState`. Invalid transitions raise `ValueError`. Status is separate and represented by `AgentStatus`, so operational health can differ from lifecycle position.

## Capabilities

`AgentCapability` is metadata only. It includes planning, reasoning, conversation, coding, memory, knowledge, retrieval, filesystem, browser, vision, speech, phone, robotics, automation, plugins, providers, tasks, learning, reflection, coordination, monitoring, reporting, summarization, embeddings, image generation, function calling, streaming, and custom.

## Permissions

`AgentPermission` is declarative only in this version. Enforcement will be added later. Permissions include filesystem, internet, memory, knowledge, tasks, providers, plugins, configuration, desktop, camera, microphone, notifications, clipboard, downloads, documents, system, mobile, voice, vision, and future extensions.

## Communication

`AgentMessage` defines the standard envelope for agent-to-agent communication. It includes sender, receiver, timestamp, type, priority, payload, metadata, correlation ID, request ID, timeout, retry count, and status.

## Message Bus

`AgentBus` supports in-process message handlers, event subscriptions, event publishing, broadcast, message history, and event history. It has no networking, sockets, HTTP, RPC, or distributed transport yet.

## Scheduler

`AgentScheduler` stores scheduled work in priority and waiting queues. It supports queueing, cancellation, pause, resume, retry metadata, timeout metadata, and delayed-work metadata. It does not execute work.

## Supervisor

`AgentSupervisor` reads the registry and creates health reports, including failed agents, unavailable agents, and restart candidates. It does not perform automatic recovery.

## Orchestrator

`AgentOrchestrator` accepts objectives through `AgentGoal` and returns an `AgentOrchestrationPlan`. It does not break down tasks or perform planning yet.

## Teams

`AgentTeam` stores metadata for single-agent, pair, static, dynamic, pipeline, supervisor, hierarchical, swarm, coordinator, and distributed team structures.

## Sessions

`AgentSession` stores session metadata for future conversation, task, and runtime grouping.

## Checkpoint System

`AgentCheckpoint` and `AgentCheckpointStore` define checkpoint metadata and an in-memory store. Persistent checkpoint storage can be added later without changing agent lifecycle methods.

## Metrics

`AgentMetrics` tracks execution count, failure count, restart count, recovery count, timing placeholders, message counts, task counts, queue length, health score, and future token/cost/model placeholders.

## Health

`AgentHealth` tracks health status, heartbeat, uptime, downtime, restart count, failure count, recovery count, and details. Startup health checks now include Agent Framework services.

## Plugin Integration

Plugins may later register agent definitions through `AgentManager.add_definition()` or direct registry integration. Plugin agents should declare permissions and plugin source metadata in `AgentProfile`.

## Provider Integration

Agents receive `provider_router` and the Provider Execution Manager through `AgentContext`. Multi-agent model work is prepared by `AgentOrchestrator` and executed only through the Provider Execution Manager and Provider Router. Agents never invoke provider adapters directly.

## Memory Integration

Agents receive `memory_manager` through `AgentContext`. `AgentMemoryInterface` is a thin availability wrapper and intentionally duplicates no memory logic.

## Knowledge Integration

Agents receive `knowledge_manager` through `AgentContext`. Knowledge ingestion, parsing, and search remain owned by the Knowledge Engine.

## Task Integration

Agents receive `task_manager` through `AgentContext`. `AgentTask` models future delegation metadata without executing tasks.

## Startup Integration

`StartupManager` initializes the Agent Framework after the existing core systems. Startup summary reports registered, loaded, enabled, running, healthy, disabled, and failed agents, plus scheduler, supervisor, orchestrator, bus, and health status.

## Health Checker Integration

`HealthChecker` verifies the Agent Framework, registry, manager, scheduler, router, supervisor, orchestrator, metrics, health, and bus. Results include status, message, timestamp, and future recommendation fields.

## Multi-Agent Intelligence

Executive JARVIS may invoke bounded collaboration after Reasoning when a request genuinely benefits from specialization or independent review. Simple requests stay on the ordinary provider-backed chat path.

Supported collaboration modes are sequential, parallel, review, debate, specialist panel, planner/executor, and research/verification. Every coordination has a parent request ID, coordination ID, unique subtask IDs, a validated delegation plan, minimum required context, provider and tool policy, bounded limits, normalized results, conflict records, and synthesis metadata.

The built-in planner and reviewer are provider-only, non-mutating roles. Their output is untrusted content. They cannot execute tools, mutate memory, goals, tasks, workflows, or configuration, grant permissions, or recursively create work. Provider-backed synthesis runs through the same provider gateway and discloses partial failure or unresolved disagreement.

Coordination metadata is stored under the configured agent workspace using bounded JSON records. Interrupted running records are retained as incomplete metadata and are never resumed automatically.

Commands include `multiagent status`, `multiagent list`, `multiagent show <coordination_id>`, `multiagent cancel <coordination_id>`, `multiagent limits`, and `multiagent mode off|confirm|automatic-safe|automatic`.

`confirm` requires explicit approval metadata before assessment can dispatch. `automatic-safe` is the default and permits only low-risk, non-mutating provider collaboration. No mode overrides Executive, permission, provider, workflow, or user-approval controls.

## Future Roadmap

Future releases can add plugin-provided specialist agents, richer evidence schemas, distributed message transports, and workflow-backed execution after separate authorization. Recursive autonomous delegation and unrestricted workers are intentionally unsupported.

## Extension Guide

To add a future agent:

1. Create a subclass of `BaseAgent`.
2. Define an `AgentProfile`.
3. Advertise capabilities and permissions.
4. Register the agent through `AgentManager` or a plugin.
5. Use `AgentContext` for all subsystem references.
6. Route model work through `ProviderRouter`.

## Developer Guide

Keep agents small and capability-focused. Prefer composition through context references. Avoid importing concrete subsystem internals. Add tests for lifecycle, registry behavior, permissions, health, and startup integration.

## Examples

Example agents live in `agents/examples/`. The core planner and reviewer can perform provider-backed text collaboration through the governed coordinator. They perform no automation, browser, voice, vision, tool, filesystem, or operating-system actions.

## Known Limitations

Multi-agent dispatch is synchronous and bounded; cancellation is cooperative between provider calls. Agent results carry observable provider metadata, but no hidden provider reasoning is stored. Debate conflict detection preserves differing conclusions but does not perform semantic fact verification without explicit research evidence. Distributed execution and autonomous mutation are intentionally unsupported.
