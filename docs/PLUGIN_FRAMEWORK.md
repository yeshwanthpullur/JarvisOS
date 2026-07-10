# Plugin Framework

The Plugin Framework is the official extension system for JARVIS OS. Future capabilities such as browser control, camera access, voice, GitHub, email, calendar, phone, downloader, PDF, and YouTube support should be implemented as plugins when they do not belong in the core runtime.

## Design Goals

- Keep core lightweight.
- Allow capabilities to be installed, validated, loaded, enabled, disabled, reloaded, unloaded, and removed through one lifecycle.
- Require every plugin to declare metadata, permissions, dependencies, configuration, and compatibility version.
- Give plugins stable public contracts instead of private access to internals.
- Keep permission checks explicit before sensitive capability use.

## Plugin Layout

A plugin is a folder inside the configured `plugins.plugin_dir`. It must contain a `plugin.json` manifest.

Example:

```text
plugins/example_hello/
  plugin.json
  plugin.py
```

## Manifest Fields

Every plugin manifest must include:

- `name`
- `id`
- `version`
- `author`
- `description`
- `permissions`
- `dependencies`
- `configuration`
- `compatibility_version`
- `entry_point`

The entry point uses `module:ClassName`, for example `plugin:HelloPlugin`.

## Lifecycle

The framework supports:

- discover
- validate
- load
- initialize
- enable
- disable
- reload
- unload
- remove

Physical installation and deletion are represented by interfaces and intentionally left for future implementation.

## Permissions

Supported permissions are:

- filesystem
- internet
- camera
- desktop
- clipboard
- downloads
- notifications
- microphone
- system
- browser
- mobile
- memory
- knowledge
- tasks

Plugins receive a `PluginContext` and must call `context.require_permission(...)` before performing permissioned work.

## Dependencies

Plugin dependencies are declared by plugin ID. Missing dependencies are detected during validation. Plugins with dependencies load only after their dependencies are loaded.

## Startup Integration

`StartupManager` initializes `PluginManager`, discovers plugins from the configured plugin directory, and displays loaded, enabled, and invalid plugin counts.

## Current Limitations

- Plugin installation and physical removal are future behavior.
- Plugins run in-process in this foundation.
- Manifest parsing uses JSON to avoid requiring PyYAML.
- No browser, camera, voice, downloader, GitHub, AI provider, or automation plugin is implemented here.
