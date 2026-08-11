# External Communication Foundation

Prompt 72 adds provider-neutral profiles, destinations, message requests/plans/validation/results, attachment metadata, rate policy, duplicate fingerprints, and a non-sending adapter contract. The existing Communication Agent remains draft-first and now exposes provider-aware planning diagnostics.

External sending is unavailable. Every future send must bind an exact provider, destination, content summary/fingerprint, attachments, permission, expiry, and Phase 4 approval before Broker dispatch. Drafting never implies sending.
