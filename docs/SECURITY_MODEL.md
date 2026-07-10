# Agent Creator Security Model

## Architecture

Security is declarative in this phase. Generated agents expose policy metadata and trust levels.

## Responsibilities

`SecurityManager` validates security policy metadata. `PolicyEngine` stores policies. `AuditManager` records creation and installation actions.

## Extension Points

Future work can add permission enforcement, sandboxing, signed packages, encrypted manifests, and organization policies.

## Examples

`SecurityPolicy` includes permission, capability, dependency, configuration, logging, health, metrics, rollback, and startup policies.

## Future Roadmap

Add filesystem, network, plugin, provider, execution, browser, phone, and container sandbox interfaces.

## Developer Notes

No generated agent may directly call a provider SDK.

## Known Limitations

No runtime enforcement exists yet.

