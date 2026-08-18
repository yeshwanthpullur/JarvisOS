"""Normalized connector metadata over existing MCP, plugin, and provider systems."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class ConnectorRecord:
    connector_id: str; name: str; category: str; adapter_type: str; source: str; version: str; installed: bool; discovered: bool; configured: bool; credentials_present: bool; enabled: bool; policy_allowed: bool; approval_required: bool; authenticated: bool; healthy: bool; connected: bool; permissions: tuple[str, ...]; capabilities: tuple[str, ...]; credential_reference: str = ""; environment: str = "core"; trust_level: str = "untrusted"; last_checked: str = ""; last_error: str = ""


class ConnectorRegistry:
    def __init__(self) -> None:
        checked = datetime.now(timezone.utc).isoformat()
        self._records = {item.connector_id: item for item in (
            ConnectorRecord("github", "GitHub", "SOURCE_CONTROL", "provider", "builtin", "1", True, True, False, False, False, False, True, False, False, False, ("github_read",), ("repository_metadata", "commit_history"), "GITHUB_TOKEN", trust_level="builtin", last_checked=checked),
            ConnectorRecord("telegram", "Telegram", "COMMUNICATION", "provider", "builtin", "1", True, True, False, False, False, False, True, False, False, False, ("send_message",), ("text_message",), "TELEGRAM_BOT_TOKEN", trust_level="builtin", last_checked=checked),
            ConnectorRecord("discord", "Discord", "COMMUNICATION", "provider", "builtin", "1", True, True, False, False, False, False, True, False, False, False, ("send_message",), ("text_message",), "DISCORD_BOT_TOKEN", trust_level="builtin", last_checked=checked),
            ConnectorRecord("email", "Email", "COMMUNICATION", "provider", "builtin", "1", True, True, False, False, False, False, True, False, False, False, ("send_email",), ("email_draft",), "SMTP_PASSWORD", trust_level="builtin", last_checked=checked),
            ConnectorRecord("slack", "Slack", "COMMUNICATION", "provider", "builtin", "1", True, True, False, False, False, False, True, False, False, False, ("send_message",), ("text_message",), "SLACK_BOT_TOKEN", trust_level="builtin", last_checked=checked),
            ConnectorRecord("mcp_local", "Local MCP", "MCP_SERVER", "mcp", "runtime", "1", True, True, False, False, False, False, True, False, False, False, ("resource_read",), ("resource_discovery", "tool_discovery"), trust_level="registered_untrusted", last_checked=checked),
            ConnectorRecord("external_plugin", "External Plugin", "PLUGIN", "plugin", "runtime", "1", False, True, False, False, False, False, True, False, False, False, (), ("manifest_discovery",), trust_level="untrusted", last_checked=checked),
        )}
        self.audit: list[dict[str, object]] = []

    def list(self) -> tuple[ConnectorRecord, ...]: return tuple(self._records[key] for key in sorted(self._records))
    def get(self, connector_id: str) -> ConnectorRecord | None: return self._records.get(connector_id)
    def capabilities(self) -> tuple[tuple[str, str], ...]: return tuple((item.connector_id, capability) for item in self.list() for capability in item.capabilities)
    def collisions(self) -> tuple[str, ...]:
        owners: dict[str, list[str]] = {}
        for connector, capability in self.capabilities(): owners.setdefault(capability, []).append(connector)
        return tuple(f"{capability}:{','.join(sorted(values))}" for capability, values in owners.items() if len(values) > 1)
    def test(self, connector_id: str) -> str:
        item = self.get(connector_id)
        if item is None: return "connector_not_found"
        self.audit.append({"connector_id": connector_id, "operation": "metadata_test", "result": "not_configured" if not item.configured else "health_only"}); self.audit = self.audit[-100:]
        return "not_configured" if not item.configured else "health_only"
    def summary(self) -> dict[str, object]:
        records = self.list(); return {"total": len(records), "discovered": sum(item.discovered for item in records), "configured": sum(item.configured for item in records), "enabled": sum(item.enabled for item in records), "authenticated": sum(item.authenticated for item in records), "healthy": sum(item.healthy for item in records), "collisions": len(self.collisions()), "auto_enable": False, "auto_authenticate": False}
