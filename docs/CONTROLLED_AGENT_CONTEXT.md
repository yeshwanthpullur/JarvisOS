# Controlled Agent Context

Context shared with external workers is separated into session, task, project, knowledge, and personal-reference scopes. Every fragment is an opaque reference with provenance, trust classification, and a character budget.

Selection follows least context: callers choose allowed scopes and a bounded item count. Personal references are excluded by default and require both explicit personal classification and an explicit allow decision. This layer never copies raw Persistent Memory, private files, transcripts, credentials, or complete conversation history into worker diagnostics.

The default store permits 64 fragments and 12,000 aggregate reference-budget characters. Exceeding either bound fails safely.

