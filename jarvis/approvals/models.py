"""Explicit, scope-bound approval models."""
from dataclasses import dataclass,field
from datetime import UTC,datetime,timedelta
from enum import StrEnum
from jarvis.foundation_common import new_id,now,validate_items,validate_request_text,validate_text
from jarvis.execution.models import ExecutionPermission,ExecutionRisk
class ApprovalState(StrEnum): PENDING="pending"; APPROVED="approved"; DENIED="denied"; CANCELLED="cancelled"; EXPIRED="expired"; REVOKED="revoked"; BLOCKED="blocked"; UNAVAILABLE="unavailable"
class ApprovalDecisionType(StrEnum): APPROVE="approve"; DENY="deny"; CANCEL="cancel"; REVOKE="revoke"
@dataclass(frozen=True,slots=True)
class ApprovalPolicy:
 policy_id:str=field(default_factory=new_id); explicit_approval_required:bool=True; approval_ttl_seconds:int=900; allow_broad_approvals:bool=False; allow_secret_access_approvals:bool=False; allow_critical_action_approvals:bool=False; require_resource_scope:bool=True; require_permission_scope:bool=True; warnings:tuple[str,...]=()
@dataclass(slots=True)
class ApprovalRequest:
 request_summary:str; action_type:str; target_subsystem:str; risk_level:ExecutionRisk; required_permissions:tuple[ExecutionPermission,...]; affected_resources:tuple[str,...]; expected_side_effects:tuple[str,...]=(); blocked_actions:tuple[str,...]=(); requested_by:str="user"; expires_at:str=""; status:ApprovalState=ApprovalState.PENDING; approval_id:str=field(default_factory=new_id); created_at:str=field(default_factory=now); warnings:tuple[str,...]=(); used:bool=False
 def __post_init__(self):
  validate_request_text(self.request_summary); validate_items(self.required_permissions); validate_items(self.affected_resources)
  if not self.expires_at:self.expires_at=(datetime.now(UTC)+timedelta(minutes=15)).isoformat()
@dataclass(frozen=True,slots=True)
class ApprovalDecision:
 approval_id:str; decision:ApprovalDecisionType; decided_by:str="user"; reason:str=""; decision_id:str=field(default_factory=new_id); decided_at:str=field(default_factory=now); warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class ApprovalStatus:
 approval_id:str; status:ApprovalState; risk_level:ExecutionRisk; expired:bool; revocable:bool; usable_for_execution:bool; warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class ApprovalResult:
 request_id:str; status:ApprovalState; approval_request:ApprovalRequest|None=None; decision:ApprovalDecision|None=None; approval_status:ApprovalStatus|None=None; warnings:tuple[str,...]=(); error:str|None=None
