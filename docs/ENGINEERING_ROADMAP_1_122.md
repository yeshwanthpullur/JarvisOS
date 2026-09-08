# Engineering Roadmap 1-122

This is the canonical engineering-step ledger. Prompt and Phase numbers are separate numbering systems and are never substituted for Engineering Step numbers.

## Baseline

- Latest checkpoint: **Step 62**
- Next target: **Step 63**
- Remaining range: **Steps 63-122**
- Remaining count: **60 steps**
- Evidence source: `docs/PRE_OLD_PHONE_FOUNDATION.md`, `docs/ROADMAP_STEPS_21_62.md`, `docs/PROMPT_HISTORY.md`, current tests, and the authoritative continuation specification received on 2026-09-08.
- Step 63 definition: **UNKNOWN / NOT RECOVERED**. It must not be implemented until its authoritative definition is supplied or recovered.

## Definition Provenance

- **CANONICAL / EVIDENCED:** Steps 21-62, as recorded in `docs/ROADMAP_STEPS_21_62.md` and verified by the current focused tests.
- **PROVISIONAL / RECOVERED SUMMARY:** The supplied recovery Markdown describes the broader architecture and gives an approximate later outline: voice completion/streaming; vision; capability/approval and safe execution; skills; scheduling; communications; observability/cost; privacy modes; offline resilience/recovery/backup; security; evaluation; dashboard; end-to-end validation; laptop freeze; stop; and later old-phone architecture. These summaries are context only, not step specifications.
- **UNKNOWN / NOT RECOVERED:** Individual authoritative definitions for Steps 1-20 and 63-122.

## Provisional Later-Roadmap Context

The supplied recovery summary groups later work approximately as follows. This table must not be used as an implementation schedule or canonical step mapping:

| Range | Provisional context only |
| ---: | --- |
| 63-64 | Voice completion/streaming-related work |
| 65-69 | Vision Intelligence |
| 70-80 | Capability registry, Approval Broker, safe execution, coding tools, GitHub, and MCP/tool integration |
| 81-83 | Browser read first, with browser actions later |
| 84-87 | Scheduler and communications |
| 88-92 | Observability, usage, and cost |
| 93-97 | Privacy modes |
| 98-102 | Offline resilience, recovery, and backup |
| 103-105 | Secrets, prompt-injection defense, and workspace isolation |
| 106-108 | Evaluation, golden tests, and regression systems |
| 109-110 | Unified dashboard |
| 111-119 | End-to-end, stress, security, failure, and repair testing |
| 120 | Freeze and document laptop architecture |
| 121 | Stop |
| 122 | Later old-phone architecture |

## Status Model

`NOT_STARTED`, `READY`, `READY_FOUNDATION`, `IN_PROGRESS`, `VERIFIED`, `DEGRADED`, `UNCONFIGURED`, `BLOCKED`, and `SUPERSEDED` are the allowed engineering-step statuses.

## Ledger

