"""In-memory explicit approval registry; approval never executes actions."""
from datetime import UTC,datetime
from jarvis.foundation_common import contains_secret,new_id,safe_ref
from jarvis.execution.models import ExecutionPermission,ExecutionRisk
from .models import *
class ApprovalRegistry:
 def __init__(self,max_pending=50,max_history=100):self.policy=ApprovalPolicy();self.requests={};self.decisions=[];self.max_pending=max_pending;self.max_history=max_history
 def create(self,summary,action_type,permissions,resources,*,risk=ExecutionRisk.HIGH,target="execution"):
  blocked=risk is ExecutionRisk.CRITICAL or contains_secret(summary) or not permissions or not resources or any("*" in str(x) for x in resources)
  req=ApprovalRequest(summary,action_type,target,risk,tuple(permissions),tuple(safe_ref(x) for x in resources),status=ApprovalState.BLOCKED if blocked else ApprovalState.PENDING,warnings=("Critical, secret, broad, or unscoped approvals are blocked.",) if blocked else ())
  self.requests[req.approval_id]=req;return req
 def get(self,i):return self.requests.get(i)
 def _expired(self,r):return datetime.fromisoformat(r.expires_at)<=datetime.now(UTC)
 def status(self,i):
  r=self.get(i)
  if not r:return None
  if r.status in {ApprovalState.PENDING,ApprovalState.APPROVED} and self._expired(r):r.status=ApprovalState.EXPIRED
  return ApprovalStatus(i,r.status,r.risk_level,r.status is ApprovalState.EXPIRED,r.status is ApprovalState.APPROVED and not r.used,r.status is ApprovalState.APPROVED and not r.used and not self._expired(r))
 def decide(self,i,decision:ApprovalDecisionType):
  r=self.get(i)
  if not r:return ApprovalResult(new_id(),ApprovalState.UNAVAILABLE,error="approval_not_found")
  self.status(i)
  allowed={ApprovalDecisionType.APPROVE:{ApprovalState.PENDING},ApprovalDecisionType.DENY:{ApprovalState.PENDING},ApprovalDecisionType.CANCEL:{ApprovalState.PENDING},ApprovalDecisionType.REVOKE:{ApprovalState.APPROVED}}
  if r.status not in allowed[decision]:return ApprovalResult(new_id(),r.status,r,approval_status=self.status(i),error="invalid_approval_transition")
  r.status={ApprovalDecisionType.APPROVE:ApprovalState.APPROVED,ApprovalDecisionType.DENY:ApprovalState.DENIED,ApprovalDecisionType.CANCEL:ApprovalState.CANCELLED,ApprovalDecisionType.REVOKE:ApprovalState.REVOKED}[decision]
  d=ApprovalDecision(i,decision);self.decisions=(self.decisions+[d])[-self.max_history:];return ApprovalResult(new_id(),r.status,r,d,self.status(i))
 def validate(self,i,action,permissions,resources,*,consume=False):
  r=self.get(i);s=self.status(i) if r else None
  match=bool(r and s and s.usable_for_execution and r.action_type==action and set(r.required_permissions)==set(permissions) and set(r.affected_resources)=={safe_ref(x) for x in resources})
  if match and consume:r.used=True
  return match
 def pending(self):return tuple(x for x in self.requests.values() if self.status(x.approval_id).status is ApprovalState.PENDING)[:self.max_pending]
 def recent(self):return tuple(list(self.requests.values())[-self.max_history:])
 def expire(self):
  for r in self.requests.values():self.status(r.approval_id)
  return sum(r.status is ApprovalState.EXPIRED for r in self.requests.values())
