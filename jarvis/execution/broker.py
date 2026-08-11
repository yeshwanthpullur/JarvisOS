"""Central policy/approval/capability gate for action-specific executors."""
from dataclasses import dataclass,field
from jarvis.foundation_common import new_id,validate_items,validate_request_text,validate_text
from jarvis.approvals import ApprovalRegistry
from .models import *
from .policy import ExecutionPolicyEngine
@dataclass(frozen=True,slots=True)
class ToolCapability:
 tool_id:str; action_types:tuple[str,...]; execution_available:bool; dry_run_available:bool; approval_required:bool; permissions_required:tuple[ExecutionPermission,...]; risk_level:ExecutionRisk; warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class ToolExecutionRequest:
 action_type:str; target_tool:str; target_subsystem:str; request_summary:str; execution_mode:ExecutionMode; risk_level:ExecutionRisk; required_permissions:tuple[ExecutionPermission,...]; affected_resources:tuple[str,...]; approval_id:str=""; dry_run:bool=True; request_id:str=field(default_factory=new_id)
 def __post_init__(self):validate_request_text(self.request_summary);validate_items(self.affected_resources)
@dataclass(frozen=True,slots=True)
class ToolExecutionValidation:
 request_id:str; policy_allowed:bool; approval_valid:bool; permissions_valid:bool; tool_available:bool; risk_allowed:bool; dry_run_only:bool; blocked_reason:str=""; validation_id:str=field(default_factory=new_id)
@dataclass(frozen=True,slots=True)
class ToolExecutionResult:
 request_id:str; status:str; validation:ToolExecutionValidation; dry_run_output:str=""; execution_output:str=""; warnings:tuple[str,...]=(); error:str|None=None
def build_default_tool_registry():
 def c(i,a,p,r=ExecutionRisk.HIGH,run=False):return ToolCapability(i,(a,),run,True,bool(p),tuple(p),r)
 return {x.tool_id:x for x in (
  c("file_executor","file_write",(ExecutionPermission.WRITE_FILES,),run=True),c("command_executor","command_execute",(ExecutionPermission.EXECUTE_COMMANDS,),run=True),c("git_executor","git_write",(ExecutionPermission.GIT_WRITE,),run=True),c("browser_reader","browser_read",(ExecutionPermission.BROWSER_READ,ExecutionPermission.NETWORK_ACCESS),ExecutionRisk.MEDIUM,True),c("notification_executor","notification_send",(ExecutionPermission.SEND_NOTIFICATION,),ExecutionRisk.MEDIUM,True),c("scheduler_runner","scheduler_run",(ExecutionPermission.SCHEDULER_RUN,),ExecutionRisk.HIGH,True),c("telegram_send_tool","telegram_send",(ExecutionPermission.SEND_MESSAGE,ExecutionPermission.NETWORK_ACCESS),ExecutionRisk.HIGH,True),c("mcp_executor","mcp_execute",(ExecutionPermission.MCP_EXECUTE,)),c("model_runtime","model_runtime_start",(ExecutionPermission.MODEL_RUNTIME_START,)))}
class ExecutionBroker:
 def __init__(self,policy=None,approvals=None):self.policy=policy or ExecutionPolicyEngine();self.approvals=approvals or ApprovalRegistry();self.tools=build_default_tool_registry();self.history=[]
 def validate(self,r:ToolExecutionRequest):
  tool=self.tools.get(r.target_tool);critical=r.risk_level is ExecutionRisk.CRITICAL
  perms=bool(tool and set(tool.permissions_required)==set(r.required_permissions));approval=not bool(tool and tool.approval_required) or self.approvals.validate(r.approval_id,r.action_type,r.required_permissions,r.affected_resources)
  reason="critical_action_blocked" if critical else "tool_unavailable" if not tool else "permission_scope_mismatch" if not perms else "approval_required_or_invalid" if not approval and not r.dry_run else ""
  return ToolExecutionValidation(r.request_id,not critical,approval,perms,bool(tool and tool.execution_available),not critical,r.dry_run,reason)
 def route(self,r:ToolExecutionRequest):
  v=self.validate(r)
  status="blocked" if not v.risk_allowed else "unavailable" if not self.tools.get(r.target_tool) else "dry_run_completed" if r.dry_run else "approval_required" if not v.approval_valid else "approved_for_executor"
  out=ToolExecutionResult(r.request_id,status,v,"Validated only; no side effect occurred." if r.dry_run else "",error=v.blocked_reason or None);self.history=(self.history+[out])[-50:];return out
