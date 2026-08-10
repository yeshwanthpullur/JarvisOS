import unittest
from datetime import UTC, datetime, timedelta
from jarvis.approvals import ApprovalDecisionType, ApprovalRegistry, ApprovalState
from jarvis.execution import ExecutionPolicyEngine
from jarvis.execution.broker import ExecutionBroker, ToolExecutionRequest
from jarvis.execution.models import ExecutionMode, ExecutionPermission, ExecutionRisk

class Phase4CoreTests(unittest.TestCase):
 def setUp(self): self.policy=ExecutionPolicyEngine(); self.approvals=ApprovalRegistry(); self.broker=ExecutionBroker(self.policy,self.approvals)
 def test_policy_defaults_and_readiness(self):
  self.assertEqual(self.policy.policy.default_mode,ExecutionMode.PLAN_ONLY);self.assertTrue(self.policy.policy.local_first);self.assertTrue(self.policy.policy.secrets_blocked);self.assertEqual(len(self.policy.readiness()),13)
 def test_critical_action_blocked(self): self.assertEqual(self.policy.plan("delete all files").status,ExecutionMode.BLOCKED)
 def test_file_write_requires_approval(self): self.assertEqual(self.policy.plan("write a file").status,ExecutionMode.APPROVAL_REQUIRED)
 def test_permissions_denied_and_secrets_blocked(self):
  rules={r.name:r for r in self.policy.permissions()};self.assertFalse(rules[ExecutionPermission.WRITE_FILES].granted_by_default);self.assertTrue(rules[ExecutionPermission.SECRETS_ACCESS].blocked_by_default)
 def test_explicit_approval_lifecycle(self):
  req=self.approvals.create("create notes", "file_write",(ExecutionPermission.WRITE_FILES,),("notes.txt",));self.assertEqual(req.status,ApprovalState.PENDING)
  self.assertFalse(self.approvals.validate(req.approval_id,"file_write",(ExecutionPermission.WRITE_FILES,),("notes.txt",)))
  self.approvals.decide(req.approval_id,ApprovalDecisionType.APPROVE);self.assertTrue(self.approvals.validate(req.approval_id,"file_write",(ExecutionPermission.WRITE_FILES,),("notes.txt",)))
  self.approvals.decide(req.approval_id,ApprovalDecisionType.REVOKE);self.assertFalse(self.approvals.validate(req.approval_id,"file_write",(ExecutionPermission.WRITE_FILES,),("notes.txt",)))
 def test_denied_cancelled_and_expired_unusable(self):
  for decision in (ApprovalDecisionType.DENY,ApprovalDecisionType.CANCEL):
   r=self.approvals.create("create notes","file_write",(ExecutionPermission.WRITE_FILES,),("notes.txt",));self.approvals.decide(r.approval_id,decision);self.assertFalse(self.approvals.status(r.approval_id).usable_for_execution)
  r=self.approvals.create("create notes","file_write",(ExecutionPermission.WRITE_FILES,),("notes.txt",));r.expires_at=(datetime.now(UTC)-timedelta(seconds=1)).isoformat();self.assertEqual(self.approvals.status(r.approval_id).status,ApprovalState.EXPIRED)
 def test_scope_mismatch_and_broad_approval_blocked(self):
  r=self.approvals.create("create notes","file_write",(ExecutionPermission.WRITE_FILES,),("*.txt",));self.assertEqual(r.status,ApprovalState.BLOCKED)
  r=self.approvals.create("create notes","file_write",(ExecutionPermission.WRITE_FILES,),("notes.txt",));self.approvals.decide(r.approval_id,ApprovalDecisionType.APPROVE);self.assertFalse(self.approvals.validate(r.approval_id,"file_write",(ExecutionPermission.WRITE_FILES,),("other.txt",)))
 def test_broker_dry_run_no_approval(self):
  r=ToolExecutionRequest("file_write","file_executor","files","write notes",ExecutionMode.DRY_RUN,ExecutionRisk.HIGH,(ExecutionPermission.WRITE_FILES,),("notes.txt",),dry_run=True);self.assertEqual(self.broker.route(r).status,"dry_run_completed")
 def test_broker_requires_exact_approval(self):
  r=ToolExecutionRequest("file_write","file_executor","files","write notes",ExecutionMode.APPROVED_EXECUTION,ExecutionRisk.HIGH,(ExecutionPermission.WRITE_FILES,),("notes.txt",),dry_run=False);self.assertEqual(self.broker.route(r).status,"approval_required")
  a=self.approvals.create("write notes","file_write",r.required_permissions,r.affected_resources);self.approvals.decide(a.approval_id,ApprovalDecisionType.APPROVE)
  r=ToolExecutionRequest(r.action_type,r.target_tool,r.target_subsystem,r.request_summary,r.execution_mode,r.risk_level,r.required_permissions,r.affected_resources,a.approval_id,False);self.assertEqual(self.broker.route(r).status,"approved_for_executor")
 def test_broker_blocks_critical_and_unavailable(self):
  r=ToolExecutionRequest("file_write","file_executor","files","delete all",ExecutionMode.DRY_RUN,ExecutionRisk.CRITICAL,(ExecutionPermission.WRITE_FILES,),("workspace",));self.assertEqual(self.broker.route(r).status,"blocked")
  r=ToolExecutionRequest("unknown","missing","none","safe unknown",ExecutionMode.DRY_RUN,ExecutionRisk.LOW,(),(),dry_run=True);self.assertEqual(self.broker.route(r).status,"unavailable")

if __name__=="__main__":unittest.main()
