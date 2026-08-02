# CLI Guide

The interactive `Jarvis >` prompt is the current primary JARVIS experience. It is backed by the Conversation and Command engines; ordinary messages use Executive JARVIS and Provider Router, while registered commands remain on the command path.

Start with `python main.py`. Use `help` for the focused command guide and `project status` for the current release, MVP readiness, and next milestone. Common operating commands include `local only on/off`, `local use <model>`, `provider status`, `tools status`, `voice status`, `voice output on/off`, `voice say <text>`, and `exit`.

## Mobile Planning Foundation

Use `mobile status`, `mobile policy`, `mobile capabilities`, `mobile setup`, `mobile plan <task>`, `mobile audit`, and `mobile close`. These commands do not connect to or control a phone. Requests involving messages, calls, notifications, contacts, photos, sensors, device input, apps, settings, purchases, login, unlock, or background monitoring are blocked.

`project status` also shows fixed and still-open limitation counts. Detailed evidence and future owners are in `docs/LIMITATIONS_REGISTER.md`.

Web inspection commands are `web status`, `web policy`, `web session`, `web open <https-url>`, `web title`, `web url`, `web snapshot`, `web audit`, and `web close`. They use the governed Web Automation Manager and a bounded standard-library adapter. `web open` reads safe public HTML/text metadata and a sanitized preview; it does not launch or control a browser. Local/internal targets, sensitive query fields, credential URLs, unsafe schemes, and unsafe categories are rejected. Interactive and sensitive actions remain unavailable.

Vision commands are `vision status`, `vision models`, `vision analyze <image_path>`, `vision describe <image_path>`, `vision ask <image_path> <question>`, `vision audit`, and `vision cleanup`. Quote paths containing spaces. PNG, JPEG, and WebP images are validated before any provider request. Analysis is local-only through the registered Ollama provider, and audit stores metadata rather than image bytes, base64, prompts, or full paths.

## Local Voice Input Setup

Voice input remains disabled until Vosk, a local model, `sounddevice`, and an input device are ready. Install optional packages with `python -m pip install -r requirements-voice.txt`; then place a model under `models/vosk/` or set `JARVIS_VOSK_MODEL_PATH`/`voice.stt_model_path`. Run `voice input status`, `voice input on`, and then `voice listen`. Use `voice listen send` only when the transcript should enter the normal JARVIS command/chat flow. `voice input test` performs one explicit test capture. See [`VOICE_INPUT.md`](VOICE_INPUT.md).

JARVIS does not download a model, activate a microphone in the background, retain captured PCM, persist transcript text in audit, or use cloud speech. Wake word and continuous listening remain unavailable.

## Local Vision Setup

Install a vision-capable Ollama model outside JARVIS, set `vision.model` to its name, then run `vision models` and `vision status`. The model must advertise vision input; a name alone is not accepted as proof. `llama3.2:1b` remains the text model and is not silently treated as vision-capable. JARVIS does not download models. Until readiness is reported, analysis commands validate files and metadata but return an honest unavailable result.

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
