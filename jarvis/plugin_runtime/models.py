"""Strict metadata models for the secure external plugin runtime."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


def _id() -> str:
    return uuid4().hex


class PluginType(str, Enum):
    PROVIDER = "provider_plugin"; SKILL = "skill_plugin"; ADAPTER = "adapter_plugin"
    INTEGRATION = "integration_plugin"; MCP = "mcp_plugin"; DOCUMENT = "document_plugin"
    RESEARCH = "research_plugin"; COMMUNICATION = "communication_plugin"; DEVELOPER = "developer_tool_plugin"


class PluginRuntimeType(str, Enum):
    DECLARATIVE = "declarative"; HTTP_ADAPTER = "http_adapter"; MCP = "mcp"
    PYTHON_SUBPROCESS = "python_subprocess"; EXTERNAL_PROCESS = "external_process"; PYTHON_INPROCESS = "python_inprocess"


class PluginState(str, Enum):
    DISCOVERED = "discovered"; REGISTERED = "registered"; DISABLED = "disabled"; UNCONFIGURED = "unconfigured"
    INCOMPATIBLE = "incompatible"; DEPENDENCY_MISSING = "dependency_missing"; CREDENTIAL_MISSING = "credential_missing"
    UNTRUSTED = "untrusted"; REVIEW_REQUIRED = "review_required"; VERIFIED = "verified"; ENABLED = "enabled"
    RUNTIME_READY = "runtime_ready"; DEGRADED = "degraded"; BLOCKED = "blocked"; ERROR = "error"


class PluginTrust(str, Enum):
    UNKNOWN = "unknown"; UNTRUSTED = "untrusted"; REVIEW_REQUIRED = "review_required"; SOURCE_VERIFIED = "source_verified"
    INTEGRITY_VERIFIED = "integrity_verified"; LOCALLY_REVIEWED = "locally_reviewed"; TRUSTED_METADATA = "trusted_for_metadata"
    TRUSTED_READ = "trusted_for_read"; TRUSTED_EXECUTION = "trusted_for_specific_execution"; BLOCKED = "blocked"


class PluginOrigin(str, Enum):
    BUILTIN = "builtin"; FIRST_PARTY = "first_party"; EXTERNAL_REVIEWED = "external_reviewed"; EXTERNAL_UNREVIEWED = "external_unreviewed"


class PluginPermission(str, Enum):
    NETWORK_READ = "network_read"; NETWORK_WRITE = "network_write"; FILESYSTEM_READ = "filesystem_read"
    FILESYSTEM_WRITE = "filesystem_write"; EXTERNAL_SEND = "external_send"; EXTERNAL_MODIFY = "external_modify"
    COMMAND_EXECUTE = "command_execute"; CREDENTIAL_REFERENCE = "credential_reference"; MCP_REGISTER = "mcp_register"


@dataclass(frozen=True, slots=True)
class PluginDependency:
    name: str; dependency_type: str; version_constraint: str = ""; required: bool = True
    source: str = ""; installed: bool = False; verified: bool = False; warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-zA-Z0-9_.-]{1,100}", self.name) or self.dependency_type not in {"plugin", "python", "node", "system", "mcp"}:
            raise ValueError("invalid_plugin_dependency")


@dataclass(frozen=True, slots=True)
class PluginProvenance:
    source_type: str = "local"; source_ref: str = ""; publisher: str = ""; commit_or_tag: str = ""
    checksum_sha256: str = ""; signature_status: str = "unsigned"; retrieved_at: str = ""


@dataclass(frozen=True, slots=True)
class PluginManifest:
    manifest_version: str; plugin_id: str; name: str; version: str; description: str; author: str
    plugin_type: PluginType; runtime_type: PluginRuntimeType = PluginRuntimeType.DECLARATIVE
    entrypoint: str = ""; minimum_jarvis_version: str = ""; maximum_jarvis_version: str = ""
    supported_platforms: tuple[str, ...] = (); declared_capabilities: tuple[str, ...] = ()
    declared_permissions: tuple[PluginPermission, ...] = (); declared_skills: tuple[str, ...] = ()
    declared_agents: tuple[str, ...] = (); declared_providers: tuple[str, ...] = (); declared_mcp_servers: tuple[str, ...] = ()
    required_credentials: tuple[str, ...] = (); network_requirements: tuple[str, ...] = ()
    filesystem_requirements: tuple[str, ...] = (); subprocess_requirements: tuple[str, ...] = ()
    dependencies: tuple[PluginDependency, ...] = (); provenance: PluginProvenance = field(default_factory=PluginProvenance)
    homepage: str = ""; source_repository: str = ""; license: str = ""; warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.manifest_version != "1.0": raise ValueError("unsupported_manifest_version")
        if not re.fullmatch(r"[a-z0-9]+(?:[._-][a-z0-9]+)+", self.plugin_id): raise ValueError("invalid_plugin_id")
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", self.version): raise ValueError("invalid_plugin_version")
        if not self.name or len(self.name) > 100 or len(self.description) > 800: raise ValueError("invalid_plugin_metadata")
        for values, error in ((self.declared_capabilities,"duplicate_plugin_capability"),(self.declared_skills,"duplicate_plugin_skill"),(self.declared_agents,"duplicate_plugin_agent")):
            if len(values) != len(set(values)): raise ValueError(error)
        if self.entrypoint and (".." in self.entrypoint.replace("\\", "/").split("/") or re.match(r"^[A-Za-z]:|^/", self.entrypoint)):
            raise ValueError("plugin_entrypoint_path_forbidden")

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "PluginManifest":
        allowed = set(cls.__dataclass_fields__)
        unknown = set(raw) - allowed
        if unknown: raise ValueError("unknown_manifest_fields:" + ",".join(sorted(unknown)[:8]))
        data = dict(raw)
        data["plugin_type"] = PluginType(data["plugin_type"])
        data["runtime_type"] = PluginRuntimeType(data.get("runtime_type", "declarative"))
        data["declared_permissions"] = tuple(PluginPermission(x) for x in data.get("declared_permissions", ()))
        data["dependencies"] = tuple(x if isinstance(x, PluginDependency) else PluginDependency(**x) for x in data.get("dependencies", ()))
        data["provenance"] = data.get("provenance", PluginProvenance()) if isinstance(data.get("provenance", PluginProvenance()), PluginProvenance) else PluginProvenance(**data["provenance"])
        for key in ("supported_platforms","declared_capabilities","declared_skills","declared_agents","declared_providers","declared_mcp_servers","required_credentials","network_requirements","filesystem_requirements","subprocess_requirements","warnings"):
            data[key] = tuple(data.get(key, ()))
        return cls(**data)


@dataclass(slots=True)
class PluginRecord:
    manifest: PluginManifest; origin: PluginOrigin = PluginOrigin.EXTERNAL_UNREVIEWED
    state: PluginState = PluginState.UNTRUSTED; trust: PluginTrust = PluginTrust.UNTRUSTED
    compatible: bool = True; enabled: bool = False; health: str = "not_checked"; reason: str = "External plugins default to untrusted and disabled."


@dataclass(frozen=True, slots=True)
class PluginVerification:
    plugin_id: str; valid: bool; compatible: bool; integrity: str; signature: str
    missing_dependencies: tuple[str, ...]; missing_credentials: tuple[str, ...]
    permission_risks: tuple[str, ...]; blocked_reasons: tuple[str, ...]; verification_id: str = field(default_factory=_id)


@dataclass(frozen=True, slots=True)
class PluginPolicy:
    enabled: bool = True; allow_external: bool = True; allow_local_development: bool = True
    allow_inprocess_external: bool = False; allow_subprocess: bool = False; allow_network: bool = False
    allow_filesystem_write: bool = False; allow_installation: bool = False; allow_updates: bool = False; allow_uninstall: bool = False
    require_integrity_check: bool = True; require_approval_for_enable: bool = True; require_approval_for_side_effects: bool = True
    max_registered: int = 64; max_enabled: int = 8; max_output_chars: int = 8000; execution_timeout_seconds: int = 30
    max_concurrent: int = 1; save_history: bool = True; max_history_items: int = 100; redact_sensitive_values: bool = True
