import unittest
from types import SimpleNamespace
from commands import CommandManager
from conversation import ConversationContext,ConversationSession
from agents import *

def nodes():
 return (AgentTaskNode("research","research_agent","research"),AgentTaskNode("browser","browser_agent","browser",("research",)),AgentTaskNode("summary","prime_agent","merge",("browser",)))
class OrchestrationRuntimeTests(unittest.TestCase):
 def setUp(self):self.r=MultiAgentOrchestrationRuntime()
 def test_graph_and_owner(self):
  s=self.r.create("r",nodes());self.assertEqual(s.owner,"prime_agent");self.assertEqual(self.r.ready_nodes(s.session_id)[0].node_id,"research")
  with self.assertRaises(ValueError):self.r.create("r",nodes(),owner="research_agent")
 def test_cycle_orphan_self_rejected(self):
  for ns in ((AgentTaskNode("a","x","x",("b",)),),(AgentTaskNode("a","x","x",("b",)),AgentTaskNode("b","x","x",("a",))),(AgentTaskNode("a","x","x",("a",)),)):
   with self.assertRaises(ValueError):self.r.create("r",ns)
 def test_dependency_order_and_completion(self):
  s=self.r.create("r",nodes());self.r.mark(s.session_id,"research",NodeStatus.COMPLETED);self.assertEqual(self.r.ready_nodes(s.session_id)[0].node_id,"browser")
  self.r.mark(s.session_id,"browser",NodeStatus.COMPLETED);self.r.mark(s.session_id,"summary",NodeStatus.COMPLETED);self.assertEqual(s.current_state,SessionState.COMPLETED)
 def test_hard_and_soft_failure(self):
  s=self.r.create("r",nodes());self.r.mark(s.session_id,"research",NodeStatus.FAILED);self.assertFalse(self.r.ready_nodes(s.session_id));self.assertEqual(s.nodes["browser"].status,NodeStatus.BLOCKED)
  soft=(AgentTaskNode("a","x","x"),AgentTaskNode("b","y","y",("a",),DependencyType.SOFT));s=self.r.create("s",soft);self.r.mark(s.session_id,"a",NodeStatus.FAILED);self.assertEqual(self.r.ready_nodes(s.session_id)[0].node_id,"b")
 def test_context_version_segmentation_redaction(self):
  s=self.r.create("r",nodes());c=self.r.contexts[s.shared_context_id];c.update("research_agent","evidence",{"research":{"claim":"safe","api_key":"hidden"},"unknown":{"x":"y"}})
  self.assertEqual(len(c.versions),1);self.assertNotIn("hidden",str(c.versions));self.assertFalse(c.segment("unknown"))
 def test_messages_are_session_scoped_secret_free(self):
  s=self.r.create("r",nodes());m=OrchestrationMessage(s.session_id,"research_agent","browser_agent",MessageType.REQUEST,"context:research",("public",),correlation_id="c")
  self.assertEqual(self.r.send(m).correlation_id,"c")
  with self.assertRaises(ValueError):self.r.send(OrchestrationMessage("other","a","b",MessageType.REQUEST,"ref",("public",)))
  with self.assertRaises(ValueError):OrchestrationMessage(s.session_id,"a","b",MessageType.REQUEST,"api_key=hidden",("public",))
 def test_budget_inheritance_and_exhaustion(self):
  b=ExecutionBudget(max_provider_calls=1);self.assertEqual(b.narrowed(max_provider_calls=0).max_provider_calls,0)
  with self.assertRaises(ValueError):b.narrowed(max_provider_calls=2)
  s=self.r.create("r",nodes());s.resource_budget=b;self.assertTrue(self.r.consume(s.session_id,provider_calls=1));self.assertFalse(self.r.consume(s.session_id,provider_calls=1));self.assertIn("resource_budget_exhausted",s.warnings)
 def test_cancel_is_bounded_idempotent(self):
  s=self.r.create("r",nodes());self.assertTrue(self.r.cancel(s.session_id));self.assertFalse(self.r.cancel(s.session_id));self.assertEqual(s.current_state,SessionState.CANCELLED)
 def test_partial_success_and_metrics(self):
  s=self.r.create("r",nodes());self.r.mark(s.session_id,"research",NodeStatus.COMPLETED);self.r.mark(s.session_id,"browser",NodeStatus.TIMED_OUT);self.assertEqual(s.current_state,SessionState.PARTIAL_SUCCESS);self.assertEqual(self.r.metrics()["partial_success"],1)
 def test_no_execution_or_authority_api(self):
  self.assertFalse(hasattr(self.r,"execute"));status=self.r.status();self.assertFalse(status["approval_bypass"]);self.assertFalse(status["broker_bypass"]);self.assertEqual(status["authority"],"coordination_only")
 def test_cli_diagnostics_are_bounded(self):
  base=SimpleNamespace(runtime=self.r,registry=SimpleNamespace(list_agents=lambda:()))
  context=ConversationContext(session=ConversationSession(),metadata={"agent_manager":SimpleNamespace(orchestrator=base)})
  manager=CommandManager();manager.initialize()
  session=self.r.create("r",nodes())
  commands=("orchestrator status","orchestrator sessions",f"orchestrator show {session.session_id}",f"orchestrator graph {session.session_id}",f"orchestrator trace {session.session_id}","orchestrator metrics","orchestrator events","orchestrator health",f"orchestrator budget {session.session_id}","orchestrator agents","orchestrator providers")
  for command in commands:
   output=manager.execute(command,context).response;self.assertTrue(output);self.assertLess(len(output),4000);self.assertNotIn("C:\\Users",output)
if __name__=="__main__":unittest.main()
