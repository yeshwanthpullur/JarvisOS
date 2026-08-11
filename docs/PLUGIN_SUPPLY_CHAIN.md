# Plugin Supply Chain

Plugin provenance records source type/reference, publisher, version, commit/tag, SHA-256, signature status, and retrieval time. Repository popularity is not trust.

Discovery never executes install scripts, package-manager hooks, downloaded binaries, or arbitrary build commands. Dependencies are recorded and checked but never installed automatically. Updates require a new review of integrity, permissions, dependencies, compatibility, and rollback before separate approval.
