"""Metadata-first plugin registry; no arbitrary plugin code is loaded here."""
from __future__ import annotations

import hashlib
from collections import deque
from dataclasses import replace
from typing import Any

from .models import *

PROTECTED_SKILLS = {"execution_policy_skill", "approval_request_skill", "broker_validation_skill"}
PROTECTED_AGENTS = {"prime_agent", "executive_jarvis", "security_agent", "memory_agent"}
SIDE_EFFECT_PERMISSIONS = {PluginPermission.NETWORK_WRITE, PluginPermission.FILESYSTEM_WRITE, PluginPermission.EXTERNAL_SEND, PluginPermission.EXTERNAL_MODIFY, PluginPermission.COMMAND_EXECUTE}


class PluginRegistry:
    def __init__(self, policy: PluginPolicy | None = None, *, jarvis_version: str = "1.7.0-alpha", approval_validator=None) -> None:
        self.policy = policy or PluginPolicy(); self.jarvis_version = jarvis_version; self.records: dict[str, PluginRecord] = {}
        self.approval_validator = approval_validator
        self.history: deque[dict[str, str]] = deque(maxlen=self.policy.max_history_items)

    def register(self, manifest: PluginManifest, *, origin: PluginOrigin = PluginOrigin.EXTERNAL_UNREVIEWED) -> PluginRecord:
        if manifest.plugin_id in self.records: raise ValueError("duplicate_plugin_id")
        if len(self.records) >= self.policy.max_registered: raise ValueError("plugin_registry_limit")
        if set(manifest.declared_skills) & PROTECTED_SKILLS: raise ValueError("protected_skill_override")
        if set(manifest.declared_agents) & PROTECTED_AGENTS: raise ValueError("protected_agent_override")
        state = PluginState.REGISTERED if origin in {PluginOrigin.BUILTIN, PluginOrigin.FIRST_PARTY} else PluginState.UNTRUSTED
        trust = PluginTrust.TRUSTED_METADATA if origin in {PluginOrigin.BUILTIN, PluginOrigin.FIRST_PARTY} else PluginTrust.UNTRUSTED
        record = PluginRecord(manifest, origin, state, trust, reason="Registered metadata only; no code executed.")
        self.records[manifest.plugin_id] = record; self._audit(manifest.plugin_id, "register", state.value); return record

    def get(self, plugin_id: str) -> PluginRecord | None: return self.records.get(plugin_id)
    def list(self) -> tuple[PluginRecord, ...]: return tuple(self.records.values())[:self.policy.max_registered]

    def verify(self, plugin_id: str, *, content: bytes | None = None, available_credentials: tuple[str, ...] = ()) -> PluginVerification:
        record = self.get(plugin_id)
        if not record: return PluginVerification(plugin_id, False, False, "unknown", "unknown", (), (), (), ("plugin_not_found",))
        m = record.manifest; blocked: list[str] = []
        current = self._version_tuple(self.jarvis_version); minimum = self._version_tuple(m.minimum_jarvis_version); maximum = self._version_tuple(m.maximum_jarvis_version)
        record.compatible = not ((minimum and current < minimum) or (maximum and current > maximum))
        if not record.compatible: blocked.append("jarvis_version_incompatible")
        if m.runtime_type is PluginRuntimeType.PYTHON_INPROCESS and record.origin is not PluginOrigin.BUILTIN: blocked.append("external_inprocess_disabled")
        if m.runtime_type in {PluginRuntimeType.PYTHON_SUBPROCESS, PluginRuntimeType.EXTERNAL_PROCESS} and not self.policy.allow_subprocess: blocked.append("subprocess_disabled")
        if m.network_requirements and not self.policy.allow_network: blocked.append("network_disabled")
        if any("write" in x for x in m.filesystem_requirements) and not self.policy.allow_filesystem_write: blocked.append("filesystem_write_disabled")
        missing_deps = tuple(x.name for x in m.dependencies if x.required and not x.installed)
        missing_creds = tuple(x for x in m.required_credentials if x not in available_credentials)
        expected = m.provenance.checksum_sha256.lower(); integrity = "not_provided"
        if expected:
            integrity = "not_checked" if content is None else "verified" if hashlib.sha256(content).hexdigest() == expected else "mismatch"
            if integrity == "mismatch": blocked.append("checksum_mismatch")
        risks = tuple(x.value for x in m.declared_permissions if x in SIDE_EFFECT_PERMISSIONS)
        if missing_deps: blocked.append("dependency_missing")
        if missing_creds: blocked.append("credential_missing")
        valid = not blocked
        if blocked:
            record.state = PluginState.BLOCKED if "checksum_mismatch" in blocked or "external_inprocess_disabled" in blocked else PluginState.REVIEW_REQUIRED
            record.reason = blocked[0]
        elif integrity == "verified": record.state = PluginState.VERIFIED; record.trust = PluginTrust.INTEGRITY_VERIFIED
        self._audit(plugin_id, "verify", "passed" if valid else "blocked")
        return PluginVerification(plugin_id, valid, record.compatible, integrity, m.provenance.signature_status, missing_deps, missing_creds, risks, tuple(blocked))

    def enable_plan(self, plugin_id: str) -> str:
        record = self.get(plugin_id)
        if not record: return "plugin_not_found"
        if record.state not in {PluginState.VERIFIED, PluginState.REGISTERED}: return f"blocked:{record.state.value}"
        return "approval_required; exact plugin ID, version, capabilities, permissions, and integrity must match"

    def enable(self, plugin_id: str, approval_id: str = "") -> str:
        record = self.get(plugin_id)
        if not record: return "plugin_not_found"
        if self.policy.require_approval_for_enable and (not approval_id or not self.approval_validator or not self.approval_validator(approval_id, record.manifest.plugin_id, record.manifest.version, tuple(x.value for x in record.manifest.declared_permissions))): return "approval_required_or_invalid"
        if record.state is not PluginState.VERIFIED or record.trust not in {PluginTrust.INTEGRITY_VERIFIED, PluginTrust.LOCALLY_REVIEWED, PluginTrust.TRUSTED_EXECUTION}: return "plugin_not_verified"
        if record.manifest.runtime_type is not PluginRuntimeType.DECLARATIVE: return "external_execution_disabled"
        if sum(x.enabled for x in self.records.values()) >= self.policy.max_enabled: return "plugin_enabled_limit"
        record.enabled = True; record.state = PluginState.ENABLED; self._audit(plugin_id, "enable", "enabled"); return "enabled_metadata_only"

    def disable(self, plugin_id: str, approval_id: str = "") -> str:
        record = self.get(plugin_id)
        if not record: return "plugin_not_found"
        if self.policy.require_approval_for_enable and (not approval_id or not self.approval_validator or not self.approval_validator(approval_id, record.manifest.plugin_id, record.manifest.version, ())): return "approval_required_or_invalid"
        record.enabled = False; record.state = PluginState.DISABLED; self._audit(plugin_id, "disable", "disabled"); return "disabled"

    def summary(self) -> dict[str, Any]:
        values = self.list()
        return {"implemented": True, "registered": len(values), "enabled": sum(x.enabled for x in values), "blocked": sum(x.state is PluginState.BLOCKED for x in values), "untrusted": sum(x.trust is PluginTrust.UNTRUSTED for x in values), "external_execution": False, "installation": False, "updates": False, "scheduled_execution": False}

    def _audit(self, plugin_id: str, action: str, status: str) -> None:
        if self.policy.save_history: self.history.append({"plugin_id": plugin_id, "action": action, "status": status})

    @staticmethod
    def _version_tuple(value: str) -> tuple[int, int, int] | tuple[()]:
        if not value:return ()
        text=value.lstrip("v").split("-",1)[0]
        try:return tuple(int(x) for x in text.split(".")[:3])  # type: ignore[return-value]
        except ValueError:return ()


