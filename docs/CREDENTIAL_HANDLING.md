# Credential Handling

GitHub authentication may reuse a secure `gh` session or environment credential reference. Tokens, authorization headers, and credential-store data are never persisted or displayed.

`TELEGRAM_BOT_TOKEN` is a runtime reference only. Identity checks may report credential presence and bounded bot metadata, never the token value, Authorization header, or raw provider error.

Communication profiles expose only required reference names and state booleans. Tokens, webhook URLs, SMTP passwords, sessions, and authorization headers never enter message plans.

The provider registry stores credential reference names and presence booleans only. It never reads or returns values. Redaction covers API keys, bearer and bot tokens, passwords, private keys, authorization headers, cookies, session IDs, webhook secrets, OAuth and refresh tokens, SMTP passwords, and GitHub tokens.

Credentials must not appear in URLs, CLI output, provider health, history, audit, tests, configuration defaults, commits, or Vercel status. `.env` remains untouched. Future provider prompts must add provider-scoped credential loading behind existing approval and execution authorities.
