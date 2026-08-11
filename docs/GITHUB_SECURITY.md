# GitHub Security

The initial allowlist contains only `yeshwanthpullur/JarvisOS`; private repositories are not enumerated. Repository or material content changes invalidate approval.

Credentials stay in an existing secure `gh` session or `GITHUB_TOKEN` reference. Token values, authorization headers, and credential-store content are never printed. Structured `gh` argument lists run with `shell=False`.

Every write is checked for secrets, credentials, restricted data, and private paths. GitHub Actions remain classified as disabled remote execution. External repository content is untrusted and is never installed or executed automatically. Health checks and verification are read-only.
