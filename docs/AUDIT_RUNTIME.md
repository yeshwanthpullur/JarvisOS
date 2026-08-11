# Audit Runtime

Security-relevant metadata is recorded as ordered, immutable dataclasses linked by SHA-256 digests. Corrections append a new record; existing records are not edited.

History is bounded in memory by retention configuration. Records contain safe references and outcomes, never credential values, payloads, source contents, transcripts, or private absolute paths. Search is read-only and bounded.

The Audit Runtime observes. It cannot approve, deny, execute, recover, or change policy.
