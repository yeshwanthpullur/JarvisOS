# Agent Protocol and Registry

## Phase 3 Batch 2

`document_agent`, `browser_agent`, `scheduler_agent`, `communication_agent`, `adapter_agent`, and `evaluation_agent` are truthful foundations. Their modes are text-only/plan-only, read-only, plan-only without a runner, draft-only, manifest-only, and local-only. `model_agent` exposes advanced-provider planning while all advanced runtimes remain unavailable.

Updated: 2026-08-10

JARVIS OS now has a typed, local-first registry for governed agent metadata. The registry describes agents, capabilities, risk, permissions, approval requirements, health, requests, decisions, and results. It does not launch autonomous workers or grant new authority.

## Safety Model

- The default execution mode is `plan_only`.
- Side effects and permissions are declared on every capability.
- High-risk capabilities require approval; critical future capabilities are blocked.
- Disabled and unavailable agents remain visible for honest diagnostics but cannot execute.
- Agent requests reference bounded context and memory identifiers; they do not mutate Persistent Memory.
- Diagnostics contain metadata only and omit prompts, memory content, transcripts, local paths, and credentials.

## Registered Specialists

Current or foundation entries cover conversation, memory, vision, image workflows, video workflows, read-only web inspection, local sync diagnostics, explicit voice controls, project health, limitations, model routing, safe system metadata, the plan-only Research Agent, and the plan-only Coding Agent.

Future entries cover MCP gateways, documents, browser writes, communication, workflows, robotics, drones, and social media. These entries are disabled or unavailable and explain what is missing. Their presence is a planning contract, not a capability claim. `research_agent` is enabled for bounded planning and evidence summaries, while autonomous source retrieval remains unavailable. `coding_agent` is enabled for bounded plans and read-only repository metadata; code edits, commands, commits, pushes, and dependency installation remain disabled.

## Commands

Use `agent status`, `agent list`, `agent capabilities`, `agent show <name>`, `agent find <capability>`, and `agent diagnostics`. Filtered diagnostics are available through `agent ready`, `agent unavailable`, `agent future`, `agent risks`, and `agent approvals`.

No agent command executes tools, contacts a provider, starts a worker, or changes user data.
