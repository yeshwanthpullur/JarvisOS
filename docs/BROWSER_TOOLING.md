# Browser Tooling

Prompt 90 adds public-HTTPS URL validation, bounded crawl plans, session metadata, and fail-closed high-risk action policy. Interactive actions require exact approval and remain unavailable in the Phase 6 adapter; login, form submission, purchase, upload, download, and remote modification are blocked.

Browser Use, Playwright, Crawl4AI, and Firecrawl are optional isolated tools. The current safe fallback is bounded read-only HTTP/web inspection. Detection does not authorize navigation, login, form submission, downloads, uploads, purchases, browser writes, or background crawling.
