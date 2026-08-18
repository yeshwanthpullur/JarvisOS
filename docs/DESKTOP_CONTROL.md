# Desktop Control

Desktop control is a disabled-by-default adapter boundary. `app list`, `app open`, and `app close` expose bounded metadata or action previews only. The Phase 6 control plane does not drive the mouse, keyboard, screen, clipboard, camera, microphone, or arbitrary applications.

Future desktop actions must use allowlisted targets, scoped approval, Broker dispatch, bounded timeouts, rollback metadata where practical, and local audit metadata without private content.
