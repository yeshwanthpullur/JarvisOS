# Release Checklist

Use this checklist for every JARVIS OS release. Record exact results in the release notes or task report.

## Scope

- [ ] Release scope and authority boundaries are defined.
- [ ] Current status, roadmap, health scorecard, and machine-readable health are updated.
- [ ] `docs/JARVIS_USE_CASES.md` still matches product direction, safety boundaries, and milestone ownership.
- [ ] `CHANGELOG.md` includes the release version and verified limitations.
- [ ] `docs/LIMITATIONS_REGISTER.md` and `docs/limitations_register.json` have consistent counts and owners.
- [ ] Limitation review categories reconcile, fixed records include evidence and tests, and bounded CLI status matches project health.
- [ ] Limitation review categories reconcile, fixed records include evidence and tests, and bounded CLI status matches project health.

## Repository Safety

- [ ] `git status --short` has no unintended tracked changes.
- [ ] Every changed file belongs to the release.
- [ ] `.env`, API keys, credentials, private endpoints, and tokens are not staged.
- [ ] Logs, WAV/audio files, databases, caches, backups, screenshots, and runtime artifacts are not staged.
- [ ] `git diff --check` passes.
- [ ] Staged file names and staged diff are reviewed before commit.

## Verification

- [ ] Changed Python files compile.
- [ ] Focused subsystem tests pass with exact totals recorded.
- [ ] Full suite passes; passed, skipped, failed, and errors are reported separately.
- [ ] Normal CLI startup and shutdown pass.
- [ ] Relevant real local acceptance tests pass.
- [ ] Manual verification is completed and its observable results are recorded.
- [ ] Local model, microphone, voice playback, and vision acceptance evidence is recorded without committing models or media.
- [ ] Vercel remains status-only and exposes no local AI execution or upload endpoint.
- [ ] Paid/external integrations use mocks unless an explicit live test was authorized.
- [ ] Deployment entrypoints are isolated from local launchers, live health URLs are checked, and duplicate connected projects are reviewed.
- [ ] Security, permissions, local-only policy, and command separation are verified.
- [ ] Sync queue artifacts remain ignored; safe schemas, secret/path rejection, offline behavior, conflict handling, and bounded retention are verified.
- [ ] Web automation URLs, permissions, blocked sensitive actions, audit redaction, and browser runtime artifact exclusions are verified.

## Release

- [ ] Release commit exists on the intended branch and remote.
- [ ] Annotated tag points to the exact verified commit.
- [ ] Tag push succeeds.
- [ ] Release title and notes match the tag and changelog.
- [ ] Release is marked prerelease/stable correctly.
- [ ] Release URL and remote tag are verified.
- [ ] Final working tree has no unintended tracked changes.
