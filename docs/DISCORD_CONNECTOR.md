# Discord Connector

Prompt 74 adds outbound-only Discord text through an explicitly configured bot transport. Channel references must be explicit; server, member, and channel enumeration are unavailable. Inbound events, DMs, webhooks, attachments, embeds, reactions, threads, voice, moderation, broad mentions, and scheduled sends remain disabled.

`DISCORD_BOT_TOKEN` is a runtime credential reference and is never displayed or persisted. Every send requires exact provider, destination, content fingerprint, permissions, expiry, Approval System validation, and `discord_send_tool` Broker dispatch. The connector is implemented but disabled and unconfigured by default.

