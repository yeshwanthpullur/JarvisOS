# Agent Registry

The repository agent registry and diagnostics are authoritative for runtime agent metadata. This note records the project-memory boundary only.

- Agents are resources, not authorities.
- External workers remain execution-disabled unless an existing approved path grants authority.
- Registry state must remain bounded and free of secrets and private paths.
