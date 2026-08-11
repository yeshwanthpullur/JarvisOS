# Workflow Engine

## Prompt 82 Runtime

The existing Workflow Engine now owns a bounded long-running coordination runtime. It provides versioned workflow and step state, typed dependency edges, cycle validation, deterministic ready-step selection, bounded parallel readiness, retries, timeouts, resource counters, checkpoints, pause/resume/cancel, recovery, temporary artifact metadata, ordered audit events, health, and simulation.

The engine does not authorize or directly perform side effects. A side-effecting step must retain its approval requirement and route through the existing Execution Policy, Approval System, and Execution Broker. Background and scheduled modes are represented for planning but unrestricted execution is disabled.

CLI: `workflow status`, `list`, `show`, `graph`, `trace`, `events`, `checkpoints`, `checkpoint-show`, `pause`, `resume`, `cancel`, `simulate`, `health`, `metrics`, `cleanup-plan`, `artifact-list`, and `artifact-show`.

The Workflow Engine coordinates structured execution in JARVIS OS.

It is responsible for:
- creating workflows
- validating workflow definitions
- building execution graphs
- creating execution contexts
- dispatching steps
- tracking progress
- handling dependencies
- collecting results
- generating summaries
- storing history
- preparing recovery metadata

The Workflow Engine is orchestration-only. It does not replace the Executive Core, the Task Engine, or the Provider Router.

Context Intelligence may keep an active workflow reference so requests like `resume the workflow` can reconnect the user to the right orchestration state. Workflow remains the authoritative source of execution state.

Goal Intelligence may reference workflow state as evidence for progress, blockers, and next steps, but it does not execute workflows directly.

## Workflow Types

Supported workflow types are metadata labels:
- single step
- sequential
- parallel
- conditional
- loop
- nested
- hierarchical
- research
- planning
- task
- conversation
- agent
- provider
- hybrid
- future distributed workflow

## Execution Boundary

Workflows may coordinate conversation, planning, memory, knowledge, tasks, plugins, providers, agents, and departments.
Any provider work inside a workflow must still pass through the Provider Execution Framework and the Provider Router.
