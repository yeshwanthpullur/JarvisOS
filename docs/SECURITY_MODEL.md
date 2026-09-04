# Agent Creator Security Model

## External Worker Boundary

Optional external workers are untrusted subprocess peers, not JARVIS authorities. Metadata discovery is bounded to safe executable, version, and catalog commands. Worker planning cannot mutate repositories; writes require isolated worktrees plus existing Approval, Policy, Broker, and Git controls. Cloud credentials are symbolic references only, external outputs require validation, completion claims require evidence, and personal context is withheld by default. No bypass flags, unrestricted permissions, automatic merge, secret reads, or hidden worker background loops are enabled.

## Architecture

The legacy Agent Creator descriptors remain declarative, while actual side effects elsewhere in JARVIS are governed by Execution Policy, exact Approval records, the Execution Broker, subsystem executors, and audit controls. The external-worker facade adds no authority of its own.

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

Agent Creator metadata alone does not provide a process sandbox. External-worker execution is therefore disabled in this foundation; any future execution must reuse the existing enforced Approval, Policy, Broker, Git, and workspace boundaries.
