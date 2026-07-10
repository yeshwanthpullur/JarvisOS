# Executive JARVIS Core

JARVIS is the permanent Executive Intelligence layer of JARVIS OS. It is not an agent. Every future request enters JARVIS first, then flows through intent detection, decision metadata, reasoning, retrieval planning, task intelligence, research intelligence, planning, workflow orchestration, dispatch, existing managers, response building, and history.

JARVIS never talks directly to AI providers. Provider work must route through the existing Provider Router.

The Conversation Engine and Command Engine now provide the user-facing operating interface for Executive JARVIS. CLI input flows through conversation context, command parsing or request handling, and then into the Executive pipeline.

## Responsibilities

- Receive requests
- Build execution context
- Identify intent
- Decide strategy
- Prepare plans
- Decide what information must be retrieved
- Create and coordinate workflows
- Dispatch to existing systems
- Coordinate memory, knowledge, tasks, plugins, tools, skills, departments, agents, and providers
- Compose responses
- Track metrics, health, diagnostics, history, and recovery metadata

## Workflow Boundary

JARVIS creates workflow definitions and hands execution to the Workflow Engine. The Workflow Engine manages workflow scheduling, checkpoints, recovery, and history. Provider execution inside a workflow must continue to flow through the Provider Execution Framework and Provider Router.

JARVIS also decides which information should be retrieved. The Retrieval Engine is responsible for precision lookup, ranking, and reference building across memory, knowledge, Obsidian, and historical sources.

## Current Limitations

This foundation contains architecture only. It does not implement AI calls, browser automation, desktop automation, voice, vision, internet automation, or autonomous execution.
