# Template Engine

## Architecture

The Template Engine renders deterministic file templates from a blueprint and manifest context.

## Responsibilities

It renders source files, package initialization, manifests, documentation, and tests. It does not call AI, providers, or external services.

## Extension Points

Future templates can support inheritance, overrides, plugin templates, marketplace templates, and versioned template packages.

## Examples

The built-in `core_agent` template renders `__init__.py`, `agent.py`, `manifest.json`, `README.md`, and `tests.py`.

## Future Roadmap

Add persistent template discovery, compatibility matrices, and custom renderers.

## Developer Notes

Templates should remain small, deterministic, and testable.

## Known Limitations

Only the built-in in-memory template is available in this version.

