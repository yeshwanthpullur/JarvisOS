# Retrieval Engine

The Retrieval Engine is the precision lookup layer above storage.

It does not store memory or knowledge. Instead, it decides how to retrieve the exact information required for a request.

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
