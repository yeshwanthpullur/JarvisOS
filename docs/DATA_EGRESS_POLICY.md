# Data Egress Policy

Outbound messages use the same classes. Secret, credential, and restricted messages are blocked; personal and sensitive content would require explicit warning and approval once a provider exists.

External payloads are classified as `public`, `project_internal`, `personal`, `sensitive`, `secret`, `credential`, or `restricted`. Provider policy explicitly lists allowed classes. Prompt 71 permits no external execution, and secret, credential, and restricted egress are blocked.

Persistent Memory, transcripts, local paths, private files, browser sessions, cookies, authorization headers, and runtime databases are not provider diagnostics. Local-first routing is preferred, and a route decision never performs inference or transfer.
