# Retrieval Engine

The Retrieval Engine is the precision lookup layer above storage.

It does not store memory or knowledge. Instead, it decides how to retrieve the exact information required for a request.

Personal Intelligence uses this layer to pull only the relevant preferences, project references, and supporting evidence instead of injecting the full user profile into every request.

Context Intelligence uses Retrieval only as a selective support layer when active session state is insufficient. Active continuity remains conversation-scoped first, while Retrieval remains responsible for bounded relevance-based recovery rather than full-history injection.

Goal Intelligence uses Retrieval to gather only the goal, milestone, task, workflow, research, memory, knowledge, and personal evidence relevant to the current goal analysis.

Responsibilities:
- receive retrieval requests
- determine retrieval strategy
- determine required sources
- query memory
- query knowledge
- merge results
- rank results
- validate results
- build references
- return structured responses

## Execution Boundary

Executive JARVIS decides what information is needed. The Retrieval Engine decides how to retrieve it. Memory and Knowledge remain the only storage systems.