class PluginRuntime:
    """Planning and validation facade. Deliberately has no arbitrary execute method."""
    def __init__(self, registry: PluginRegistry | None = None): self.registry = registry or PluginRegistry()
    def status(self) -> dict[str, Any]: return self.registry.summary()
    def install_plan(self, source: str) -> str: return "installation_disabled; inspect provenance, manifest, integrity, dependencies, and permissions first"
    def update_plan(self, plugin_id: str) -> str: return "updates_disabled; compare version, integrity, permissions, dependencies, and rollback before approval"
    def uninstall_plan(self, plugin_id: str) -> str: return "uninstall_execution_disabled; disable first and preserve bounded metadata"


def render_plugin_command(command: str, args: tuple[str, ...], runtime: PluginRuntime) -> str:
    op = command.split(maxsplit=1)[1] if " " in command else "status"; registry = runtime.registry
    if op == "help": return "Plugin: status|list|show|inspect|capabilities|permissions|dependencies|health|history|enable-plan|enable|disable-plan|disable|install-plan|update-plan|uninstall-plan|verify"
    if op == "status": return "Plugin runtime: " + " ".join(f"{k}={str(v).lower() if isinstance(v,bool) else v}" for k,v in runtime.status().items())
    if op == "list": return "plugin list: " + (", ".join(f"{x.manifest.plugin_id}:{x.state.value}" for x in registry.list()) or "none")
    if op == "history": return "Plugin history: " + ("; ".join(f"{x['plugin_id']}:{x['action']}:{x['status']}" for x in registry.history) or "none")
    plugin_id = args[0] if args else ""
    record = registry.get(plugin_id)
    if op == "install-plan": return "Plugin install plan: " + runtime.install_plan(plugin_id)
    if op == "update-plan": return "Plugin update plan: " + runtime.update_plan(plugin_id)
    if op == "uninstall-plan": return "Plugin uninstall plan: " + runtime.uninstall_plan(plugin_id)
    if op == "enable-plan": return f"Plugin enable plan: {registry.enable_plan(plugin_id)} executed=no"
    if op == "disable-plan": return "Plugin disable plan: approval_required executed=no"
    if op == "enable": return f"Plugin enable: {registry.enable(plugin_id)} executed=no"
    if op == "disable": return f"Plugin disable: {registry.disable(plugin_id)} executed=no"
    if op == "verify":
        result = registry.verify(plugin_id); return f"Plugin verify: id={plugin_id or 'missing'} valid={str(result.valid).lower()} integrity={result.integrity} signature={result.signature} blocked={','.join(result.blocked_reasons) or 'none'} executed=no"
    if not record: return "Plugin not found."
    m = record.manifest
    if op in {"show", "inspect"}: return f"Plugin: id={m.plugin_id} version={m.version} type={m.plugin_type.value} runtime={m.runtime_type.value} state={record.state.value} trust={record.trust.value} enabled={str(record.enabled).lower()}"
    if op == "capabilities": return "Plugin capabilities: " + (", ".join(m.declared_capabilities[:20]) or "none")
    if op == "permissions": return "Plugin permissions requested (not granted): " + (", ".join(x.value for x in m.declared_permissions[:20]) or "none")
    if op == "dependencies": return "Plugin dependencies: " + (", ".join(f"{x.name}:{'ready' if x.installed and x.verified else 'missing/unverified'}" for x in m.dependencies[:20]) or "none")
    if op == "health": return f"Plugin health: {record.health}; runtime execution is disabled unless individually trusted and authorized."
    return "plugin help"
