# Limitations Register

Updated: 2026-08-01

This register is the authoritative compact audit of limitations recorded from Prompts 27 through 33. A limitation is marked **fixed** only when code, tests, or manual evidence supports that conclusion. Safety boundaries and missing external capabilities remain visible rather than being presented as defects.

## Counts

| Measure | Count |
| --- | ---: |
| Total limitations audited | 26 |
| Fixed before Prompt 33.1 | 8 |
| Fixed during Prompt 33.1 | 4 |
| Fixed total | 12 |
| Still open in any form | 14 |
| Open | 5 |
| Deferred | 5 |
| Blocked | 3 |
| Experimental | 1 |

The machine-readable source is [`limitations_register.json`](limitations_register.json). Its counts are validated by tests.

## Fixed Before This Audit

| ID | Limitation | Evidence |
| --- | --- | --- |
| LIM-001 | Ordinary chat bypassed provider execution | Real Ollama chat and provider-path tests pass. |
| LIM-002 | Local AI commands could not reliably reach ProviderManager | Direct context lookup and `model_id` regression tests pass. |
| LIM-003 | Architecture placeholder or echo could replace provider output | ProviderResponse content now drives visible chat. |
| LIM-004 | SAPI synthesis did not guarantee audible playback | Direct playback and manual audible verification passed. |
| LIM-005 | Normal speech could leave permanent audio | Playback-only defaults and cleanup tests pass. |
| LIM-006 | Vercel treated CLI `main.py` as a handler | Canonical deployment is Ready and `/api/status` returns HTTP 200. |
| LIM-007 | No concise machine-readable project status | Health JSON and `project status` are tested. |
| LIM-008 | `sync conflicts` could fall into Goal Intelligence | Registered commands now dispatch first. |

## Fixed During This Audit

| ID | Limitation | Fix |
| --- | --- | --- |
| LIM-009 | Project status omitted limitation totals | Added compact fixed/open counts and register path. |
| LIM-010 | Offline STT setup guidance was fragmented | Added one safe local setup checklist to the CLI guide. |
| LIM-011 | Local vision setup guidance was fragmented | Clarified capability discovery and semantic readiness. |
| LIM-012 | Tracking language understated the sync foundation | Distinguished working local queue from unavailable remote transfer. |

## Still Open

| ID | Status | Severity | Limitation | Next Owner |
| --- | --- | --- | --- | --- |
| LIM-013 | Open | Medium | SAPI playback blocks the CLI while speaking. | Future Voice Stabilization |
| LIM-014 | Open | Medium | Paid cloud providers lack routine live verification. | Cloud Provider Validation |
| LIM-015 | Open | Medium | Production tool catalog is intentionally narrow. | Prompt 34 and later tool milestones |
| LIM-016 | Open | Medium | Automated memory retention and compaction are incomplete. | Memory Lifecycle Stabilization |
| LIM-017 | Open | Low | Vercel duplicate cleanup and protection review require dashboard action. | Manual deployment administration |
| LIM-018 | Deferred | High | Encrypted remote synchronization backend does not exist. | Future Encrypted Sync Backend |
| LIM-019 | Deferred | Medium | Autonomous plans remain advisory. | Future Governed Execution Milestone |
| LIM-020 | Deferred | Medium | Multi-agent specialist breadth is limited. | Future Agent Expansion |
| LIM-021 | Deferred | High | Web automation is not implemented. | Prompt 34 - Web Automation |
| LIM-022 | Deferred | High | Mobile automation is not implemented. | Prompt 35 - Mobile Automation |
| LIM-023 | Blocked | High | Real local voice input is unavailable. | Local STT Setup and Verification |
| LIM-024 | Blocked | High | Semantic image analysis is unavailable. | Local Vision Model Setup |
| LIM-025 | Blocked | Medium | Wake word and continuous listening are unavailable. | Future Voice Input Milestone |
| LIM-026 | Experimental | Medium | Local web interface remains experimental. | Dedicated Interface Stabilization |

## Interpretation

- **Open** means useful work remains but does not require starting the next major roadmap milestone.
- **Deferred** means the work belongs to a named future milestone or requires a substantial new capability.
- **Blocked** means a model, dependency, adapter, service, or explicit setup step is missing.
- **Experimental** means the capability exists but is not the recommended primary experience.

The CLI remains primary. Online deployment remains a safe status foundation only. Local queueing does not imply remote sync, image metadata does not imply semantic vision, and voice command architecture does not imply working microphone transcription.
