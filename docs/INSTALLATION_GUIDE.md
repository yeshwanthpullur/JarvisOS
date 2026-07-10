# Agent Installation Guide

## Architecture

The installer accepts generated build plans and records installation metadata.

## Responsibilities

It validates target files, prepares rollback metadata, optionally writes generated files, updates the dynamic registry, and updates the catalog.

## Extension Points

Future installers can support upgrades, reinstall, uninstall, rollback execution, compatibility reports, and package verification.

## Examples

`AgentInstaller.install(plan, destination_root, write_files=False)` records metadata without writing files.

## Future Roadmap

Add physical uninstall, migration, package verification, and signing.

## Developer Notes

Installers must never modify unrelated modules.

## Known Limitations

Rollback execution is metadata-only.

