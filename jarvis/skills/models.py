"""Declarative skill manifests and permission metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Any


class SkillStatus(str, Enum):
    READY = "ready"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"
    ERROR = "error"
    FUTURE = "future"


class SkillRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SkillExecutionMode(str, Enum):
    DISABLED = "disabled"
    PLAN_ONLY = "plan_only"
    DRY_RUN = "dry_run"
    APPROVED_EXECUTION = "approved_execution"


class SkillPermission(str, Enum):
    READ_CONTEXT = "read_context"
    READ_MEMORY_REFS = "read_memory_refs"
    WRITE_MEMORY = "write_memory"
    READ_FILES = "read_files"
    WRITE_FILES = "write_files"
    EXECUTE_COMMANDS = "execute_commands"
    NETWORK_ACCESS = "network_access"
    BROWSER_READ = "browser_read"
    BROWSER_WRITE = "browser_write"
    SEND_MESSAGE = "send_message"
    SEND_EMAIL = "send_email"
    CALENDAR_READ = "calendar_read"
    CALENDAR_WRITE = "calendar_write"
    SOCIAL_POST = "social_post"
    HARDWARE_READ = "hardware_read"
    HARDWARE_WRITE = "hardware_write"
    CAMERA_ACCESS = "camera_access"
    MICROPHONE_ACCESS = "microphone_access"
    LOCATION_ACCESS = "location_access"
    SYSTEM_STATUS = "system_status"
    SYSTEM_MODIFY = "system_modify"
    DEPLOY = "deploy"
    GIT_READ = "git_read"
    GIT_WRITE = "git_write"
    GITHUB_READ = "github_read"
    GITHUB_ISSUE_WRITE = "github_issue_write"
    GITHUB_PR_WRITE = "github_pr_write"
    GITHUB_RELEASE_WRITE = "github_release_write"
    GITHUB_MERGE = "github_merge"
    GITHUB_ADMIN = "github_admin"
    SECRETS_ACCESS = "secrets_access"


APPROVAL_PERMISSIONS = {
    SkillPermission.WRITE_MEMORY, SkillPermission.WRITE_FILES, SkillPermission.EXECUTE_COMMANDS,
    SkillPermission.NETWORK_ACCESS, SkillPermission.BROWSER_WRITE, SkillPermission.SEND_MESSAGE,
    SkillPermission.SEND_EMAIL, SkillPermission.CALENDAR_WRITE, SkillPermission.SOCIAL_POST,
    SkillPermission.HARDWARE_WRITE, SkillPermission.CAMERA_ACCESS, SkillPermission.MICROPHONE_ACCESS,
    SkillPermission.LOCATION_ACCESS, SkillPermission.SYSTEM_MODIFY, SkillPermission.DEPLOY,
    SkillPermission.GIT_WRITE, SkillPermission.GITHUB_ISSUE_WRITE, SkillPermission.GITHUB_PR_WRITE,
    SkillPermission.GITHUB_RELEASE_WRITE, SkillPermission.GITHUB_MERGE, SkillPermission.GITHUB_ADMIN,
}


@dataclass(frozen=True, slots=True)
class SkillCapability:
    name: str
    description: str
    capability_type: str
    input_types: tuple[str, ...] = ()
    output_types: tuple[str, ...] = ()
    side_effects: tuple[str, ...] = ()
    risk_level: SkillRiskLevel = SkillRiskLevel.LOW
    requires_approval: bool = False

    def __post_init__(self) -> None:
        if not self.name or len(self.name) > 80 or len(self.description) > 600:
            raise ValueError("invalid_skill_capability")
        if self.side_effects and not self.requires_approval:
            raise ValueError("skill_side_effects_require_approval")


@dataclass(frozen=True, slots=True)
class SkillManifest:
    skill_id: str
    name: str
    description: str
    version: str
    owner: str
    category: str
    status: SkillStatus
    capabilities: tuple[SkillCapability, ...]
    input_schema: Mapping[str, Any] = field(default_factory=dict)
    output_schema: Mapping[str, Any] = field(default_factory=dict)
    side_effects: tuple[str, ...] = ()
    required_permissions: tuple[SkillPermission, ...] = ()
    required_providers: tuple[str, ...] = ()
    network_required: bool = False
    local_only: bool = True
    requires_approval: bool = False
    risk_level: SkillRiskLevel = SkillRiskLevel.LOW
    enabled: bool = False
    execution_mode: SkillExecutionMode = SkillExecutionMode.DISABLED
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.skill_id or len(self.skill_id) > 80 or len(self.name) > 80 or len(self.description) > 600:
            raise ValueError("invalid_skill_manifest")
        names = [item.name for item in self.capabilities]
        if len(names) != len(set(names)):
            raise ValueError("duplicate_skill_capability")
        approval_needed = bool(self.side_effects or set(self.required_permissions).intersection(APPROVAL_PERMISSIONS) or self.risk_level in {SkillRiskLevel.HIGH, SkillRiskLevel.CRITICAL})
        if approval_needed and not self.requires_approval:
            raise ValueError("skill_approval_required")
        if self.status in {SkillStatus.FUTURE, SkillStatus.UNAVAILABLE, SkillStatus.DISABLED, SkillStatus.NOT_CONFIGURED} and self.enabled:
            raise ValueError("unavailable_skill_cannot_be_enabled")
