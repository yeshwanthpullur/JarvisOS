import re,tempfile,unittest
from pathlib import Path
from commands import CommandManager
from jarvis.approvals import ApprovalDecisionType,ApprovalRegistry
from jarvis.execution.broker import ExecutionBroker
from jarvis.execution.files import FileExecutor
from jarvis.execution.models import ExecutionPermission

class Phase4IntegrationTests(unittest.TestCase):
 def setUp(self):self.m=CommandManager();self.m.initialize()
 def cmd(self,text):
  r=self.m.execute(text);self.assertNotIn("Unknown command",r.response,text);self.assertLess(len(r.response),10000);self.assertIsNone(re.search(r"[A-Za-z]:\\Users\\",r.response));return r.response
 def test_all_cli_namespaces(self):
  commands=("execution status","execution policy","execution permissions","execution readiness","execution risk write a file","execution plan run this command","execution capabilities","approval status","approval help","approval pending","approval list","approval expire","broker status","broker help","broker capabilities","broker plan write a file","broker validate write a file","broker dry-run write a file","file-exec status","file-exec help","file-exec policy","file-exec validate .env","file-exec dry-run create file","command status","command help","command policy","command allowlist","command validate python --version","command dry-run python --version","git-exec status","git-exec help","git-exec policy","git-exec inspect","git-exec files","git-exec dry-run commit","browser policy","browser validate https://example.com","browser dry-run https://example.com","notification status","notification help","notification providers","notification policy","notification dry-run safe test","scheduler runtime-status","scheduler jobs","scheduler due","scheduler runtime-policy","project status")
  for c in commands:self.cmd(c)
  self.assertIn("approved public HTTP(S) GET only",self.cmd("browser policy"))
 def test_cli_security_boundaries(self):
  self.assertIn("blocked",self.cmd("execution risk delete all files"));self.assertIn("allowed=false",self.cmd("file-exec validate .env"));self.assertIn("blocked",self.cmd('command validate "python --version | more"'));self.assertIn("force=no",self.cmd("git-exec status"));self.assertIn("background=no",self.cmd("scheduler runtime-status"));self.assertIn("external=no",self.cmd("notification status"))
 def test_prime_routes_and_blocks(self):
  self.assertIn("execution_agent",self.cmd('prime route "write this file"'));self.assertIn("execution_agent",self.cmd('prime route "run this command"'));self.assertIn("notification_agent",self.cmd('prime route "show me a local notification"'));self.assertIn("blocked",self.cmd('prime route "force push main"'));self.assertIn("blocked",self.cmd('prime route "delete all files"'));self.assertIn("blocked",self.cmd('prime route "read my .env secret"'))
 def test_end_to_end_approval_broker_file_chain(self):
  with tempfile.TemporaryDirectory() as td:
   reg=ApprovalRegistry();broker=ExecutionBroker(approvals=reg);executor=FileExecutor(Path(td),broker);req=reg.create("create result","file_write",(ExecutionPermission.WRITE_FILES,),("result.txt",));self.assertEqual(executor.execute("create_text_file","result.txt","ok",approval_id=req.approval_id).status,"approval_required");reg.decide(req.approval_id,ApprovalDecisionType.APPROVE);result=executor.execute("create_text_file","result.txt","ok",approval_id=req.approval_id);self.assertEqual(result.status,"completed");self.assertEqual((Path(td)/"result.txt").read_text(),"ok");self.assertTrue(executor.rollback(result.rollback_id))
 def test_no_public_execution_api(self):
  api=(Path(__file__).parents[1]/"api"/"index.py").read_text(encoding="utf-8");
  for term in ("FileExecutor","CommandSandbox","GitExecutor","BrowserReader","NotificationExecutor","SchedulerRuntime","ApprovalRegistry","ExecutionBroker"):self.assertNotIn(term,api)

if __name__=="__main__":unittest.main()