| Step | Status | Definition / evidence | Next action |
| ---: | --- | --- | --- |
| 1 | UNKNOWN / NOT RECOVERED | No authoritative individual definition recovered from repository records. | Recover definition before execution. |
| 2 | UNKNOWN / NOT RECOVERED | The repository records a Steps 2-20 foundation checkpoint, but not an authoritative individual definition for Step 2. | Recover definition before execution. |
| 3 | UNKNOWN / NOT RECOVERED | The repository records a Steps 2-20 foundation checkpoint, but not an authoritative individual definition for Step 3. | Recover definition before execution. |
| 4 | UNKNOWN / NOT RECOVERED | The repository records a Steps 2-20 foundation checkpoint, but not an authoritative individual definition for Step 4. | Recover definition before execution. |
| 5 | UNKNOWN / NOT RECOVERED | The repository records a Steps 2-20 foundation checkpoint, but not an authoritative individual definition for Step 5. | Recover definition before execution. |
| 6 | UNKNOWN / NOT RECOVERED | The repository records a Steps 2-20 foundation checkpoint, but not an authoritative individual definition for Step 6. | Recover definition before execution. |
| 7 | UNKNOWN / NOT RECOVERED | The repository records a Steps 2-20 foundation checkpoint, but not an authoritative individual definition for Step 7. | Recover definition before execution. |
| 8 | UNKNOWN / NOT RECOVERED | The repository records a Steps 2-20 foundation checkpoint, but not an authoritative individual definition for Step 8. | Recover definition before execution. |
| 9 | UNKNOWN / NOT RECOVERED | The repository records a Steps 2-20 foundation checkpoint, but not an authoritative individual definition for Step 9. | Recover definition before execution. |
| 10 | UNKNOWN / NOT RECOVERED | The repository records a Steps 2-20 foundation checkpoint, but not an authoritative individual definition for Step 10. | Recover definition before execution. |
| 11 | UNKNOWN / NOT RECOVERED | The repository records a Steps 2-20 foundation checkpoint, but not an authoritative individual definition for Step 11. | Recover definition before execution. |
| 12 | UNKNOWN / NOT RECOVERED | The repository records a Steps 2-20 foundation checkpoint, but not an authoritative individual definition for Step 12. | Recover definition before execution. |
| 13 | UNKNOWN / NOT RECOVERED | The repository records a Steps 2-20 foundation checkpoint, but not an authoritative individual definition for Step 13. | Recover definition before execution. |
| 14 | UNKNOWN / NOT RECOVERED | The repository records a Steps 2-20 foundation checkpoint, but not an authoritative individual definition for Step 14. | Recover definition before execution. |
| 15 | UNKNOWN / NOT RECOVERED | The repository records a Steps 2-20 foundation checkpoint, but not an authoritative individual definition for Step 15. | Recover definition before execution. |
| 16 | UNKNOWN / NOT RECOVERED | The repository records a Steps 2-20 foundation checkpoint, but not an authoritative individual definition for Step 16. | Recover definition before execution. |
| 17 | UNKNOWN / NOT RECOVERED | The repository records a Steps 2-20 foundation checkpoint, but not an authoritative individual definition for Step 17. | Recover definition before execution. |
| 18 | UNKNOWN / NOT RECOVERED | The repository records a Steps 2-20 foundation checkpoint, but not an authoritative individual definition for Step 18. | Recover definition before execution. |
| 19 | UNKNOWN / NOT RECOVERED | The repository records a Steps 2-20 foundation checkpoint, but not an authoritative individual definition for Step 19. | Recover definition before execution. |
| 20 | UNKNOWN / NOT RECOVERED | The repository records a Steps 2-20 foundation checkpoint, but not an authoritative individual definition for Step 20. | Recover definition before execution. |
| 21 | READY | Task checkpointing, resume, and recovery. Evidence: `docs/ROADMAP_STEPS_21_62.md` and focused tests. | Maintain evidence. |
| 22 | READY_FOUNDATION | Automated code review agents. Structured findings and review gates are tested; unrestricted external review is disabled. | Maintain bounded foundation. |
| 23 | READY_FOUNDATION | Automated testing and verification agents. Deterministic plans and gates are tested; external execution is disabled. | Maintain bounded foundation. |
| 24 | READY_FOUNDATION | Automatic rework loop. Bounded requests and attempt limits are tested; unbounded self-modification is disabled. | Maintain bounded foundation. |
| 25 | READY_FOUNDATION | Integration/merge candidate pipeline. Candidate gating is tested; automatic merge/commit/push is disabled. | Maintain bounded foundation. |
| 26 | READY | Proof-of-work and evidence completion. Typed bounded evidence is exercised. | Maintain evidence. |
| 27 | VERIFIED | Small real-project multi-agent test. Isolated in-process benchmark passed without merge. | Maintain benchmark evidence. |
| 28 | DEGRADED | Gesture-reel serious benchmark. Software-side benchmark is deterministic; physical validation is pending. | Await hardware/platform evidence. |
| 29 | VERIFIED | Munder DiffLin evaluation. Suitability is classified without execution authority. | Maintain evidence. |
| 30 | READY | JARVIS owns orchestration checkpoint, review, evidence, recovery, and candidate state. | Maintain authority boundary. |
| 31 | READY | JARVIS-native Control Room backend with bounded governed actions. | Maintain bounded control. |
| 32 | READY_FOUNDATION | Control Room UI/dashboard. API and DOM checks passed; visual browser acceptance remains unclaimed. | Perform visual acceptance when appropriate. |
| 33 | READY_FOUNDATION | Research Intelligence planning, source lifecycle, and evidence coordination. | Maintain read-only boundary. |
| 34 | DEGRADED | Crawl4AI and Firecrawl bounded crawler contract. Optional live packages/services unavailable. | Configure only through approved local/optional route. |
| 35 | READY | Source verification and citations. Source linkage and no-invented-citation behavior tested. | Maintain evidence quality. |
| 36 | READY_FOUNDATION | Deep/technical research bounded roles and DAG planning. No open-ended autonomous loop. | Maintain bounded research. |
| 37 | READY | Canonical local document pipeline and provenance. | Maintain provenance. |
| 38 | UNCONFIGURED | Docling adapter exists; package absent. | Configure optional dependency only if approved. |
| 39 | UNCONFIGURED | Marker adapter exists; package absent. | Configure optional dependency only if approved. |
| 40 | READY_FOUNDATION | Provider-neutral local OCR contracts and routing. | Keep live engine optional. |
| 41 | UNCONFIGURED | PaddleOCR adapter exists; package absent. | Configure optional dependency only if approved. |
| 42 | PLANNED | Optional cloud OCR behind explicit policy. | Remains disabled by default. |
| 43 | READY | Document/OCR routing with bounded fallback and failure states. | Maintain bounded routing. |
| 44 | READY | Unified versioned document representation and round-trip behavior. | Maintain schema compatibility. |
| 45 | DEGRADED | PDF/DOCX/PPTX/table/image extraction. Complex layout/OCR needs optional providers. | Preserve truthful degraded states. |
| 46 | READY_FOUNDATION | Grounded document QA and summarization with provenance. | Maintain source grounding. |
| 47 | READY | Knowledge/RAG pipeline with deterministic lexical/hybrid path. | Semantic retrieval remains optional. |
| 48 | UNCONFIGURED | Qdrant vector-store contract and routing. Package/server absent. | Configure only through approved local setup. |
| 49 | UNCONFIGURED | Chroma and FAISS fallback contracts. Packages absent. | Configure only through approved local setup. |
| 50 | READY_FOUNDATION | Versioned deterministic local embeddings and bounded reranking. | Add production embedding provider only when approved. |
| 51 | READY | Provenance/citation-aware retrieval. | Maintain stale/conflict visibility. |
| 52 | READY_FOUNDATION | Governed personal-memory architecture. | Preserve explicit authority. |
| 53 | UNCONFIGURED | Mem0 adapter governed by JARVIS; package absent. | Keep local governed memory authoritative. |
| 54 | READY_FOUNDATION | Local temporal memory fallback; native Graphiti unavailable. | Maintain truthful fallback. |
| 55 | READY | Session/project/knowledge/personal separation. | Maintain scope enforcement. |
| 56 | READY | Explicit memory lifecycle operations and audit. | Preserve non-destructive defaults. |
| 57 | READY_FOUNDATION | Provider-neutral Voice Intelligence and explicit PTT routing. | Physical validation remains pending. |
| 58 | DEGRADED | Faster-Whisper adapter and fixtures; dependency/model absent. | Configure local dependency/model if approved. |
| 59 | DEGRADED | Vosk fallback and fixtures; runtime dependency availability is degraded. | Preserve fallback and truthful health. |
| 60 | DEGRADED | Piper adapter and SAPI fallback; voice model absent. | Configure local voice model if approved. |
| 61 | READY | Windows SAPI fallback, interruption, and long-reply playback. | Maintain Windows-specific path. |
| 62 | READY_FOUNDATION | Explicit push-to-talk states, bounded buffers, cleanup, and normal dispatch. Physical microphone test pending. | Complete physical validation only when configured. |
| 63 | READY_FOUNDATION | Recovered Engineering Specification: voice completion/streaming lifecycle beyond Step 62. Metadata-only playback events, ordered chunk lifecycle, observer isolation, and bounded event history are implemented and tested. | Continue to Step 64 using the recovered voice grouping; preserve explicit capture and playback boundaries. |
| 64 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 65 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 66 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 67 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 68 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 69 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 70 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 71 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 72 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 73 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 74 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 75 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 76 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 77 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 78 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 79 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 80 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 81 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 82 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 83 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 84 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 85 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 86 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 87 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 88 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 89 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 90 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 91 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 92 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 93 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 94 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 95 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 96 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 97 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 98 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 99 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 100 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 101 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 102 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 103 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 104 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 105 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 106 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 107 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 108 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 109 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 110 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 111 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 112 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 113 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 114 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 115 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 116 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 117 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 118 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 119 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 120 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 121 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |
| 122 | UNKNOWN / NOT RECOVERED | No authoritative definition recovered. | Supply or recover definition. |

