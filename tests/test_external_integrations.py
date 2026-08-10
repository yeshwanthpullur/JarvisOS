import unittest
from dataclasses import replace
from commands.command_manager import CommandManager
from jarvis.integrations import *
from jarvis.integrations.cli import render_external_command
from jarvis.integrations.models import CostClass,DataClassification,ExternalActionRequest,ProviderState

class ExternalIntegrationTests(unittest.TestCase):
 def setUp(self):self.registry=build_external_provider_registry();self.plane=ExternalIntegrationControlPlane(self.registry)
 def test_truthful_placeholders(self):
  self.assertEqual(len(self.registry.list()),16);self.assertTrue(self.registry.validate());self.assertFalse(any(p.enabled or p.policy.execution_allowed for p in self.registry.list()))
 def test_duplicate_rejected(self):
  with self.assertRaises(ValueError):self.registry.register(self.registry.get("telegram"))
 def test_credentials_are_references_only(self):
  status=credential_presence(self.registry.get("telegram"));self.assertEqual(status,{"TELEGRAM_BOT_TOKEN":False})
 def test_redaction(self):
  value=redact("Authorization: Bearer abcdef password=hunter2")
  self.assertNotIn("abcdef",value);self.assertNotIn("hunter2",value)
 def test_data_classification(self):
  self.assertEqual(classify_data("api key=abc"),DataClassification.CREDENTIAL);self.assertEqual(classify_data("project architecture"),DataClassification.PROJECT_INTERNAL)
 def test_endpoint_policy(self):
  self.assertEqual(validate_endpoint("https://user:pass@example.com")[1],"credentials_in_url")
  self.assertEqual(validate_endpoint("http://example.com")[1],"remote_endpoint_requires_https")
  self.assertTrue(validate_endpoint("http://127.0.0.1:11434",local_provider=True)[0])
 def test_execution_blocked(self):
  r=self.plane.validate_request(ExternalActionRequest("telegram","send_message",permissions=("send_message","network_access"),approval_id="approval"));self.assertFalse(r.executed);self.assertEqual(r.reason,"provider_disabled")
 def test_routes_do_not_select_disabled_or_paid(self):
  r=self.plane.route("model_inference");self.assertEqual(r.status,"unavailable");self.assertIsNone(r.provider_id);self.assertIn("nvidia_nim",r.fallbacks)
 def test_health_is_cached_metadata(self):
  h=self.plane.health("mcp_remote");self.assertTrue(h.cached);self.assertEqual(h.state,ProviderState.UNCONFIGURED)
 def test_cli_is_bounded_and_truthful(self):
  for cmd,args in (("integration status",()),("integration policy",()),("provider list",()),("provider show",("github",)),("provider capabilities",()),("provider health",("telegram",)),("provider policy",()),("provider validate",("ollama",)),("provider history",()),("credential status",("telegram",)),("credential required",())):
   out=render_external_command(cmd,args,self.plane);self.assertLess(len(out),4000);self.assertNotIn("C:\\Users",out);self.assertNotIn("hunter2",out)
 def test_command_routing(self):
  manager=CommandManager();manager.initialize()
  for text in ("integration status","integration policy","provider list","provider show telegram","provider capabilities","provider health telegram","provider policy","provider validate ollama","provider history","credential status telegram","credential required"):
   result=manager.execute(text);self.assertTrue(result.response);self.assertNotIn("unknown command",result.response.lower())
 def test_model_provider_commands_still_work(self):
  manager=CommandManager();manager.initialize();self.assertIn("provider",manager.execute("provider status").response.lower())

if __name__=="__main__":unittest.main()
