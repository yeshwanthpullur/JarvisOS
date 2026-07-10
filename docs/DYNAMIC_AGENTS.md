# Dynamic Agents

## Architecture

Dynamic Agents are optional agents created after deployment.

## Responsibilities

`DynamicAgentRegistry` tracks generated agents, installation state, enablement, lifecycle, search, archive, and metadata.

## Extension Points

Future dynamic agents can support import, export, cloning, upgrades, marketplace packages, and runtime loading.

## Examples

The installer records generated dynamic agents without modifying core modules.

## Future Roadmap

Add persisted registry storage, package import/export, and runtime loading.

## Developer Notes

Dynamic Agents must never bypass the Agent Framework.

## Known Limitations

Runtime loading and hot reload are not implemented.

