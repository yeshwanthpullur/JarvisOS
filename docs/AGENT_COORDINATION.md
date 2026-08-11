# Agent Coordination

Agents exchange immutable, session-scoped message references through the Orchestrator. Cross-session and self-delegation are blocked. Receiving agents get only required context segments, not global conversation, memory, credentials, or unrelated provider internals. Corrections create new versions/messages; conflicts retain provenance instead of overwriting unrelated state.
