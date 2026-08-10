# Credential Handling

The provider registry stores credential reference names and presence booleans only. It never reads or returns values. Redaction covers API keys, bearer and bot tokens, passwords, private keys, authorization headers, cookies, session IDs, webhook secrets, OAuth and refresh tokens, SMTP passwords, and GitHub tokens.

Credentials must not appear in URLs, CLI output, provider health, history, audit, tests, configuration defaults, commits, or Vercel status. `.env` remains untouched. Future provider prompts must add provider-scoped credential loading behind existing approval and execution authorities.
