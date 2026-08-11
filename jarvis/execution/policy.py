"""Deterministic, deny-by-default controlled execution policy."""
from __future__ import annotations
from jarvis.foundation_common import new_id, validate_request_text
from .models import *

ACTION_MAP=(
    (("force push","delete all","read .env","secret","credential","disable security","bypass"),"blocked"),
    (("commit","git push","stage "),"git_write"), (("run ","command","test suite","pytest"),"command_execute"),
    (("write ","create file","append","rename file","move file"),"file_write"),
    (("http://","https://","read webpage","read this public"),"browser_read"),
    (("notification","notify me","show me a local"),"notification_send"),
    (("telegram send","send this to telegram","message me on telegram"),"telegram_send"),
    (("discord send","send this to discord"),"discord_send"),(("email send","email this","send email"),"email_send"),(("slack send","send this to slack"),"slack_send"),
    (("remind","run due","schedule"),"scheduler_run"),
)
PERMISSIONS={
 "file_write":(ExecutionPermission.WRITE_FILES,), "command_execute":(ExecutionPermission.EXECUTE_COMMANDS,),
 "git_write":(ExecutionPermission.GIT_WRITE,), "browser_read":(ExecutionPermission.BROWSER_READ,ExecutionPermission.NETWORK_ACCESS),
 "notification_send":(ExecutionPermission.SEND_NOTIFICATION,), "scheduler_run":(ExecutionPermission.SCHEDULER_RUN,), "telegram_send":(ExecutionPermission.SEND_MESSAGE,ExecutionPermission.NETWORK_ACCESS), "discord_send":(ExecutionPermission.SEND_MESSAGE,ExecutionPermission.NETWORK_ACCESS), "email_send":(ExecutionPermission.SEND_EMAIL,ExecutionPermission.NETWORK_ACCESS), "slack_send":(ExecutionPermission.SEND_MESSAGE,ExecutionPermission.NETWORK_ACCESS),
}

class ExecutionPolicyEngine:
    def __init__(self): self.policy=ExecutionPolicy(); self.history:list[ExecutionPolicyResult]=[]
    def classify(self,text:str)->tuple[str,ExecutionRisk]:
        validate_request_text(text); v=text.lower()
        if any(x in v for x in CRITICAL_TERMS): return "blocked",ExecutionRisk.CRITICAL
        for terms,action in ACTION_MAP:
            if any(x in v for x in terms): return action, ExecutionRisk.HIGH if action in {"file_write","command_execute","git_write","scheduler_run"} else ExecutionRisk.MEDIUM
        return "status",ExecutionRisk.LOW
    def permissions(self)->tuple[PermissionRule,...]:
        blocked={ExecutionPermission.SECRETS_ACCESS,ExecutionPermission.CREDENTIALS_ACCESS}
        return tuple(PermissionRule(p,"execution",ExecutionRisk.CRITICAL if p in blocked else ExecutionRisk.HIGH if p not in {ExecutionPermission.READ_CONTEXT,ExecutionPermission.SYSTEM_STATUS} else ExecutionRisk.LOW,requires_approval=p not in {ExecutionPermission.READ_CONTEXT,ExecutionPermission.SYSTEM_STATUS},blocked_by_default=p in blocked) for p in ExecutionPermission)
    def readiness(self)->tuple[ExecutionReadiness,...]:
        active={"file_operations","command_execution","git_operations","browser_read","notifications","scheduler_runner"}
        names=("file_operations","command_execution","git_operations","browser_read","browser_interactive","notifications","scheduler_runner","communication_sending","mcp_plugin_execution","model_runtime_start","document_parsing","research_retrieval","coding_edits")
        return tuple(ExecutionReadiness(n,execution_available=n in active,approval_system_available=True,blocker="" if n in active else "Intentionally disabled or unavailable.") for n in names)
    def plan(self,text:str)->ExecutionPolicyResult:
        action,risk=self.classify(text); blocked=risk is ExecutionRisk.CRITICAL; perms=PERMISSIONS.get(action,())
        plan=ExecutionPlan(new_id(),action,"Bounded controlled-execution plan.",("Validate action-specific policy.","Require exact explicit approval for side effects.","Route through broker to a dedicated executor."),risk,perms,ExecutionMode.BLOCKED if blocked else ExecutionMode.APPROVAL_REQUIRED if action in SIDE_EFFECTS or action in PERMISSIONS else ExecutionMode.PLAN_ONLY,not blocked and bool(perms),"Critical action is not approvable." if blocked else "")
        result=ExecutionPolicyResult(plan.request_id,plan.mode,self.policy,self.permissions(),readiness=self.readiness(),plan=plan,error="critical_action_blocked" if blocked else None)
        self.history=(self.history+[result])[-25:]; return result
