# Telegram Pairing

1. Configure `TELEGRAM_BOT_TOKEN` through the local approved credential mechanism and explicitly enable the connector. Do not place a token in source control.
2. Run `telegram pair` locally. JARVIS displays a six-digit code valid for five minutes.
3. Send `/pair <code>` from the intended private Telegram chat through the connector.
4. The connector fingerprints the chat and user identifiers, invalidates the code, and authorizes only that owner scope.
5. Use `telegram pair-status`, `telegram chats`, and `telegram auth-status` for bounded metadata. Revocation removes only the Telegram authorization.

Wrong, expired, reused, group, and channel pairing attempts are rejected. Pairing does not grant permission to execute side effects; Phase 4 approvals and the Broker still apply.
