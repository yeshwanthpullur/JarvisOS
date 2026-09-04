# OpenCode Adapter

OpenCode is detected on Windows through `opencode.cmd` before less-specific executable names. The adapter performs bounded `--version` and `models` metadata discovery and does not use `--auto` or any bypass option.

Discovered model identifiers are cached for the current JARVIS process. A refresh marks models absent from the latest catalog as unavailable instead of deleting history. Alias resolution requires an exact identifier. `ox-alpha` remains unresolved when exact discovery does not prove it exists.

Model discovery is not a model call and does not authorize repository access. During verification, a harmless isolated call to an explicitly free model returned exactly `OK`, invoked no tools, and did not access or modify the repository. Unavailable network/provider state is reported as degraded rather than weakening permissions.
