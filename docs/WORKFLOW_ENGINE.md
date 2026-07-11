# Workflow Engine

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
