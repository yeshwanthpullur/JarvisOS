import io,os,subprocess,tempfile,unittest
from datetime import UTC,datetime,timedelta
from pathlib import Path
from unittest.mock import patch
from jarvis.approvals import ApprovalDecisionType,ApprovalRegistry
from jarvis.execution.broker import ExecutionBroker
from jarvis.execution.models import ExecutionPermission
from jarvis.execution.files import FileExecutor
from jarvis.execution.commands import CommandSandbox
from jarvis.execution.git import GitExecutor
from jarvis.browser.execution import BrowserReader
from jarvis.notifications import NotificationExecutor,NotificationProvider
from jarvis.scheduler.runtime import SchedulerRuntime,JobStatus

def approve(reg,summary,action,perms,resources):
 r=reg.create(summary,action,perms,resources);reg.decide(r.approval_id,ApprovalDecisionType.APPROVE);return r.approval_id
class FakeProvider:
 provider=NotificationProvider("fake","Fake local","test","ready",True);calls=[]
 def display(self,t,b):self.calls.append((t,b));return True
class FakeResponse:
 headers=None
 def __init__(self,body=b"<html><title>Safe</title><script>bad()</script><p>Hello world</p></html>"):
  from email.message import Message
  self.body=body;self.headers=Message();self.headers["Content-Type"]="text/html; charset=utf-8"
 def geturl(self):return "https://example.com/docs"
 def read(self,n):return self.body[:n]
class FakeOpener:
 def open(self,*a,**k):return FakeResponse()
def public_resolver(*a,**k):return [(None,None,None,None,("93.184.216.34",443))]

class FileExecutionTests(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);self.reg=ApprovalRegistry();self.broker=ExecutionBroker(approvals=self.reg);self.ex=FileExecutor(self.root,self.broker)
 def tearDown(self):self.t.cleanup()
 def approval(self,op,path,dest=""):return approve(self.reg,op,"file_write",(ExecutionPermission.WRITE_FILES,),(Path(path).name,)+( (Path(dest).name,) if dest else ()))
 def test_path_safety(self):
  self.assertTrue(self.ex.validate_path("safe.txt").target_allowed);self.assertFalse(self.ex.validate_path("../escape.txt").target_allowed);self.assertFalse(self.ex.validate_path(".env").target_allowed);self.assertFalse(self.ex.validate_path(".git/config").target_allowed);self.assertFalse(self.ex.validate_path("models/x.gguf").target_allowed)
 def test_dry_run_no_mutation(self):self.assertEqual(self.ex.dry_run("create_text_file","a.txt","x").status,"dry_run_completed");self.assertFalse((self.root/"a.txt").exists())
 def test_create_append_mkdir_rename_and_rollback(self):
  r=self.ex.execute("create_text_file","a.txt","hello",approval_id=self.approval("create","a.txt"));self.assertEqual(r.status,"completed");self.assertTrue(self.ex.rollback(r.rollback_id));self.assertFalse((self.root/"a.txt").exists())
  (self.root/"a.txt").write_text("a");r=self.ex.execute("append_text","a.txt","b",approval_id=self.approval("append","a.txt"));self.assertEqual((self.root/"a.txt").read_text(),"ab");self.assertTrue(self.ex.rollback(r.rollback_id));self.assertEqual((self.root/"a.txt").read_text(),"a")
  r=self.ex.execute("create_directory","d",approval_id=self.approval("mkdir","d"));self.assertTrue((self.root/"d").is_dir());self.assertTrue(self.ex.rollback(r.rollback_id))
  (self.root/"a.txt").write_text("a");r=self.ex.execute("rename_file","a.txt",destination="b.txt",approval_id=self.approval("rename","a.txt","b.txt"));self.assertTrue((self.root/"b.txt").exists());self.assertTrue(self.ex.rollback(r.rollback_id))
 def test_missing_approval_overwrite_delete_and_size_blocked(self):
  self.assertEqual(self.ex.execute("create_text_file","a.txt","x").status,"approval_required");(self.root/"a.txt").write_text("x");self.assertEqual(self.ex.execute("write_text","a.txt","y",approval_id=self.approval("write","a.txt")).status,"blocked");self.assertEqual(self.ex.execute("delete_file","a.txt",approval_id=self.approval("delete","a.txt")).status,"unavailable");self.assertEqual(self.ex.dry_run("create_text_file","b.txt","x"*9000).status,"blocked")

class CommandTests(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);self.reg=ApprovalRegistry();self.broker=ExecutionBroker(approvals=self.reg);self.ex=CommandSandbox(self.root,self.broker)
 def tearDown(self):self.t.cleanup()
 def test_policy_blocks_shell_network_install_git_writes(self):
  for c in ("python --version | more","powershell Get-Date","pip install x","git commit -m x","git push","curl https://example.com"):
   self.assertFalse(self.ex.validate(c).executable_allowed,c)
  self.assertTrue(self.ex.validate("git status").executable_allowed)
 def test_outside_cwd_blocked(self):self.assertFalse(self.ex.validate("python --version",Path(self.t.name).parent).working_directory_allowed)
 def test_dry_run_and_approval(self):self.assertEqual(self.ex.dry_run("python --version").status,"dry_run_completed");self.assertEqual(self.ex.execute("python --version","missing").status,"approval_required")
 def test_execute_shell_false_bounded_environment_and_output(self):
  summary="python --version";resources=(self.root.name,summary);aid=approve(self.reg,summary,"command_execute",(ExecutionPermission.EXECUTE_COMMANDS,),resources)
  with patch("jarvis.execution.commands.subprocess.run") as run:
   run.return_value=subprocess.CompletedProcess([],0,"x"*5000,"");r=self.ex.execute(summary,aid);self.assertEqual(r.status,"completed");self.assertTrue(r.output_truncated);self.assertFalse(run.call_args.kwargs["shell"]);self.assertNotIn("SECRET_TOKEN",run.call_args.kwargs["env"])
 def test_timeout_safe(self):
  aid=approve(self.reg,"python --version","command_execute",(ExecutionPermission.EXECUTE_COMMANDS,),(self.root.name,"python --version"))
  with patch("jarvis.execution.commands.subprocess.run",side_effect=subprocess.TimeoutExpired("python",1)):self.assertTrue(self.ex.execute("python --version",aid).timed_out)

class GitTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);subprocess.run(["git","init","-b","main"],cwd=self.root,capture_output=True);subprocess.run(["git","config","user.email","test@example.com"],cwd=self.root);subprocess.run(["git","config","user.name","Test"],cwd=self.root);self.reg=ApprovalRegistry();self.broker=ExecutionBroker(approvals=self.reg);self.ex=GitExecutor(self.root,self.broker)
 def tearDown(self):self.t.cleanup()
 def aid(self,op,resources):return approve(self.reg,op,"git_write",(ExecutionPermission.GIT_WRITE,),resources)
 def test_protected_assessment(self):
  for x in (".env","secret.key","models/x.gguf","data/jobs.json","x.backup"):self.assertFalse(self.ex.assess(x).allowed_to_stage)
 def test_stage_commit_no_implicit_push(self):
  (self.root/"a.txt").write_text("safe");a=self.aid("stage",("a.txt",));self.assertEqual(self.ex.stage(("a.txt",),a).status,"completed")
  resources=("main","Safe commit","a.txt");c=self.aid("commit",resources);r=self.ex.commit("Safe commit",c);self.assertEqual(r.status,"completed");self.assertTrue(r.commit_ref);self.assertEqual(r.push_status,"")
 def test_secret_commit_blocked(self):
  (self.root/"a.txt").write_text("api_key=abc123");subprocess.run(["git","add","a.txt"],cwd=self.root);self.assertEqual(self.ex.commit("safe",self.aid("commit",("main","safe","a.txt"))).status,"blocked")
 def test_push_policy(self):self.assertEqual(self.ex.push("x",remote="evil",branch="main").status,"blocked")

class BrowserTests(unittest.TestCase):
 def setUp(self):self.reg=ApprovalRegistry();self.broker=ExecutionBroker(approvals=self.reg);self.reader=BrowserReader(self.broker,public_resolver,FakeOpener())
 def test_url_policy(self):
  self.assertTrue(self.reader.validate_url("https://example.com").public_target)
  for u in ("file:///x","javascript:alert(1)","https://example.com:444/x"):self.assertFalse(self.reader.validate_url(u).public_target)
  for ip in ("127.0.0.1","10.0.0.1","169.254.169.254"):
   r=BrowserReader(self.broker,lambda *a,ip=ip,**k:[(None,None,None,None,(ip,443))]);self.assertFalse(r.validate_url(f"https://{ip}").public_target)
 def test_dry_run_and_read(self):
  self.assertEqual(self.reader.dry_run("https://example.com").status,"dry_run_completed");aid=approve(self.reg,"read","browser_read",(ExecutionPermission.BROWSER_READ,ExecutionPermission.NETWORK_ACCESS),("example.com",));r=self.reader.read("https://example.com/docs",aid);self.assertEqual(r.status,"completed");self.assertIn("Hello world",r.text_preview);self.assertNotIn("bad()",r.text_preview)

class NotificationSchedulerTests(unittest.TestCase):
 def setUp(self):FakeProvider.calls=[];self.reg=ApprovalRegistry();self.broker=ExecutionBroker(approvals=self.reg);self.note=NotificationExecutor(self.broker,FakeProvider())
 def test_notification_approval_secret_rate(self):
  fp="Test:5";aid=approve(self.reg,"note","notification_send",(ExecutionPermission.SEND_NOTIFICATION,),("local_device",fp));self.assertEqual(self.note.send("Test","hello",aid).status,"completed");self.assertEqual(self.note.send("API key","api_key=abc",aid).status,"blocked")
  self.note.policy=type(self.note.policy)(max_notifications_per_window=1);self.assertEqual(self.note.dry_run("Again","safe").status,"blocked")
 def test_scheduler_manual_only_and_notification(self):
  clock=lambda:datetime(2030,1,1,tzinfo=UTC);fp="Scheduled reminder:5";aid=approve(self.reg,"scheduled","notification_send",(ExecutionPermission.SEND_NOTIFICATION,),("local_device",fp));rt=SchedulerRuntime(self.broker,self.note,clock);j=rt.create("hello",aid,when=clock());self.assertFalse(rt.policy.allow_background_runner);run=rt.run(j.job_id);self.assertEqual(run.execution_status,"completed");self.assertEqual(j.status,JobStatus.COMPLETED);self.assertEqual(len(FakeProvider.calls),1)
 def test_scheduler_blocks_targets_cadence_and_controls(self):
  rt=SchedulerRuntime(self.broker,self.note,lambda:datetime.now(UTC));
  with self.assertRaises(ValueError):rt.create("unsafe","x",target="command_execute")
  with self.assertRaises(ValueError):rt.create("fast","x",cadence_minutes=1)
  j=rt.create("later","x",when=datetime.now(UTC)+timedelta(days=1));self.assertTrue(rt.pause(j.job_id));self.assertTrue(rt.resume(j.job_id));self.assertTrue(rt.cancel(j.job_id));self.assertFalse(rt.due())

if __name__=="__main__":unittest.main()
