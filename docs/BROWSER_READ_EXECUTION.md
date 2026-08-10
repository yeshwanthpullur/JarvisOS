# Controlled Browser Read Execution

The controlled browser executor performs bounded public HTTP(S) GET requests only. It validates DNS and every resolved address to block loopback, private, link-local, metadata, and unsupported-port targets. Redirects are revalidated.

No cookies, authentication, JavaScript execution, forms, uploads, downloads, browser writes, or account actions are supported. Responses are bounded and reduced to safe text metadata. Use `browser execute read <url>` only through approval and broker policy.
