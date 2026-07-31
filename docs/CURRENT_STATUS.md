# Current Status

Updated: 2026-08-01

## Current Release

- Release: `v0.3.0-alpha - Local Voice and CLI Stability`
- Commit: `d2bcb28d988b098c73e98199fc646c08b95f248e`
- Branch: `main`
- Release page: `https://github.com/yeshwanthpullur/JarvisOS/releases/tag/v0.3.0-alpha`

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
- Online deployment foundation: repository routing now isolates the CLI from a safe status-only Vercel function; live project verification is tracked separately from online sync.

## Experimental Features

- Local desktop web interface. It is loopback-only and feature-connected, but may feel jerky or laggy and is not the recommended primary mode.

## Not Started Features

- Online sync.
- Web automation.
- Mobile automation.

## Blocked Features

- Real offline microphone transcription is blocked until a supported local STT runtime, model, and capture adapter are explicitly configured. No microphone capture is started automatically.

## Known Limitations

- SAPI playback is synchronous, so the CLI waits while speech is playing.
- Voice input is architecturally connected but unavailable on this machine; `voice listen` does not fake transcription.
- Cloud execution depends on user-provided credentials and explicit paid-request approval.
- The web interface is experimental.
- No vision, cross-device sync, browser automation, or mobile control exists yet.
- Runtime state is local and some conversation/interface state is not durable across restarts.
- The former Vercel failure occurred because automatic detection treated root `main.py` as a Python function even though it is intentionally CLI-only. `vercel.json` now builds only `api/index.py`; the deployed surface remains status-only and is not online JARVIS or sync.
- Two Vercel projects (`jarvis-os` and `jarvis-os-6oy2`) are connected. Keep `jarvis-os` as the canonical project after live verification and disconnect or delete the duplicate manually.

## Next Recommended Prompt

Prompt 33 - Online Sync Foundation. Vision remains separate from web/mobile automation and does not grant screen-control authority.

## Last Verified Tests

- Full suite: 1,408 passed, 0 skipped, 0 failed, 0 errors.
- Focused vision/provider/command/settings/project-health suite: 119 passed.
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
- [x] Run `voice output off` and `exit`.
- [ ] Re-verify paid cloud execution only with explicit permission and configured credentials.
