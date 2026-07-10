# Agent Manifest Specification

## Architecture

Every generated agent receives a provider-independent manifest.

## Responsibilities

The manifest records agent ID, name, version, description, author, category, blueprint, template, capabilities, permissions, dependencies, configuration, health metadata, metrics metadata, compatibility version, timestamps, and manifest version.

## Extension Points

Future manifests can support signatures, encryption metadata, migration metadata, and marketplace metadata.

## Examples

`AgentManifest.to_dict()` produces JSON-safe metadata for generated packages.

## Future Roadmap

Add schema files, compatibility checks, and package signing.

## Developer Notes

Manifest data must not include secrets.

## Known Limitations

No digital signature or encryption is implemented yet.

