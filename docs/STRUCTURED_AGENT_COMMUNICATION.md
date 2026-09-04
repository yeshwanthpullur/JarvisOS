# Structured Agent Communication

External worker communication uses immutable messages of type `FINDING`, `QUESTION`, `REQUEST`, `ARTIFACT`, `BLOCKER`, `REVIEW`, `REJECTION`, `APPROVAL_REQUEST`, or `COMPLETION_CLAIM`.

Each message declares session, task, sender, receiver, opaque payload reference, trust, privacy scope, correlation ID, and timestamp. Cross-session messages, self-routing, secret-shaped payloads, and oversized references are rejected. Completion claims require evidence references and are not trusted merely because a worker produced them.

Messages do not carry full prompts, files, credentials, memory content, transcripts, or model output. Existing Approval and Broker events remain authoritative for execution decisions.

