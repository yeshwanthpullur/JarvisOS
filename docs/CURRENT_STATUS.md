# Current Status

Updated: 2026-08-02

## Current Release

- Release: `v0.9.0-alpha - Local STT and Voice Input Foundation`
- Baseline commit: `515ee84f812469ffd2117d51ef1e42ed47c2ece5`
- Branch: `main`
- Release page: `https://github.com/yeshwanthpullur/JarvisOS/releases/tag/v0.9.0-alpha`

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
- Voice Input: executable lazy Vosk transcription, model validation, explicit in-memory `sounddevice` capture, status/on/off/test/listen commands, optional transcript handoff, and content-free audit exist. Real microphone transcription still needs optional packages, a local model, and manual device verification on this machine.
- Vision Intelligence: an explicit local Ollama adapter now discovers the configured vision model, routes real image requests through Provider Router, normalizes failures/timeouts, and keeps bounded metadata-only audit. Semantic analysis is available when a local model advertises vision; the verified machine has only `llama3.2:1b`, so its real model state remains unavailable.
- Online deployment foundation: both connected Vercel projects reached Ready from commit `57a10421c8f98beb24bb3eb7d2bad60bc0bf036b`; the canonical `jarvis-os` `/api/status` response was verified live.
- Online Sync foundation: disabled-by-default manual queueing, strict summary schemas, atomic persistence, deduplication, bounded audit/retention, conflict detection, and truthful unavailable remote behavior work. No real encrypted remote adapter is configured.
- Web Automation: bounded read-only public HTML/text inspection works through a standard-library adapter with DNS/IP checks, redirect revalidation, sanitized previews, and redacted audit. Interactive actions remain blocked.
- Mobile Automation: planning-only manager, policy, adapters, CLI, and redacted audit work without connecting to or controlling a phone. Private and sensitive actions are blocked.
- Study and research support: general chat, retrieval, research, planning, goals, and public-page inspection can help, but no dedicated end-to-end Study Assistant workflow exists.
- Advanced project building: planning, tools, agents, providers, tests, and Git workflows exist independently, but a formal governed Builder Mode is not implemented.
- Raspberry Pi and hardware support: general coding and planning guidance is available, but no verified hardware profile or deployment module exists.
- Personal workspace: the CLI composes many capabilities, but the unified multi-tool replacement experience remains future work.

## Experimental Features

- Local desktop web interface. It is loopback-only and feature-connected, but may feel jerky or laggy and is not the recommended primary mode.

## Not Started Features

- Image generation workflow inside JARVIS OS.
- Video editing workflow.
- Safe call and communication assistance.
- Real encrypted remote synchronization and cross-device sync.
- Live camera/video vision and cloud vision.

## Blocked Features

- Real offline microphone transcription is blocked until a supported local STT runtime, model, and capture adapter are explicitly configured. No microphone capture is started automatically.
- Real semantic image analysis on the verified machine is blocked until a local Ollama vision model such as `llava` is installed and configured. JARVIS does not download it.

## Known Limitations

The audited register contains **46** limitations: **17 fixed** and **29 still open** across open, deferred, blocked, and experimental states. Future product goals are recorded as deferred capabilities, not current defects or completed features. See [`LIMITATIONS_REGISTER.md`](LIMITATIONS_REGISTER.md).

- SAPI playback is synchronous, so the CLI waits while speech is playing.
- Voice input has a real optional Vosk/capture path but remains unavailable on this machine until Vosk, `sounddevice`, a model, and a microphone are verified; `voice listen` does not fake transcription.
- Cloud execution depends on user-provided credentials and explicit paid-request approval.
- The web interface is experimental.
- Sync is local-queue-only in practice: `sync run` cannot upload until a real authenticated encrypted adapter is configured. The Vercel status endpoint is not a sync backend.
- Local Ollama vision execution now exists, but the verified machine lacks a vision model. Live camera/video, face recognition, guaranteed OCR, cloud/Vercel vision, cross-device sync, interactive browser control, and live mobile control do not exist.
- Image generation, video editing, dedicated study, formal Builder Mode, Raspberry Pi profiles, communication/call assistance, and the unified personal workspace remain future milestones.
- Runtime state is local and some conversation/interface state is not durable across restarts.
- The former Vercel failure occurred because automatic detection treated root `main.py` as a Python function even though it is intentionally CLI-only. `vercel.json` now builds only `api/index.py`; the deployed surface remains status-only and is not online JARVIS or sync.
- The current production deployment for canonical project `jarvis-os` is Ready at commit `df912e8f67c06503bb0eecb1fa8cbec13095f2b4`. Failed deployments shown before commit `57a10421c8f98beb24bb3eb7d2bad60bc0bf036b` are historical records from before `vercel.json` and `api/index.py` existed; they do not describe current health and may be ignored or deleted.
- `jarvis-os-6oy2` was created as a duplicate and still appears in the Vercel account. It should remain unused and be disconnected or deleted manually; `jarvis-os` is the only canonical project.
- Verified canonical endpoint: `https://jarvis-221b5o5fc-jj1-e21e.vercel.app/api/status`. Vercel Deployment Protection may redirect anonymous root or health requests to sign-in until the project setting is changed.

## Next Recommended Prompt

Prompt 38 - Study Assistant and Research Workflows. Vision and Voice Input remain Partial until their optional local models and hardware are installed and verified with real inputs.

The product direction after Prompt 35 is maintained in [`JARVIS_USE_CASES.md`](JARVIS_USE_CASES.md) and maps named milestones through Prompt 50.

## Last Verified Tests

- Full suite: 1,518 passed, 0 skipped, 0 failed, 0 errors.
- Focused vision/provider/config/tracking/deployment suite: 85 passed, 0 skipped, 0 failed, 0 errors.
- Focused Vision Intelligence suite: 25 passed, 0 skipped, 0 failed, 0 errors.
- Real Ollama chat: passed with `llama3.2:1b`.
- Local Ollama vision discovery: Ollama reachable; configured `llava` model missing, so no real image description was claimed.
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
- [x] Run `vision status` and `vision models`; confirm Ollama is reachable and the missing local vision model is reported truthfully.
- [x] Confirm mocked local Ollama vision execution routes image data through Provider Router while audit retains no image/base64/prompt/path content.
- [x] Run `web status` and `web policy`; confirm unsafe URLs and sensitive actions are blocked.
- [x] Inspect `https://example.com` through `web open`, `web title`, and `web snapshot`; confirm bounded output and no persistent page data.
- [x] Run mobile status, policy, capabilities, setup, safe planning, audit, and close; confirm no phone access.
- [x] Confirm message, notification, call, and camera plans are blocked before adapter dispatch.
- [x] Run `voice output off` and `exit`.
- [ ] Re-verify paid cloud execution only with explicit permission and configured credentials.
