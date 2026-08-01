# Web Automation Foundation

## Purpose

Web Automation provides a governed boundary for future browser work. The CLI, planners, tools, agents, and providers must send web requests through `WebAutomationManager`; adapters do not receive authority from page content or model output.

## Current Capability

The foundation validates HTTP(S) URLs, blocks local/internal and credential-bearing targets by default, classifies action risk, checks scoped permissions, normalizes results, maintains bounded redacted audit history, and exposes read-only CLI commands. The default adapter is intentionally unavailable. No browser is launched and no page is claimed as opened unless a real adapter completes the request.

Allowed foundation actions are status, open URL, title/current URL reads, ephemeral snapshot metadata, metadata summary, and session close. Page content and screenshots are not persisted by default.

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

With the default configuration, status and policy remain usable while browser operations return a truthful unavailable or disabled result.

## URL Policy

Only `http` and `https` are accepted. User information in URLs, loopback/private/link-local/reserved hosts, unsupported schemes, and policy-sensitive categories are rejected. A future adapter must apply the same policy to every redirect and must not downgrade secure navigation silently.

## Audit And Privacy

Audit records contain request/action identifiers, timestamp, risk, safe domain, policy decision, result status, and a bounded summary. They exclude passwords, tokens, cookies, full page content, screenshots, form values, private messages, and sensitive URL query data. Runtime audit state lives under ignored `data/web-automation/` storage.

## Limits

Audit retention and action timeout are bounded by configuration. Sessions exist only in runtime memory. No persistent browser profile, cookie jar, download directory, or screenshot store is created by this foundation.

## Known Limitations

- No production browser adapter is configured.
- No real page is opened in the default environment.
- Redirect revalidation is an adapter requirement and must be proven before a real adapter is enabled.
- Interactive and sensitive actions remain unavailable.
- Mobile automation and full remote sync are outside this milestone.
