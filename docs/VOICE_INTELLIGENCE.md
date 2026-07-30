# Voice Intelligence

Voice Intelligence is a local-first input/output layer that feeds validated transcripts into the existing Command and Conversation Engines. It never executes commands, tools, plans, agents, or workflows itself. Voice recognition and wake-word events are not authentication or approval.

Voice, microphone input, wake words, continuous listening, and raw-audio retention are disabled by default. Text mode remains fully operational when every audio dependency is unavailable.

## Modes and sessions

Modes are `off`, `push-to-talk`, `single-listen`, `continuous-session-ready`, and `wake-word-ready`. The latter two provide state contracts only and never start a background listener. Sessions distinguish ready, listening, processing, confirmation, speaking, interrupted, cancelled, failed, and completed states.

## Adapters and local backends

The adapter registry validates identity and capabilities. Windows SAPI is the real local text-to-speech backend and supports WAV output and playback. Offline STT discovery checks for supported local libraries but reports unavailable until both an engine and model are configured. No model is downloaded and no cloud fallback occurs.

Audio devices are normalized and only adapter-confirmed devices are listed. Microphone capture is not fabricated when no capture adapter exists. WAV input is checked for allowed path scope, extension, actual RIFF structure, size, duration, sample rate, and channels without modifying the source.

## Validation, safety, and privacy

Transcripts are untrusted. Empty, oversized, malformed, low-confidence, and ambiguous results are rejected or require confirmation before sensitive command routing. Responses containing secrets or code remain text-only; long responses are summarized for speech while full text stays visible.

Strict privacy enforces local-only processing, no raw retention, and minimal metadata. Standard prefers local processing. Diagnostic adds local metadata but never enables recording. Retention requires explicit opt-in and remains bounded. Audio bytes and full transcripts are not logged.

## Commands

Commands include `voice status`, `on`, `off`, `listen`, `stop`, `cancel`, `interrupt`, `session`, `devices`, `backend`, `device`, `input`, `output`, `say`, `transcribe`, `mode`, `privacy`, `language`, `rate`, `volume`, `raw-audio`, `limits`, and `health`. Commands remain on the existing Command Engine path.

## Limitations

Push-to-talk state is implemented, but real microphone capture requires a future registered Windows capture adapter. Offline transcription remains unavailable unless a supported engine and model already exist. SAPI cancellation is cooperative at the process boundary; generated acceptance WAV files are local runtime artifacts and are not committed.
