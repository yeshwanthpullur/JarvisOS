# Browser Agent

## Controlled Read Execution

Phase 4 adds an approval-gated public HTTP(S) GET executor with DNS/IP and redirect checks. Interactive browsing, authentication, cookies, JavaScript, forms, uploads, downloads, and account actions remain disabled.

Prompt 54 adds a read-only Browser Agent foundation for source policy, capability diagnostics, and bounded webpage-summary planning. It may compose with the existing read-only web subsystem when explicitly invoked.

Interactive browser control, login, forms, account actions, purchases, downloads, cookies, sessions, CAPTCHA bypass, and browser writes are disabled. No browser executable is launched by this foundation.

Commands: `browser status`, `help`, `plan`, `safety`, `capabilities`, `sources`, `summarize`, `show`, and `history`.
