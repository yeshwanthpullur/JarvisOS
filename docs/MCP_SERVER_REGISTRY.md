# MCP Server Registry

The registry loads bounded server manifests from `config.yaml`. It records transport, credential references, state, trust, health, tools, resources, prompts, permissions, and limitations. Duplicate IDs, malformed IDs, non-allowlisted executables, missing credential references, and over-capacity registration fail safely.

## Configured Server

`playwright` is registered as local stdio with `npx.cmd` as the declared launcher and `@playwright/mcp@latest` as the package reference. Installation is disabled, so JARVIS resolves only an already cached package and launches its validated `cli.js` with `node.exe`; it never asks npm to download or update the package. The server receives a restricted environment and explicit `--isolated --headless --image-responses omit` arguments. It does not connect to an existing browser profile.

Initial trust is `trusted_for_discovery`. `allowed_tools` is empty. Real verification discovered 24 tools, but none became trusted, enabled, or execution-available.

## Protocol

The official Python MCP SDK provides the local stdio lifecycle:

- initialize/handshake
- capability-aware `tools/list`, `resources/list`, and `prompts/list`
- bounded `resources/read`
- policy-gated `tools/call`
- timeout and malformed-server normalization
- deterministic shutdown and worker cleanup

Unsupported optional capabilities return an empty collection rather than failing otherwise valid discovery. External results remain untrusted data.

Trust is granular: unknown, blocked, reviewed, discovery, resources, or specific tools. A server cannot mutate its own manifest, trust, allowlist, policy, approval, or Broker decision.
