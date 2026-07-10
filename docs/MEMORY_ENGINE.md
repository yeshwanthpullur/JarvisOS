# Memory Engine

Memory remains the permanent structured store for JARVIS OS. Reflection does not duplicate memory storage; it only prepares learning metadata and references that can later be captured by Memory or Knowledge through existing interfaces.

The Memory Engine stores persistent structured memory in SQLite.

It is the storage layer for memories, sessions, projects, tags, and relationships.

## Responsibilities

- create memory records
- update memory records
- delete memory records
- search memory records
- list memory records
- load memory records
- count memory records

## Retrieval Boundary

The Retrieval Engine may query memory, but it does not replace the Memory Engine or add a second storage system. Memory remains the source of truth for persistent memory records.
