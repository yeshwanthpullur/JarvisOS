# Slack Connector

Prompt 74 adds outbound-only Slack text through an explicitly configured bot API. Destinations are explicit channel references or future local aliases; workspace/member enumeration and arbitrary user discovery are unavailable. Inbound events, DMs, threads, attachments, reactions, uploads, channel management, webhooks, and scheduled sends remain disabled.

`SLACK_BOT_TOKEN` is a runtime credential reference and never appears in output or history. Every send requires exact approval and `slack_send_tool` Broker dispatch. The connector is implemented but disabled and unconfigured by default.

