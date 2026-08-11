# Telegram Security

Telegram is an interface, not an authority. Unknown users and groups cannot control JARVIS. The first user is never trusted automatically: a local CLI pairing code is short-lived, single-use, compared by fingerprint, and accepted only from a private chat. Runtime authorization stores pseudonymous references rather than profile details.

Independent sends are data egress and require exact approval for the Telegram action, destination reference, permissions, and resource scope. The Broker remains the only dispatch authority. Duplicate updates cannot create duplicate side effects, duplicate sends are suppressed, and provider retries remain bounded. Token, message bodies, raw updates, and private paths are excluded from bounded history.

The connector accepts text only. Unsupported media is not downloaded. Webhooks, group chats, channels, scheduled sends, hidden background polling, and public Vercel execution endpoints are disabled. Telegram messages cannot request `.env`, credentials, arbitrary shell execution, force pushes, or approval bypasses.

