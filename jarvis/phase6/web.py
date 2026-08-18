"""Bounded browser/crawler policy and metadata sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from urllib.parse import urlparse
from uuid import uuid4
import ipaddress


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WebAction(StrEnum):
    READ_PUBLIC_PAGE = "read_public_page"; SEARCH_PUBLIC_WEB = "search_public_web"; CRAWL_PUBLIC_SITE = "crawl_public_site"; EXTRACT_PUBLIC_CONTENT = "extract_public_content"; OPEN_BROWSER_PAGE = "open_browser_page"; SCREENSHOT_PAGE = "screenshot_page"; CLICK_LINK = "click_link"; FILL_FORM = "fill_form"; LOGIN = "login"; UPLOAD_FILE = "upload_file"; DOWNLOAD_FILE = "download_file"; SUBMIT_FORM = "submit_form"; SEND_MESSAGE = "send_message"; POST_CONTENT = "post_content"; PURCHASE = "purchase"; DELETE_OR_MODIFY_REMOTE_CONTENT = "delete_or_modify_remote_content"; ACCOUNT_SETTING_CHANGE = "account_setting_change"; UNKNOWN = "unknown"


LOW_RISK = {WebAction.READ_PUBLIC_PAGE, WebAction.SEARCH_PUBLIC_WEB, WebAction.CRAWL_PUBLIC_SITE, WebAction.EXTRACT_PUBLIC_CONTENT}
MEDIUM_RISK = {WebAction.OPEN_BROWSER_PAGE, WebAction.SCREENSHOT_PAGE, WebAction.CLICK_LINK, WebAction.DOWNLOAD_FILE, WebAction.UPLOAD_FILE}
HIGH_RISK = set(WebAction) - LOW_RISK - MEDIUM_RISK - {WebAction.UNKNOWN}


@dataclass(frozen=True, slots=True)
class CrawlLimits:
    max_pages: int = 5; max_depth: int = 1; max_runtime_seconds: int = 60; max_content_bytes: int = 1_000_000; max_download_bytes: int = 10_000_000; max_concurrent_requests: int = 2; retry_limit: int = 1; timeout_seconds: int = 15; requests_per_minute: int = 10


@dataclass(frozen=True, slots=True)
class BrowserDecision:
    action: WebAction; allowed: bool; approval_required: bool; risk: str; reason: str


@dataclass(slots=True)
class BrowserSession:
    session_id: str; tool: str; purpose: str; allowed_domains: tuple[str, ...]; requested_by: str = "user"; started_at: str = field(default_factory=_now); ended_at: str = ""; current_url: str = ""; actions_taken: int = 0; approval_events: int = 0; downloads: int = 0; uploads: int = 0; screenshots: int = 0; errors: int = 0; status: str = "planned"


@dataclass(frozen=True, slots=True)
class CrawlPlan:
    crawl_id: str; safe_domain: str; tool: str; limits: CrawlLimits; status: str; approval_required: bool; reason: str


class WebControlPlane:
    def __init__(self, *, network_allowed: bool = False, browser_enabled: bool = False, crawler_enabled: bool = False, limits: CrawlLimits | None = None) -> None:
        self.network_allowed = network_allowed; self.browser_enabled = browser_enabled; self.crawler_enabled = crawler_enabled; self.limits = limits or CrawlLimits(); self.sessions: dict[str, BrowserSession] = {}; self.crawls: dict[str, CrawlPlan] = {}; self.audit: list[dict[str, object]] = []

    def classify(self, action: str) -> WebAction:
        normalized = action.strip().lower().replace(" ", "_")
        return next((item for item in WebAction if item.value == normalized), WebAction.UNKNOWN)

    def decide(self, action: WebAction, *, approved: bool = False) -> BrowserDecision:
        if action is WebAction.UNKNOWN:
            return BrowserDecision(action, False, False, "unknown", "Unknown web action is blocked.")
        if action in HIGH_RISK:
            return BrowserDecision(action, False, True, "high", "High-risk online actions are disabled in Phase 6 even when approval metadata exists.")
        if action in MEDIUM_RISK:
            allowed = self.browser_enabled and approved
            return BrowserDecision(action, allowed, True, "medium", "Controlled browser and exact approval are required." if not allowed else "Approved for broker validation; no action has run.")
        allowed = self.network_allowed
        return BrowserDecision(action, allowed, False, "low", "Read-only network policy is disabled." if not allowed else "Read-only policy allows broker validation.")

    def validate_url(self, url: str) -> tuple[bool, str]:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            return False, "Only public HTTPS URLs are allowed."
        try:
            ip = ipaddress.ip_address(parsed.hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False, "Local and private network targets are blocked."
        except ValueError:
            pass
        return True, parsed.hostname.lower()

    def plan_crawl(self, url: str) -> CrawlPlan:
        valid, value = self.validate_url(url)
        status = "planned" if valid else "blocked"
        tool = "crawl4ai" if self.crawler_enabled else "read_only_fallback"
        plan = CrawlPlan(f"crawl-{uuid4().hex[:10]}", value if valid else "", tool, self.limits, status, False, "Bounded plan only; robots, terms, rate, and source policy must be rechecked before retrieval." if valid else value)
        self.crawls[plan.crawl_id] = plan; self.audit.append({"action": "crawl_plan", "crawl_id": plan.crawl_id, "status": status, "domain": plan.safe_domain, "at": _now()}); self.audit = self.audit[-100:]
        return plan

    def run_crawl(self, url: str) -> CrawlPlan:
        plan = self.plan_crawl(url)
        if plan.status == "blocked":
            return plan
        status = "unavailable" if not self.network_allowed or not self.crawler_enabled else "broker_required"
        result = CrawlPlan(plan.crawl_id, plan.safe_domain, plan.tool, plan.limits, status, False, "Crawler execution is unavailable." if status == "unavailable" else "Route the bounded read through policy and Broker; direct execution is not permitted here.")
        self.crawls[result.crawl_id] = result
        return result

    def close(self, session_id: str) -> bool:
        session = self.sessions.get(session_id)
        if session is None:
            return False
        session.status = "closed"; session.ended_at = _now(); return True

    def expire_sessions(self, minutes: int = 10) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=max(1, minutes)); count = 0
        for session in self.sessions.values():
            if session.status not in {"closed", "expired"} and datetime.fromisoformat(session.started_at) < cutoff:
                session.status = "expired"; session.ended_at = _now(); count += 1
        return count

    def status(self) -> dict[str, object]:
        return {"browser_enabled": self.browser_enabled, "network_allowed": self.network_allowed, "crawler_enabled": self.crawler_enabled, "sessions": len(self.sessions), "crawls": len(self.crawls), "high_risk_actions": "blocked", "execution_authority": False}
