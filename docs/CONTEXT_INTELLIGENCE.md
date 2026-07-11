# Context Intelligence

Context Intelligence gives JARVIS practical continuity across related interactions without introducing a second conversation, task, workflow, or memory system.

## Purpose

It tracks the minimum active state needed for requests such as:

- `Continue.`
- `Go back to the previous project.`
- `What were we doing?`
- `Resume the workflow.`
- `Use the previous one.`

## Architecture

- Conversation Engine owns the conversation session.
- Context Intelligence manages active context, recent context history, pending continuation state, and reference resolution inside that session.
- Executive JARVIS receives only the resolved context that is relevant for the current request.
- Memory remains the durable structured-memory authority.
- Retrieval remains the selective recovery layer when active state alone is insufficient.
- Personal Intelligence remains responsible for durable user-specific information.
- Task Intelligence, Workflow, and Research remain authoritative for their own records and execution state.

## Context Types

The current implementation supports lightweight references for objectives, project references, workflow references, research references, pending state, continuation state, and recent results.

## Active Context

Active context includes the current objective, current primary work item, recent contexts, pending clarification or next-step metadata, unresolved-question metadata, last meaningful action, and last meaningful result.

## Reference Resolution

Resolution prefers:

1. current explicit instruction
2. current explicit entity
3. active context
4. recent compatible context
5. authoritative task, workflow, and research references
6. relevant personal context

If more than one plausible candidate remains, JARVIS asks for clarification instead of guessing.

## Continuation

Continuation is grounded in actual state. The current implementation checks pending clarification, pending next-step metadata, active project context, active workflow context, and recent research context.

## Boundaries

- Personal Intelligence owns durable user-related context.
- Task Intelligence owns project and goal records.
- Workflow owns workflow state.
- Research owns research state and findings.
- Context Intelligence stores only references and continuity metadata.

## User Control

The existing command engine exposes:

- `context show`
- `context recent`
- `context clear`
- `context pause`
- `context resume`
- `context previous`
- `objective show`

## Limitations

- Context continuity is primarily session-scoped today.
- Retrieval support is intentionally lightweight and selective.
- The implementation prefers clarification over aggressive inference.
