# Communication Providers

Foundation profiles cover manual copy, local notification, a test stub, Telegram, Discord, SMTP/API email, Slack, Matrix, and future WhatsApp, SMS, social, and webhook families. Prompt 73 implements only Telegram text transport; it is not ready until explicitly enabled, authenticated, paired, and reachable. Every other external provider remains unavailable.

Provider state distinguishes registration, configuration, credential presence, authentication, reachability, readiness, degradation, rate limiting, blocking, disabling, and unavailability. Health checks are metadata-only and never send a test message.
