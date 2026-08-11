# Email Connector

Prompt 74 adds outbound plain-text email models for SMTP and a future provider-specific API mode. Initial scope is one validated recipient, bounded subject/body, header-injection rejection, duplicate protection, and exact approved sending. Inbox access, OAuth flows, HTML, CC/BCC, attachments, lists, bulk delivery, and scheduled delivery remain disabled.

SMTP host, port, username, password, sender, and API token are runtime references only. Readiness requires complete configuration and a non-sending authentication/connection check; host resolution alone is insufficient. Every send passes `email_send_tool`; ambiguous failures are not blindly retried.

