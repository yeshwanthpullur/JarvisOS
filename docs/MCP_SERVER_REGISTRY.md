# MCP Server Registry

The registry tracks bounded server manifests, transport, source, credential references, state, trust, health, tools, resources, prompts, permissions, and limitations. Duplicate IDs and over-capacity registration fail safely.

Trust is granular: unknown, blocked, reviewed, discovery, resources, or specific tools. A server cannot mutate its own registry entry or trust state. No server is registered by default.
