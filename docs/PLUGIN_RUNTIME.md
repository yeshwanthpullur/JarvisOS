# Secure Plugin Runtime

Model-provider plugins may register metadata but cannot bypass model/provider registries, endpoint policy, or runtime readiness checks.

Prompt 77 adds a metadata-first extensibility boundary. Strict manifests enter the Plugin Registry, where provenance, compatibility, integrity, dependencies, credentials, capabilities, permissions, and protected-name collisions are checked before enablement can be planned.

External plugins default to `untrusted` and disabled. The runtime does not dynamically import external Python, install dependencies, clone repositories, launch packages, execute arbitrary code, update plugins, schedule plugins, or grant requested permissions. Declarative metadata may be enabled only after integrity verification and exact approval; executable runtimes remain disabled.

Plugin capabilities flow through local policy, the Skill and Agent registries, the Approval System, and the Broker. A plugin may add capability but cannot grant authority, replace Prime or security authorities, write memory directly, or treat its own output as trusted instructions.

Use `plugin status`, `plugin list`, `plugin show`, `plugin inspect`, `plugin capabilities`, `plugin permissions`, `plugin dependencies`, `plugin health`, `plugin verify`, and `plugin history`. Enable, disable, install, update, and uninstall commands are approval-bound plans or disabled execution surfaces.
