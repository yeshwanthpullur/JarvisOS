# Web Automation Foundation

## Purpose

Web Automation provides a governed boundary for future browser work. The CLI, planners, tools, agents, and providers must send web requests through `WebAutomationManager`; adapters do not receive authority from page content or model output.

## Current Capability

The foundation validates HTTPS URLs, resolves public hostnames, blocks local/internal and credential-bearing targets, classifies action risk, checks scoped permissions, normalizes results, maintains bounded redacted audit history, and exposes read-only CLI commands. `ReadOnlyWebInspectionAdapter` performs real text-only public page inspection with the Python standard library. No browser window is launched.

Allowed operations are status, bounded URL inspection, title/current URL reads, ephemeral snapshot metadata, metadata summary, and session close. Only title, safe metadata, response size, redirect domains, and a sanitized preview are retained in memory. Raw HTML, page content, cookies, profiles, downloads, and screenshots are never persisted.

## Blocked Actions

Clicking, typing, form submission, downloading, uploading, login, purchase, message sending, deletion, and account changes are blocked before adapter dispatch. CAPTCHA, paywall, login-gate, or platform-protection bypass is prohibited. These operations need a future explicit approval flow and a separately verified adapter.

## Commands

```text
web status
web policy
web session
web open <https-url>
web title
web url
web snapshot
web audit
web close
```

The default configuration enables HTTPS read-only network inspection. Adapter errors remain truthful and do not fall back to provider-generated page claims.

## URL Policy

Only `http` and `https` syntax is accepted, and normal operation requires HTTPS. Plain HTTP plus local/private targets may be enabled only for deterministic tests. User information, sensitive query fields, loopback/private/link-local/reserved/metadata addresses, unsupported schemes, and policy-sensitive categories are rejected. Hostnames are resolved before fetching, and every redirect and final URL is revalidated. Redirects are limited to five.

## Audit And Privacy

Audit records contain request/action identifiers, timestamp, risk, requested/final safe domains, policy decision, result status, redirect count, content type, byte count, error code, and a bounded summary. They exclude passwords, tokens, cookies, full URLs with sensitive queries, raw HTML, page content, screenshots, form values, and private messages. Runtime audit state lives under ignored `data/web-automation/` storage.

## Limits

Default limits are an 8-second timeout, 5 redirects, 512 KiB response, 2,000-character preview, 200-character title, and 100 audit entries. Only HTML, plain text, and XHTML are inspected. Sessions exist only in runtime memory.

## Known Limitations

- Read-only inspection is HTTP fetching, not a visual or JavaScript browser.
- Login-required and dynamically rendered pages are unavailable.
- Interactive and sensitive actions remain unavailable.
- No autonomous browsing is enabled.
- Mobile automation and full remote sync are outside this milestone.
