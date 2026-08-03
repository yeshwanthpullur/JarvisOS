# CLI Guide

The interactive `Jarvis >` prompt is the current primary JARVIS experience. It is backed by the Conversation and Command engines; ordinary messages use Executive JARVIS and Provider Router, while registered commands remain on the command path.

Start with `python main.py`. Use `help` for the focused command guide and `project status` for the current release, MVP readiness, and next milestone. Common operating commands include `local only on/off`, `local use <model>`, `provider status`, `tools status`, `voice status`, `voice output on/off`, `voice say <text>`, and `exit`.

## Conversation Intelligence

Plain text supports bounded multi-turn follow-ups such as `Explain more`, `Go deeper`, `Simplify`, `Give examples`, `Compare`, `Summarize`, `Repeat`, `Continue`, `Why?`, and `How?`. Clear references such as `it`, `that`, `former`, and `latter` use the active topic or comparison; ambiguous references produce one clarification question instead of a guess.

Use `conversation status`, `conversation topic`, `conversation confidence`, `conversation mode`, `conversation summary`, and `conversation reset`. Context is in memory and bounded. `conversation reset` does not delete persistent memories; `memory forget <id>` remains the explicit deletion authority. `voice listen send` and `voice interrupt` submit through this same conversation path without automatically storing transcripts.

## Mobile Planning Foundation

Use `mobile status`, `mobile policy`, `mobile capabilities`, `mobile setup`, `mobile plan <task>`, `mobile audit`, and `mobile close`. These commands do not connect to or control a phone. Requests involving messages, calls, notifications, contacts, photos, sensors, device input, apps, settings, purchases, login, unlock, or background monitoring are blocked.

`project status` shows fixed, still-open, intentionally restricted, and externally blocked limitation counts. Use `limitations status`, `limitations open`, `limitations fixed`, `limitations show <id>`, `limitations category <category>`, or `limitations next` for bounded evidence and ownership. The full review is in `docs/LIMITATIONS_REVIEW_PROMPT_40.md`.

## Memory Commands

Use `memory status`, `memory help`, `memory list`, `memory search <text>`, `memory show <id>`, `memory remember <title> | <content>`, `memory forget <id>`, `memory update <id> <content>`, `memory archive <id>`, `memory recent`, `memory preferences`, `memory projects`, `memory audit`, `memory cleanup`, and `memory consolidate`. Memory stays local, secret-aware, and bounded. The memory layer can feed safe context back into chat, but it does not sync anywhere and it does not replace command or conversation authority.

Web inspection commands are `web status`, `web policy`, `web session`, `web open <https-url>`, `web title`, `web url`, `web snapshot`, `web audit`, and `web close`. They use the governed Web Automation Manager and a bounded standard-library adapter. `web open` reads safe public HTML/text metadata and a sanitized preview; it does not launch or control a browser. Local/internal targets, sensitive query fields, credential URLs, unsafe schemes, and unsafe categories are rejected. Interactive and sensitive actions remain unavailable.

Vision commands are `vision status`, `vision models`, `vision analyze <image_path>`, `vision describe <image_path>`, `vision ask <image_path> <question>`, `vision audit`, and `vision cleanup`. Quote paths containing spaces. PNG, JPEG, and WebP images are validated before any provider request. Analysis is local-only through the registered Ollama provider, and audit stores metadata rather than image bytes, base64, prompts, or full paths.

## Local Voice Input Setup

Voice input is manually verified with Vosk, `sounddevice`, a microphone, and a local Indian-English model. Keep the model outside Git and configure `JARVIS_VOSK_MODEL_PATH` or `voice.stt_model_path`. Run `voice input status`, `voice input on`, and then `voice listen`. Use `voice listen send` only when the transcript should enter the normal JARVIS command/chat flow. `voice input test` performs one explicit test capture. Missing local prerequisites are reported truthfully without hidden recording. See [`VOICE_INPUT.md`](VOICE_INPUT.md).

JARVIS does not download a model, activate a microphone in the background, retain captured PCM, persist transcript text in audit, or use cloud speech. Wake word and continuous listening remain unavailable.

## Voice Playback Controls

Spoken replies run in one ordered background queue. Use `voice speaking status` to inspect progress, `voice pause` for a safe-boundary pause, `voice stop` to interrupt immediately while retaining unspoken speech, and `voice resume` to continue. Because Windows SAPI cannot report the exact word reached when its process is terminated, resuming after `voice stop` restarts the interrupted chunk from its beginning; already completed chunks are not replayed. Use `voice cancel` to interrupt immediately and permanently discard the retained queue. Starting a new response replaces and cancels any older resumable speech.

## Local Vision Setup

Install a vision-capable Ollama model outside JARVIS, set `vision.model` to its name, then run `vision models` and `vision status`. Local LLaVA analysis and image Q&A are manually verified on the current machine. The model must advertise vision input; a name alone is not accepted as proof, and `llama3.2:1b` is not silently treated as vision-capable. JARVIS does not download models and reports unavailable truthfully when Ollama or the configured model is absent.

## Sync Commands

```text
sync status
sync on
sync off
sync add project_status
sync queue
sync queue summary
sync inspect <sync_item_id>
sync cancel <sync_item_id>
sync retry <sync_item_id>
sync run
sync conflicts
sync cleanup
```

Sync starts disabled. `sync on` enables a manual local queue only; it does not enable background or remote uploading. `sync add project_status` queues a compact allowlisted health snapshot. `sync run` truthfully returns unavailable until an authenticated encrypted remote adapter exists. The Vercel status endpoint is not a sync backend.
