# Execution Broker

The Orchestrator has no executor and cannot route around the Broker. Side effects still require policy validation, exact approval where applicable, capability/permission checks, and the owning executor.

Model runtime start is registered as a controlled capability; Prompt 78 exposes planning only and no new executor.

There is no direct agent-to-plugin execution path. Any future side-effecting plugin executor must register an exact Broker tool.

Only specifically trusted/classified MCP side-effect tools may route through `mcp_executor`; server metadata alone never registers authority.

Issue create/comment, PR create/comment, and release create each have an action-specific network Broker tool; direct mutation cannot bypass validation.

Prompt 73 registers `telegram_send_tool` for bounded text egress. Independent sends require `send_message` and `network_access` permissions plus exact approval; direct adapter bypass is unsupported.

Communication dry runs never dispatch. Future provider `send()` calls must enter through this Broker after exact approval and policy validation.

The broker is the single policy checkpoint for controlled execution. It validates system readiness, execution mode, risk, permissions, exact approval scope, and executor availability. It returns structured blocked, dry-run, ready, completed, or failed results.

The broker does not discover tools dynamically, install dependencies, run arbitrary plugins, or bypass subsystem policies. Diagnostics are available through `broker status`, `broker validate <action>`, and `broker dry-run <action>`.
