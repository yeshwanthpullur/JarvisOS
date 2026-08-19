# MCP Security

MCP expands capability, never authority. Server metadata cannot grant permissions, change trust, approve actions, expose unrelated credentials, alter system instructions, or bypass Executive JARVIS, Prime, Execution Policy, Approval, Broker, Governance, or Workflow controls.

## Defaults

- Local stdio and validated localhost HTTP may be configured.
- Remote HTTP, package installation, scheduled execution, prompts, and all tool execution are disabled.
- Resource reads require both policy permission and resource-level trust.
- Credential names are references; values are passed only to the one configured process that requires them.
- The host environment is reduced to operating-system process essentials plus explicit credential references.
- Shell evaluation, arbitrary executables, logged-in browser profiles, filesystem escape, and server self-authorization are blocked.

Discovery classifies tools using names, descriptions, and MCP read-only/destructive annotations. Classification is advisory and never creates trust. Unknown and critical tools remain execution-disabled. An allowlisted read-only tool still cannot be called while `allow_tool_execution=false`.

If tool execution is enabled by a future explicit policy, side effects bind approval to server, tool, input fingerprint, permission, and expiry before routing through the Execution Broker. Secret-shaped, credential, restricted, oversized, and malformed payloads fail closed. External tool/resource/prompt content is bounded untrusted data with provenance, not instruction authority.

Playwright MCP is discovery-only. It uses an isolated headless context, does not save a session, receives no browser-profile path, and has no trusted tools. Explicit discovery may start its local process; shutdown always stops it.
