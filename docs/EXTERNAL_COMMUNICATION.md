# External Communication Foundation

Prompt 73 implements Telegram as the first real text transport while preserving this provider-neutral foundation. It remains disabled until explicitly configured, and independent sends require exact Phase 4 approval and Broker dispatch.

Prompt 74 adds Discord, SMTP/API email, and Slack outbound text adapters using the same egress, approval, Broker, retry, rate, duplicate, and metadata-only history policies. They are outbound-only and disabled by default.

Prompt 72 adds provider-neutral profiles, destinations, message requests/plans/validation/results, attachment metadata, rate policy, duplicate fingerprints, and a non-sending adapter contract. The existing Communication Agent remains draft-first and now exposes provider-aware planning diagnostics.

External sending is unavailable. Every future send must bind an exact provider, destination, content summary/fingerprint, attachments, permission, expiry, and Phase 4 approval before Broker dispatch. Drafting never implies sending.
