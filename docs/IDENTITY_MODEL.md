# Identity Model

Identity types include users, agents, providers, plugins, MCP servers, runtimes, workflows, services, and future external identities. Authentication, authorization, roles, trust, and privacy scope remain separate fields.

Roles compose explicit permissions and restrictions. Effective delegated permissions are intersected with parent permissions, enforcing least privilege without implicit inheritance gains.

The foundation does not implement external authentication or identity federation.
