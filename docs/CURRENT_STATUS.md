# Current Status

Updated: 2026-08-02

## Current Release

- Release: `v0.5.0-alpha - Sync and Limitations Tracking`
- Baseline commit: `01dd1fc1f139f45a4c54b86202cb71fe8619829f`
- Branch: `main`
- Release page: `https://github.com/yeshwanthpullur/JarvisOS/releases/tag/v0.5.0-alpha`

## Stable Launch

```powershell
python main.py
```

The normal CLI is the current primary and recommended user experience. Use `help` for common commands and `project status` for a compact project-health summary.

The local web interface is optional and experimental:

```powershell
python main.py --ui
```

## Working Features

- Core startup, health checks, clean shutdown, configuration, and rotating logs.
- Ordinary local chat through Executive JARVIS, Reasoning, Provider Execution Manager, Provider Router, and Ollama.
- Local-only routing policy and explicit local-model selection.
- Focused CLI help, provider/tool status, and readable non-debug output.
- Safe calculator and text-transformation tools through Tool Intelligence.
- Windows SAPI voice playback through `voice say` and safe automatic spoken replies.
- Playback-only speech produces no permanent audio file by default; temporary voice audio is bounded and user-cleanable.
- Conversation, context, retrieval, personal, task, goal, workflow, reflection, and adaptive foundations.
- Automated regression suite and a published annotated alpha release.

## Partially Working Features

- Cloud provider framework: configured adapters, policy, normalization, mocked tests, and command access exist; paid live providers are not continuously verified.
- Tool Intelligence: safe built-ins work, while broad external tool integrations are future work.
- Autonomous Planning: advisory plans work, but autonomous execution is intentionally not enabled.
- Multi-Agent Intelligence: governed planner/reviewer coordination exists, but broad specialist coverage is limited.
- Memory and Knowledge: authoritative local storage exists, but long-term pruning and cross-device policy are not automated.
- Voice Input: status, explicit enable/disable/listen commands, local STT discovery, privacy limits, and temp cleanup exist; real microphone transcription still needs a configured local engine, model, and capture adapter.
- Vision Intelligence: CLI path validation, safe metadata, local-only policy, and Provider Router integration work; semantic analysis awaits a model that advertises vision capability.
- Online deployment foundation: both connected Vercel projects reached Ready from commit `57a10421c8f98beb24bb3eb7d2bad60bc0bf036b`; the canonical `jarvis-os` `/api/status` response was verified live.
- Online Sync foundation: disabled-by-default manual queueing, strict summary schemas, atomic persistence, deduplication, bounded audit/retention, conflict detection, and truthful unavailable remote behavior work. No real encrypted remote adapter is configured.
- Web Automation foundation: strict URL policy, permissions, read-only commands, normalized results, and bounded redacted audit work. No real browser adapter is configured, and interactive actions are blocked.

## Experimental Features

- Local desktop web interface. It is loopback-only and feature-connected, but may feel jerky or laggy and is not the recommended primary mode.

## Not Started Features

- Mobile automation.

## Blocked Features

- Real offline microphone transcription is blocked until a supported local STT runtime, model, and capture adapter are explicitly configured. No microphone capture is started automatically.

## Known Limitations

The audited register contains **27** limitations: **13 fixed** and **14 still open** across open, deferred, blocked, and experimental states. See [`LIMITATIONS_REGISTER.md`](LIMITATIONS_REGISTER.md).

- SAPI playback is synchronous, so the CLI waits while speech is playing.
- Voice input is architecturally connected but unavailable on this machine; `voice listen` does not fake transcription.
- Cloud execution depends on user-provided credentials and explicit paid-request approval.
- The web interface is experimental.
- Sync is local-queue-only in practice: `sync run` cannot upload until a real authenticated encrypted adapter is configured. The Vercel status endpoint is not a sync backend.
- Semantic vision, cross-device sync, interactive browser control, and mobile control do not exist yet. Safe image metadata, the local sync queue, and governed read-only web request foundations do exist.
- Runtime state is local and some conversation/interface state is not durable across restarts.
- The former Vercel failure occurred because automatic detection treated root `main.py` as a Python function even though it is intentionally CLI-only. `vercel.json` now builds only `api/index.py`; the deployed surface remains status-only and is not online JARVIS or sync.
- The current production deployment for canonical project `jarvis-os` is Ready at commit `df912e8f67c06503bb0eecb1fa8cbec13095f2b4`. Failed deployments shown before commit `57a10421c8f98beb24bb3eb7d2bad60bc0bf036b` are historical records from before `vercel.json` and `api/index.py` existed; they do not describe current health and may be ignored or deleted.
- `jarvis-os-6oy2` was created as a duplicate and still appears in the Vercel account. It should remain unused and be disconnected or deleted manually; `jarvis-os` is the only canonical project.
- Verified canonical endpoint: `https://jarvis-221b5o5fc-jj1-e21e.vercel.app/api/status`. Vercel Deployment Protection may redirect anonymous root or health requests to sign-in until the project setting is changed.

## Next Recommended Prompt

Prompt 35 - Mobile Automation. It must establish a narrow trusted-device boundary and must not weaken the web, tool, workflow, or approval controls.

## Last Verified Tests

- Full suite: 1,463 passed, 0 skipped, 0 failed, 0 errors.
- Focused web/command/CLI/voice/vision/sync/settings/tracking/deployment suite: 213 passed.
- Real Ollama chat: passed with `llama3.2:1b`.
- Local-only enforcement: passed.
- Explicit and automatic Windows SAPI playback paths: passed; audible playback was manually confirmed.
- `git diff --check`: passed.

## Manual Verification Checklist

- [x] Start `python main.py` and reach `Jarvis >`.
- [x] Run `local only on`.
- [x] Run `local use llama3.2:1b`.
- [x] Ask a normal question and receive a real Ollama answer.
- [x] Run `voice status` and confirm Windows SAPI readiness.
- [x] Run `voice output on` and `voice say JARVIS CLI VOICE CHECK`.
- [x] Confirm a safe assistant reply is spoken.
- [x] Confirm normal speech creates no permanent WAV/MP3 and `voice cleanup` is safe.
- [x] Confirm `voice input status/on/listen` reports unavailable local prerequisites without activating a microphone.
- [x] Run calculator Tool Intelligence and confirm a real normalized result.
- [x] Run `web status` and `web policy`; confirm unsafe URLs and sensitive actions are blocked.
- [ ] Configure and verify a real read-only browser adapter before claiming live page access.
- [x] Run `voice output off` and `exit`.
- [ ] Re-verify paid cloud execution only with explicit permission and configured credentials.
