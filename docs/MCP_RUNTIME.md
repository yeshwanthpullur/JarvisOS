# MCP Runtime

The Phase 6 connector view keeps MCP discovery distinct from configuration, authentication, health, connection, and execution. Remote MCP and automatic server startup are disabled; discovered content remains untrusted and cannot bypass the MCP Runtime, Policy, Approval, or Broker.

Model-produced MCP requests still pass independent MCP trust, policy, approval, and Broker controls.

Plugin and MCP trust are independent: a verified plugin does not implicitly trust its MCP tools, and MCP trust does not authorize plugin code.

Prompt 76 adds a controlled MCP registry/runtime. Servers come only from trusted local configuration and begin disabled or untrusted. The runtime supports bounded discovery, capability classification, trusted resource reads, tool-call planning, lifecycle metadata, timeouts, cancellation-compatible transport boundaries, rate/concurrency policy, and content-free history.

Local stdio uses a reviewed executable and structured arguments with `shell=False` and a minimal environment. Local HTTP accepts loopback endpoints only. Remote HTTP is disabled by default and requires HTTPS plus an explicit host allowlist. No server is installed, downloaded, cloned, launched, or contacted automatically.
