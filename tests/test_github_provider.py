import hashlib,json,unittest
from commands import CommandManager
from config.schema import GitHubProviderConfig
from jarvis.approvals import ApprovalDecisionType
from jarvis.execution.broker import ExecutionBroker
from jarvis.execution.models import ExecutionPermission,ExecutionRisk
from jarvis.integrations.github import *

class FakeGitHub:
 def __init__(self,auth=True):self.auth=auth;self.calls=[]
 def available(self):return True
 def auth_status(self):return self.auth
 def read(self,repo,resource,identifier="",limit=20):self.calls.append(("read",repo,resource));return [{"number":i,"title":"item "+str(i),"body":"must not leak"} for i in range(30)] if resource!="repo" else {"full_name":repo,"default_branch":"main","private":False}
 def mutate(self,repo,action,payload):self.calls.append(("write",repo,action));return {"html_url":"https://github.com/example/1"}

class GitHubProviderTests(unittest.TestCase):
 def runtime(self,**changes):
  values=GitHubPolicy().__dict__ if hasattr(GitHubPolicy(),"__dict__") else {f.name:getattr(GitHubPolicy(),f.name) for f in __import__('dataclasses').fields(GitHubPolicy)};values.update(enabled=True,allow_issue_write=True,allow_pr_write=True,allow_release_write=True);values.update(changes);b=ExecutionBroker();return GitHubProvider(policy=GitHubPolicy(**values),transport=FakeGitHub(),broker=b),b
 def approval(self,r,b,action,repo,payload):
  serialized=json.dumps(payload,sort_keys=True);fp=hashlib.sha256(f"{repo}:{action}:{serialized}".encode()).hexdigest()[:20];permission=r.WRITE_PERMISSIONS[action];a=b.approvals.create("github",f"github_{action}",(permission,ExecutionPermission.NETWORK_ACCESS),(repo,fp),risk=ExecutionRisk.HIGH);b.approvals.decide(a.approval_id,ApprovalDecisionType.APPROVE);return a.approval_id
 def test_defaults_and_models(self):
  self.assertFalse(GitHubPolicy().enabled);self.assertEqual(GitHubPolicy().allowed_repositories,("yeshwanthpullur/JarvisOS",));self.assertFalse(GitHubProviderConfig().allow_merge)
  self.assertTrue(GitHubIssuePlan("r","t","b").approval_required);self.assertTrue(GitHubPullRequestPlan("r","main","x","t","b").approval_required);self.assertTrue(GitHubReleasePlan("r","v1","t","n").draft)
 def test_auth_states_and_health(self):
  self.assertEqual(GitHubProvider().status()["state"],"disabled");r,_=self.runtime();self.assertEqual(r.status()["state"],"auth_unverified");self.assertTrue(r.health().executed);self.assertEqual(r.status()["state"],"ready")
  r.transport.auth=False;self.assertEqual(r.health().error,"authentication_unverified")
 def test_repository_scope_and_no_enumeration(self):
  r,_=self.runtime();r.authenticated=True;self.assertEqual(r.read("repo","someone/private").error,"repository_not_allowed");self.assertEqual(r.policy.allowed_repositories,("yeshwanthpullur/JarvisOS",))
 def test_reads_bounded_and_sanitized(self):
  r,_=self.runtime(max_results=5);r.authenticated=True;result=r.read("issues");self.assertEqual(len(result.items),5);self.assertNotIn("body",str(result.items));self.assertLess(len(str(result.items)),3000)
 def test_writes_require_exact_approval(self):
  r,b=self.runtime();r.authenticated=True;payload={"title":"Safe issue","body":"bounded project note"};self.assertEqual(r.mutate("issue_create","yeshwanthpullur/JarvisOS",payload).error,"approval_required");aid=self.approval(r,b,"issue_create","yeshwanthpullur/JarvisOS",payload);self.assertTrue(r.mutate("issue_create","yeshwanthpullur/JarvisOS",payload,aid).executed)
 def test_repository_and_content_change_invalidate_approval(self):
  r,b=self.runtime();r.authenticated=True;p={"title":"Safe","body":"one"};aid=self.approval(r,b,"issue_create","yeshwanthpullur/JarvisOS",p);self.assertEqual(r.mutate("issue_create","other/repo",p,aid).error,"repository_not_allowed");self.assertEqual(r.mutate("issue_create","yeshwanthpullur/JarvisOS",{"title":"Safe","body":"two"},aid).error,"approval_required")
 def test_secret_and_private_path_blocked(self):
  r,_=self.runtime();r.authenticated=True
  for body in ("access token=secretvalue","see C:\\Users\\name\\private.txt","read .env"):
   self.assertEqual(r.mutate("issue_create","yeshwanthpullur/JarvisOS",{"title":"x","body":body}).status,"blocked")
 def test_admin_merge_workflow_and_force_push_absent(self):
  r,_=self.runtime();s=r.status();self.assertFalse(s["merge"]);self.assertFalse(s["workflow_execute"]);self.assertFalse(s["admin"]);self.assertNotIn("force",r.WRITE_TOOLS)
 def test_distinct_broker_tools(self):
  _,b=self.runtime()
  for tool in ("github_issue_create_tool","github_issue_comment_tool","github_pr_create_tool","github_pr_comment_tool","github_release_create_tool"):self.assertIn(tool,b.tools)
 def test_cli_and_local_git_separation(self):
  m=CommandManager();m.initialize()
  for command in ("github status","github help","github auth-status","github health","github repo","github capabilities","github rate-status","github issues","github issue-show 1","github issue-plan test","github issue-create test","github prs","github pr-show 1","github pr-plan test","github pr-create test","github releases","github release-show v1","github release-plan test","github release-create test","github workflows","github checks","github history"):
   out=m.execute(command).response;self.assertNotIn("unknown command",out.lower());self.assertLess(len(out),3000);self.assertNotIn("C:\\Users",out)
  self.assertNotIn("git push",m.execute("github help").response.lower())
 def test_prime_agents_and_skills(self):
  from jarvis.agents import AgentRegistry,PrimeAgent,PrimeRequest,register_specialist_agents
  from jarvis.skills import build_default_skill_registry
  p=PrimeAgent(register_specialist_agents(AgentRegistry()));self.assertEqual(p.route(PrimeRequest("check GitHub issues")).selected_agent,"coding_agent");self.assertEqual(p.route(PrimeRequest("create GitHub issue")).risk_level.value,"high")
  skills=build_default_skill_registry();self.assertTrue(skills.get_skill("github_repository_read_skill").enabled);self.assertFalse(skills.get_skill("github_merge_skill").enabled)
 def test_history_is_metadata_only(self):
  r,_=self.runtime();r.authenticated=True;r.read("repo");value=str(r.history);self.assertNotIn("token",value.lower());self.assertNotIn("body",value.lower())

if __name__=="__main__":unittest.main()
