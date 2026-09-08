"""Provider-neutral, bounded crawler adapters for untrusted read-only content."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
import importlib.util
from typing import Callable, Protocol
from urllib.parse import urljoin

from .runtime import _INJECTION, normalize_url


class CrawlerState(StrEnum):
    READY = "ready"
    DEGRADED = "degraded"
    UNCONFIGURED = "unconfigured"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class CrawlerRecord:
    crawler_id: str
    backend: str
    installed: bool
    configured: bool
    healthy: bool
    locality: str
    requires_secret: bool
    capabilities: tuple[str, ...]
    state: CrawlerState
    limits: tuple[tuple[str, int], ...]
    reason: str
    last_health_check: str = ""


@dataclass(frozen=True, slots=True)
class NormalizedCrawlResult:
    source_url: str
    final_url: str
    title: str
    status: str
    content_type: str
    retrieved_at: str
    raw_reference: str
    clean_text: str
    markdown: str
    links: tuple[str, ...]
    metadata: tuple[tuple[str, str], ...]
    crawl_backend: str
    errors: tuple[str, ...] = ()
    trust: str = "untrusted_external"


class CrawlerAdapter(Protocol):
    crawler_id: str
    def detect(self) -> CrawlerRecord: ...
    def health(self) -> CrawlerRecord: ...
    def fetch(self, url: str, *, timeout: int = 15, max_chars: int = 20_000) -> NormalizedCrawlResult: ...
    def crawl(self, url: str, *, max_depth: int = 1, max_pages: int = 5, timeout: int = 15, max_chars: int = 20_000) -> tuple[NormalizedCrawlResult, ...]: ...
    def cancel(self) -> None: ...
    def capabilities(self) -> tuple[str, ...]: ...


Fetcher = Callable[[str, int], dict[str, object]]


@dataclass(slots=True)
class BoundedCrawlerAdapter:
    crawler_id: str
    backend: str
    locality: str
    requires_secret: bool = False
    configured: bool = True
    installed: bool = True
    fetcher: Fetcher | None = None
    _cancelled: bool = False
    max_depth_limit: int = 2
    max_pages_limit: int = 10

    def capabilities(self) -> tuple[str, ...]:
        return ("fetch", "crawl", "extract", "cancel", "read_only")

    def detect(self) -> CrawlerRecord:
        ready = self.installed and self.configured and self.fetcher is not None
        state = CrawlerState.READY if ready else CrawlerState.UNCONFIGURED if self.installed and not self.configured else CrawlerState.DEGRADED if self.installed else CrawlerState.UNAVAILABLE
        reason = "Ready for bounded read-only retrieval." if ready else "Adapter metadata is available but a live bounded fetch function is not configured."
        return CrawlerRecord(self.crawler_id, self.backend, self.installed, self.configured, ready, self.locality, self.requires_secret, self.capabilities(), state, (("max_depth", self.max_depth_limit), ("max_pages", self.max_pages_limit)), reason, datetime.now(UTC).isoformat())

    def health(self) -> CrawlerRecord:
        return self.detect()

    def fetch(self, url: str, *, timeout: int = 15, max_chars: int = 20_000) -> NormalizedCrawlResult:
        normalized = normalize_url(url)
        timeout = max(1, min(int(timeout), 60)); max_chars = max(256, min(int(max_chars), 100_000))
        if self._cancelled:
            return self._error(normalized, "cancelled")
        if self.fetcher is None or not self.configured:
            return self._error(normalized, "crawler_unconfigured")
        try:
            raw = self.fetcher(normalized, timeout)
            text = " ".join(str(raw.get("text", "")).split())
            errors: list[str] = []
            if len(text) > max_chars:
                text = text[: max_chars - 3] + "..."; errors.append("content_truncated")
            if _INJECTION.search(text):
                errors.append("prompt_injection_content_untrusted")
            links = []
            for link in tuple(raw.get("links", ()))[:100]:
                try: links.append(normalize_url(urljoin(normalized, str(link))))
                except ValueError: continue
            links = list(dict.fromkeys(links))
            return NormalizedCrawlResult(normalized, normalize_url(str(raw.get("final_url", normalized))), str(raw.get("title", ""))[:300], str(raw.get("status", "retrieved"))[:40], str(raw.get("content_type", "text/html"))[:100], datetime.now(UTC).isoformat(), f"crawl:{self.crawler_id}:{abs(hash(normalized))}", text, str(raw.get("markdown", ""))[:max_chars], tuple(links), (("robots_policy", "respected_by_adapter"),), self.crawler_id, tuple(errors))
        except (TimeoutError, OSError, ValueError, TypeError) as exc:
            return self._error(normalized, f"{type(exc).__name__}:retrieval_failed")

    def crawl(self, url: str, *, max_depth: int = 1, max_pages: int = 5, timeout: int = 15, max_chars: int = 20_000) -> tuple[NormalizedCrawlResult, ...]:
        depth_limit = max(0, min(int(max_depth), self.max_depth_limit)); page_limit = max(1, min(int(max_pages), self.max_pages_limit))
        queue = [(normalize_url(url), 0)]; seen: set[str] = set(); results = []
        while queue and len(results) < page_limit and not self._cancelled:
            current, depth = queue.pop(0)
            if current in seen: continue
            seen.add(current)
            result = self.fetch(current, timeout=timeout, max_chars=max_chars); results.append(result)
            if depth < depth_limit and result.status == "retrieved":
                queue.extend((link, depth + 1) for link in result.links if link not in seen)
        return tuple(results)

    def cancel(self) -> None:
        self._cancelled = True

    def _error(self, url: str, error: str) -> NormalizedCrawlResult:
        return NormalizedCrawlResult(url, url, "", "cancelled" if error == "cancelled" else "error", "", datetime.now(UTC).isoformat(), "", "", "", (), (), self.crawler_id, (error,))


class Crawl4AIAdapter(BoundedCrawlerAdapter):
    def __init__(self, fetcher: Fetcher | None = None) -> None:
        installed = importlib.util.find_spec("crawl4ai") is not None
        super().__init__("crawl4ai", "crawl4ai", "local", False, True, installed, fetcher)


class FirecrawlAdapter(BoundedCrawlerAdapter):
    def __init__(self, *, configured: bool = False, fetcher: Fetcher | None = None) -> None:
        super().__init__("firecrawl", "firecrawl", "cloud_optional", True, configured, True, fetcher)


@dataclass(slots=True)
class CrawlerRegistry:
    adapters: dict[str, CrawlerAdapter] = field(default_factory=dict)

    def register(self, adapter: CrawlerAdapter) -> None:
        if adapter.crawler_id in self.adapters: raise ValueError("duplicate_crawler")
        self.adapters[adapter.crawler_id] = adapter

    def get(self, crawler_id: str) -> CrawlerAdapter | None: return self.adapters.get(crawler_id)
    def list(self) -> tuple[CrawlerRecord, ...]: return tuple(self.adapters[key].detect() for key in sorted(self.adapters))
    def ready(self) -> tuple[CrawlerAdapter, ...]: return tuple(adapter for adapter in self.adapters.values() if adapter.detect().state is CrawlerState.READY)
    def summary(self) -> dict[str, object]:
        values = self.list(); return {"registered": len(values), "ready": sum(item.state is CrawlerState.READY for item in values), "states": {item.crawler_id: item.state.value for item in values}}


def build_default_crawler_registry() -> CrawlerRegistry:
    registry = CrawlerRegistry(); registry.register(Crawl4AIAdapter()); registry.register(FirecrawlAdapter(configured=False)); return registry
