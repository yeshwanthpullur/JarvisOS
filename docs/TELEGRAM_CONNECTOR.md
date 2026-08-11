# Telegram Connector

Prompt 73 adds JARVIS OS's first real external conversational transport. It uses the Telegram Bot API through a fixed HTTPS endpoint and supports bounded text, explicit private-chat pairing, duplicate suppression, rate limits, deterministic chunking, and an explicitly controlled long-poll lifecycle.

The connector is implemented but disabled and unconfigured by default. `TELEGRAM_BOT_TOKEN` is read only at runtime through the approved credential reference. The token is never printed, persisted, audited, returned by status commands, or exposed through Vercel. No model or Telegram library is downloaded.

Inbound text passes update validation, private-chat authorization, replay protection, normalization, the Communication Gateway, Conversation Intelligence, Prime routing, and existing subsystem policy. Telegram content is untrusted user input and cannot alter system policy, permissions, credentials, or approval state.

Normal replies may return only to the originating authorized chat. Independent outbound text requires an exact, non-expired Phase 4 approval and must pass the Execution Broker's `telegram_send_tool`. Critical actions remain blocked. Telegram does not create a separate approval store or execution path.

Use `telegram status`, `telegram identity`, `telegram pair`, `telegram polling-status`, `telegram start`, and `telegram stop`. Starting validates enablement, credential presence, bot identity, and at least one authorized chat. Polling is bounded and explicit; no service, startup task, permanent daemon, webhook, or Vercel route is installed.

Attachments, voice, video, groups, channels, webhook ingress, bulk delivery, scheduled delivery, contact access, and arbitrary Bot API methods remain disabled.

