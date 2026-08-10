# Data Egress Policy

External payloads are classified as `public`, `project_internal`, `personal`, `sensitive`, `secret`, `credential`, or `restricted`. Provider policy explicitly lists allowed classes. Prompt 71 permits no external execution, and secret, credential, and restricted egress are blocked.

Persistent Memory, transcripts, local paths, private files, browser sessions, cookies, authorization headers, and runtime databases are not provider diagnostics. Local-first routing is preferred, and a route decision never performs inference or transfer.
