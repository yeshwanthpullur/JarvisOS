# Agent Creator Framework

## Architecture

The Agent Creator is the manufacturing subsystem for future JARVIS OS agents. It composes blueprints, templates, manifests, validation, generation plans, installation metadata, rollback plans, catalog entries, departments, policy metadata, and audit records.

## Responsibilities

- Create generation plans from blueprints.
- Render deterministic templates.
- Validate manifests, templates, and generated files.
- Install generated agents through explicit installer interfaces.
- Track generated agents in registries and catalogs.
- Expose startup and health statistics.

## Extension Points

Future extensions can add blueprint packages, template packages, custom validators, installers, policy engines, marketplace metadata, and AI-assisted generation through public contracts.

## Examples

Use `AgentCreator.create_preview()` for non-mutating generation and `install_generated()` for installation metadata.

## Future Roadmap

Future releases can add persisted catalogs, signed packages, visual builders, marketplace support, and AI-assisted generation routed through ProviderRouter.

## Developer Notes

The creator does not bypass the Agent Framework. Generated agents must inherit `BaseAgent`.

## Known Limitations

This version is architecture-first. It does not implement AI code generation or autonomous modification.

