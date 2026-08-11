# Plugin Manifest

Manifest version `1.0` requires a stable plugin ID and semantic version. It declares plugin/runtime type, capabilities, permissions, skills, agents, providers, MCP servers, credential references, network/filesystem/subprocess needs, dependencies, provenance, checksum, and signature status.

Unknown fields, malformed IDs or versions, duplicate declarations, unsupported runtimes, path traversal, absolute entrypoints, and protected skill or agent overrides fail closed. Declarations request capability; they never grant permission.
