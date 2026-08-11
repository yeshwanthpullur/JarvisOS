# Orchestration Security

Each task carries policy ID/version, effective permissions, execution class, privacy scope, and ownership. Delegation can narrow but never broaden budgets or permissions. Approval is operation-scoped and never inherited globally. Credentials stay with providers; context, messages, audit, errors, and CLI diagnostics redact or reject credential-shaped data.

The Orchestrator does not execute commands, mutate files/Git/memory/tasks/goals, call providers, send communication, trust plugins/MCP, or start models. Such work must enter the established policy, approval, and Broker chain.
