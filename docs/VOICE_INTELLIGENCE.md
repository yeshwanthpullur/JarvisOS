# Voice Intelligence

Voice Intelligence is a local-first input/output layer that feeds validated transcripts into the existing Command and Conversation Engines. It never executes commands, tools, plans, agents, or workflows itself. Voice recognition and wake-word events are not authentication or approval.

Voice, microphone input, wake words, continuous listening, and raw-audio retention are disabled by default. Text mode remains fully operational when every audio dependency is unavailable.

## Modes and sessions

Modes are `off`, `push-to-talk`, `single-listen`, `continuous-session-ready`, and `wake-word-ready`. The latter two provide state contracts only and never start a background listener. Sessions distinguish ready, listening, processing, confirmation, speaking, interrupted, cancelled, failed, and completed states.

## Adapters and local backends

The adapter registry validates identity and capabilities. Windows SAPI is the real local text-to-speech backend and supports WAV output and playback. Offline STT discovery recognizes Vosk, faster-whisper, and a configured whisper.cpp-style executable, but reports unavailable until an engine, model, and microphone capture adapter are ready. No model is downloaded and no cloud fallback occurs.

Audio devices are normalized and only adapter-confirmed devices are listed. Microphone capture is not fabricated when no capture adapter exists. WAV input is checked for allowed path scope, extension, actual RIFF structure, size, duration, sample rate, and channels without modifying the source.

## Validation, safety, and privacy

Transcripts are untrusted. Empty, oversized, malformed, low-confidence, and ambiguous results are rejected or require confirmation before sensitive command routing. Responses containing secrets or code remain text-only; long responses are summarized for speech while full text stays visible.

Strict privacy enforces local-only processing, no raw retention, and minimal metadata. Standard prefers local processing. Diagnostic adds local metadata but never enables recording. Raw retention defaults off. Normal speech uses direct playback without a WAV or MP3; file output requires an explicit path. Temporary input audio is scoped to the configured temp directory, bounded by age/count policy, and removable with `voice cleanup`; the command also removes legacy generated output from the managed voice-output directory. User-provided input files are not deleted. Audio bytes and full transcripts are not logged.

## Commands

Commands include `voice status`, `voice input status/on/off`, `voice listen`, `voice cleanup`, `voice output on/off`, `voice say`, `transcribe`, `stop`, `cancel`, `interrupt`, `session`, `devices`, `backend`, `device`, `mode`, `privacy`, `language`, `rate`, `volume`, `raw-audio`, `limits`, and `health`. Commands remain on the existing Command Engine path.

## Limitations

Push-to-talk command/state and privacy boundaries are implemented, but real microphone capture requires a registered capture adapter plus a configured local STT engine/model. The current machine reports those missing capabilities truthfully. SAPI cancellation is cooperative at the process boundary; explicitly saved or acceptance-test WAV files remain local runtime artifacts and are not committed.
