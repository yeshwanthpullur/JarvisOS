# CLI Guide

The interactive `Jarvis >` prompt is the current primary JARVIS experience. It is backed by the Conversation and Command engines; ordinary messages use Executive JARVIS and Provider Router, while registered commands remain on the command path.

Start with `python main.py`. Use `help` for the focused command guide and `project status` for the current release, MVP readiness, and next milestone. Common operating commands include `local only on/off`, `local use <model>`, `provider status`, `tools status`, `voice status`, `voice output on/off`, `voice say <text>`, and `exit`.

`project status` also shows fixed and still-open limitation counts. Detailed evidence and future owners are in `docs/LIMITATIONS_REGISTER.md`.

Web inspection commands are `web status`, `web policy`, `web session`, `web open <https-url>`, `web title`, `web url`, `web snapshot`, `web audit`, and `web close`. They use the governed Web Automation Manager and a bounded standard-library adapter. `web open` reads safe public HTML/text metadata and a sanitized preview; it does not launch or control a browser. Local/internal targets, sensitive query fields, credential URLs, unsafe schemes, and unsafe categories are rejected. Interactive and sensitive actions remain unavailable.

Vision commands are `vision status`, `vision describe <image_path>`, and `vision ask <image_path> <question>`. Quote paths containing spaces. Image metadata is available after validation; semantic descriptions require a genuinely vision-capable configured model.

## Local Voice Input Setup

Voice input remains disabled until all three local prerequisites exist: a supported offline STT engine, its model files, and a registered microphone capture adapter. Supported discovery paths include Vosk, faster-whisper, and a configured whisper.cpp-style executable. Configure paths through existing voice settings, then run `voice input status` before enabling input. JARVIS does not download a model, activate a microphone, retain raw audio, or use cloud speech automatically.

## Local Vision Setup

Install a vision-capable model in the configured local runtime outside JARVIS, then refresh local model discovery and run `vision status`. The provider must advertise vision input; a model name alone is not accepted as proof. `llama3.2:1b` remains the text model and is not silently treated as vision-capable. Until readiness is reported, `vision describe` and `vision ask` validate files and metadata but return an honest unavailable result for semantic analysis.

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
