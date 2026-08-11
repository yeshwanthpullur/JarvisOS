# Disaster Recovery Plan

Recovery remains operator-controlled and preserves Policy, Approval, Broker, and Governance boundaries.

| Event | Detection | Safe response | Restricted action |
|---|---|---|---|
| Runtime interruption | Health and process diagnostics | Stop cleanly, inspect bounded state, restart explicitly | No hidden restart loop |
| Provider outage | Provider health and circuit state | Degrade, use a configured local fallback, or report unavailable | No implicit cloud route |
| Workflow interruption | Checkpoint and workflow status | Validate checkpoint, produce recovery plan, resume explicitly | No unauthorized side effects |
| Resource exhaustion | CPU/RAM/queue thresholds | Pause or reject work and reduce bounded load | No limit bypass |
| Configuration corruption | Schema/config validation | Restore reviewed configuration from trusted version control | Never restore secrets automatically |
| Knowledge index damage | Integrity/provenance checks | Rebuild from explicitly admitted sources | Do not promote to Memory |
| Governance/audit issue | Hash-chain and policy checks | Preserve evidence, open bounded incident, require operator review | No audit rewrite |

Configuration, knowledge indexes, workflow metadata, governance metadata, and audit metadata require separately protected backups. Secrets, tokens, runtime sessions, and private payloads are not included in repository backups. Rollback feasibility must be reviewed per schema and cannot be assumed for external side effects.
