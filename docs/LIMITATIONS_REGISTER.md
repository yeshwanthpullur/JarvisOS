# Limitations Register

Updated: 2026-08-05

This register is the authoritative compact audit of limitations reviewed through Prompt 42. A limitation is marked **fixed** only when code, tests, or manual evidence supports that conclusion. Safety boundaries and missing external capabilities remain visible rather than being presented as defects.

## Counts

| Measure | Count |
| --- | ---: |
| Total limitations audited | 47 |
| Fixed before Prompt 41 | 22 |
| Fixed during Prompt 41 | 1 |
| Fixed during Prompt 42 | 1 |
| Fixed total | 24 |
| Still open in any form | 23 |
| Open | 4 |
| Deferred | 16 |
| Blocked | 3 |
| Experimental | 1 |

The machine-readable source is [`limitations_register.json`](limitations_register.json). Its counts are validated by tests.

## Fixed Outside Prompt 37

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
| LIM-009 | Project status omitted limitation totals | Compact counts and register path are data-backed. |
| LIM-010 | Offline STT setup guidance was fragmented | The CLI guide has a safe local setup checklist. |
| LIM-011 | Local vision setup guidance was fragmented | Capability discovery and semantic readiness are distinct. |
| LIM-012 | Tracking language understated the sync foundation | Local queue and unavailable remote transfer are distinct. |
| LIM-013 | SAPI playback blocked the CLI while speaking | Long Windows SAPI replies now use a tested background worker with immediate stop/resume/cancel controls. |
| LIM-030 | Video editing workflow was not implemented | Prompt 42 added a governed local-first video editing workflow foundation with prompt validation, safety review, provider abstraction, dry-run planning, bounded metadata, truthful unavailable-provider handling, and CLI commands. |
| LIM-021 | Web automation had no governed foundation | Prompt 34 added strict policy, permissions, read-only commands, normalized results, bounded audit, and a truthful fallback adapter. |
| LIM-028 | Web automation had no live read-only inspection or redirect verification | Prompt 34.1 added bounded standard-library inspection and redirect validation. |
| LIM-022 | Mobile automation had no governed foundation | Prompt 35 added planning-only policy, adapters, commands, and redacted audit. |
| LIM-023 | Real microphone STT was unavailable on the current machine | Vosk, a microphone, and an Indian-English local model passed manual `voice listen send` verification. |
| LIM-024 | Real semantic image analysis required an installed local vision model | Local Ollama LLaVA image analysis and image Q&A passed manual verification. |
| LIM-040 | Local voice input had no executable offline STT/capture path | Prompt 36 added lazy Vosk recognition, explicit in-memory capture, normalized results, and safe CLI handoff. |
| LIM-041 | Vision had no explicit governed local Ollama analysis workflow | Prompt 37 added model capability discovery, Provider Router image execution, safety policy, bounded metadata-only audit, and complete CLI controls. |
| LIM-047 | Free-form chat lacked bounded multi-turn conversation intelligence | Prompt 39 added bounded topics, entities, follow-ups, references, clarification, repair, modes, confidence, and summaries. |

## Fixed During Prompt 41

| ID | Limitation | Fix |
| --- | --- | --- |
| LIM-029 | Image generation workflow was not implemented | Prompt 41 added a governed local-first image workflow foundation with prompt validation, safety review, provider abstraction, dry-run planning, bounded metadata, truthful unavailable-provider handling, and CLI commands. |

## Still Open

| ID | Status | Severity | Limitation | Next Owner |
| --- | --- | --- | --- | --- |
| LIM-014 | Open | Medium | Paid cloud providers lack routine live verification. | Cloud Provider Validation |
| LIM-015 | Open | Medium | Production tool catalog is intentionally narrow. | Prompt 34 and later tool milestones |
| LIM-017 | Open | Low | Vercel duplicate cleanup and protection review require dashboard action. | Manual deployment administration |
| LIM-018 | Deferred | High | Encrypted remote synchronization backend does not exist. | Future Encrypted Sync Backend |
| LIM-019 | Deferred | Medium | Autonomous plans remain advisory. | Future Governed Execution Milestone |
| LIM-020 | Deferred | Medium | Multi-agent specialist breadth is limited. | Future Agent Expansion |
| LIM-025 | Blocked | Medium | Wake word and continuous listening are unavailable. | Future Voice Input Milestone |
| LIM-026 | Experimental | Medium | Local web interface remains experimental. | Dedicated Interface Stabilization |
| LIM-027 | Deferred | High | Interactive and sensitive web actions are unavailable. | Future Governed Interactive Web Automation |
| LIM-031 | Deferred | High | Cross-device synchronization is unavailable. | Prompt 44 - Cross-Device Sync |
| LIM-032 | Deferred | Medium | Dedicated Raspberry Pi and hardware support is not implemented. | Existing future hardware-support milestone |
| LIM-033 | Deferred | Medium | Dedicated study assistant workflow is not implemented. | Prompt 38 - Study Assistant and Research Workflows |
| LIM-034 | Deferred | High | Advanced Builder Mode is not formalized. | Future Advanced Builder / Coding Workflow Foundation |
| LIM-035 | Deferred | High | Call and communication assistance is not implemented. | Prompt 47 - Safe Communication and Call Assistance Foundation |
| LIM-036 | Deferred | High | Unified personal multi-tool workspace is not implemented. | Prompt 49 - Personal Workspace / Multi-Tool Replacement Layer |
| LIM-037 | Deferred | High | No real phone adapter or live mobile control exists. | Future Governed Mobile Adapter |
| LIM-038 | Deferred | High | No approval-gated mobile actions exist. | Future Governed Mobile Actions |
| LIM-039 | Deferred | Medium | No trusted phone companion app exists. | Future Mobile Companion |
| LIM-042 | Deferred | High | Live camera and real-time video vision are unavailable. | Future Explicit Camera and Video Safety Milestone |
| LIM-043 | Blocked | High | Identity recognition and sensitive-trait inference are blocked. | Permanent Safety Boundary |
| LIM-044 | Deferred | Medium | Cloud and Vercel vision execution are unavailable. | Future Optional Cloud Vision Review |
| LIM-045 | Open | Medium | OCR accuracy is not guaranteed. | Future OCR Evaluation |
| LIM-046 | Blocked | High | Medical diagnosis and legal or forensic certainty are blocked. | Permanent Safety Boundary |

## Interpretation

- **Open** means useful work remains but does not require starting the next major roadmap milestone.
- **Deferred** means the work belongs to a named future milestone or requires a substantial new capability.
- **Blocked** means a model, dependency, adapter, service, or explicit setup step is missing.
- **Experimental** means the capability exists but is not the recommended primary experience.

The CLI remains primary. Online deployment remains a safe status foundation only. Local queueing does not imply remote sync, verified push-to-talk does not imply continuous conversation, verified still-image analysis does not imply live camera/video vision, and read-only web inspection does not imply interactive browser control.
