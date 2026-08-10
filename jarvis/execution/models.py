"""Bounded shared models for controlled local execution."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from jarvis.foundation_common import new_id, now, validate_items, validate_request_text, validate_text

class ExecutionMode(StrEnum):
    PLAN_ONLY="plan_only"; DRY_RUN="dry_run"; APPROVAL_REQUIRED="approval_required"; APPROVED_EXECUTION="approved_execution"; BLOCKED="blocked"; UNAVAILABLE="unavailable"; COMPLETED="completed"; FAILED="failed"
class ExecutionRisk(StrEnum): LOW="low"; MEDIUM="medium"; HIGH="high"; CRITICAL="critical"
class ExecutionPermission(StrEnum):
    READ_CONTEXT="read_context"; READ_MEMORY_REFS="read_memory_refs"; WRITE_MEMORY="write_memory"; READ_FILES="read_files"; WRITE_FILES="write_files"; EXECUTE_COMMANDS="execute_commands"; GIT_READ="git_read"; GIT_WRITE="git_write"; BROWSER_READ="browser_read"; BROWSER_WRITE="browser_write"; NETWORK_ACCESS="network_access"; SEND_NOTIFICATION="send_notification"; SEND_MESSAGE="send_message"; SEND_EMAIL="send_email"; SCHEDULER_CREATE="scheduler_create"; SCHEDULER_RUN="scheduler_run"; MCP_EXECUTE="mcp_execute"; PLUGIN_EXECUTE="plugin_execute"; MODEL_RUNTIME_START="model_runtime_start"; MODEL_DOWNLOAD="model_download"; SECRETS_ACCESS="secrets_access"; CREDENTIALS_ACCESS="credentials_access"; SYSTEM_STATUS="system_status"; SYSTEM_MODIFY="system_modify"; DEPLOY="deploy"

@dataclass(frozen=True, slots=True)
class ExecutionPolicy:
    policy_id:str=field(default_factory=new_id); default_mode:ExecutionMode=ExecutionMode.PLAN_ONLY; local_first:bool=True; approval_required_for_side_effects:bool=True; secrets_blocked:bool=True; credentials_blocked:bool=True; external_network_disabled:bool=True; background_execution_disabled:bool=True; warnings:tuple[str,...]=()
@dataclass(frozen=True, slots=True)
class PermissionRule:
    name:ExecutionPermission; category:str; risk_level:ExecutionRisk; granted_by_default:bool=False; requires_approval:bool=True; blocked_by_default:bool=False; reason:str="Denied unless an action-specific policy grants it."; permission_id:str=field(default_factory=new_id)
@dataclass(frozen=True, slots=True)
class ExecutionCapability:
    name:str; status:str; execution_available:bool; dry_run_available:bool=True; approval_required:bool=True; permissions_required:tuple[ExecutionPermission,...]=(); warnings:tuple[str,...]=(); capability_id:str=field(default_factory=new_id)
    def __post_init__(self): validate_text(self.name); validate_items(self.permissions_required); validate_items(self.warnings)
@dataclass(frozen=True, slots=True)
class ExecutionReadiness:
    subsystem:str; plan_available:bool=True; dry_run_available:bool=True; execution_available:bool=False; approval_system_available:bool=False; blocker:str="Dedicated executor is not enabled."; warnings:tuple[str,...]=()
@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    request_id:str; action_type:str; summary:str; steps:tuple[str,...]; risk_level:ExecutionRisk; required_permissions:tuple[ExecutionPermission,...]; mode:ExecutionMode; approval_required:bool; blocked_reason:str=""; warnings:tuple[str,...]=(); plan_id:str=field(default_factory=new_id)
    def __post_init__(self): validate_text(self.summary); validate_items(self.steps); validate_items(self.required_permissions)
@dataclass(frozen=True, slots=True)
class ExecutionPolicyResult:
    request_id:str; status:ExecutionMode; policy:ExecutionPolicy; permissions:tuple[PermissionRule,...]=(); capabilities:tuple[ExecutionCapability,...]=(); readiness:tuple[ExecutionReadiness,...]=(); plan:ExecutionPlan|None=None; warnings:tuple[str,...]=(); error:str|None=None

SIDE_EFFECTS={"file_write","file_modify","file_delete","command_execute","git_stage","git_commit","git_push","browser_read","notification_send","scheduler_create","scheduler_run","communication_send","mcp_execute","plugin_execute","model_runtime_start","deploy"}
CRITICAL_TERMS=("delete all","force push","read .env","show .env","credential","private key","disable security","bypass","surveillance","track a person")
