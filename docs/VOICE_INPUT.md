# Local Voice Input

## Current Status

Voice Input is **Working locally for explicit push-to-talk use**. Offline Vosk transcription, `sounddevice` microphone capture, an Indian-English local model, `voice listen`, and `voice listen send` have been manually verified on the current machine. Input remains off until explicitly enabled or requested, and audit records stay bounded and content-free.

This is not continuous two-way conversation. Wake word, always-listening operation, and dynamic multilingual model switching remain unavailable.

Windows SAPI voice output is independent and remains available without Vosk.

## Privacy Boundary

- The microphone is opened only by `voice listen` or `voice input test` after input is explicitly enabled.
- Wake word and continuous listening are disabled and not implemented.
- Captured PCM remains in memory and is not written to disk.
- Raw audio persistence is off by default.
- Transcript text is not written to the voice-input audit.
- Audio is never sent to a cloud speech service.
- `voice listen` displays the transcript but does not submit it automatically.
- `voice listen send` is the explicit handoff into the existing Conversation and Command engines.

## Optional Installation

Use the optional dependency file rather than changing the core runtime:

```powershell
python -m pip install -r requirements-voice.txt
```

Download a Vosk model manually from the official Vosk model source, extract it outside Git tracking, and either:

1. Place its contents under `models/vosk/`, or
2. Set the non-secret environment variable `JARVIS_VOSK_MODEL_PATH` to the extracted model directory, or
3. Set `voice.stt_model_path` in local configuration.

A valid model directory must contain at least `am/final.mdl` and `conf/model.conf`. JARVIS does not download, unpack, or commit models automatically.

## Commands

```text
voice status
voice input status
voice input on
voice input test
voice listen
voice listen send
voice transcribe <allowed-wav-path>
voice devices input
voice input off
voice cleanup
```

`voice input on` succeeds only when the Vosk dependency, model, capture adapter, and input device are ready. `voice transcribe` accepts a validated PCM WAV file and does not require a microphone. Paths remain restricted by the existing allowed-audio scope.

## Audio Requirements

The Vosk adapter accepts uncompressed mono, 16-bit PCM WAV or equivalent in-memory PCM. Capture defaults to 16 kHz mono, a maximum of 30 seconds, and a bounded silence timeout. Empty speech, unsupported formats, model errors, and capture failures produce normalized non-success statuses.

## Known Limitations

- Vosk and `sounddevice` are optional and not installed automatically.
- No model is bundled with the repository.
- Live microphone transcription has not been verified on the current machine.
- Speech playback remains synchronous.
- Wake word, continuous listening, and cloud STT are not implemented.