## Reconciliation Result

The repository supports the Step 62 baseline and the known Steps 21-62 evidence. Step 63 now has a clearly labeled recovered engineering specification derived from the supplied recovery roadmap, existing voice architecture, and current tests. It is not claimed to be the original historical prompt. Steps 64-122 remain recovered group context or unrecovered individual definitions and must be handled with the same provenance discipline.

## Step 63 Record

### Step 63

- **Status:** `READY_FOUNDATION`
- **Specification classification:** `RECOVERED ENGINEERING SPECIFICATION`
- **Objective:** Advance the voice subsystem with bounded provider-neutral streaming lifecycle behavior without adding continuous listening or unrestricted execution.
- **Implementation:** Added `VoicePlaybackEvent`, optional lifecycle observers, bounded event history, ordered chunk-started/completed events, completion/failure/cancel/stop/resume events, and `stream_playback()`.
- **Files:** `jarvis/voice_intelligence.py`, `tests/test_voice_playback_control.py`.
- **Dependencies:** Existing Windows SAPI playback worker and Step 62 sentence chunking; no new package or credential.
- **Tests:** Voice playback and Step 57-62 suite: 32 passed, 2 subtests passed; full suite after the change: 2,309 passed, 331 subtests, 0 failed, 1 pre-existing collection warning.
- **Verification:** Event payloads contain state/counters only; raw speech text and audio paths are not emitted. Observer exceptions do not terminate playback.
- **Evidence:** Focused pytest run completed successfully in the project `.venv`.
- **Limitations:** This is lifecycle/event streaming, not continuous microphone listening, wake-word activation, or cloud streaming.
- **Decisions:** Preserve existing interruption, stop/resume/cancel, SAPI process control, and explicit PTT boundaries.
- **Automation impact:** Enables safe UI/control-room playback progress observation without granting execution authority.
- **Git commit:** `f62051c` (`Implement recovered engineering step 63 voice streaming`).
- **Obsidian records:** `JARVIS_OS/01_PROJECT/CURRENT_STATUS.md`, `JARVIS_OS/12_TESTING/TEST_STATUS.md`, and the Step 63 session log.
- **Next step:** Reconstruct and implement Step 64 only from the recovered voice grouping and repository evidence.
