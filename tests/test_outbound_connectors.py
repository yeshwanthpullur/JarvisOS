import unittest
from commands import CommandManager
from config.schema import DiscordConfig,EmailConnectorConfig,SlackConfig
from jarvis.approvals import ApprovalDecisionType
from jarvis.execution.broker import ExecutionBroker
from jarvis.execution.models import ExecutionPermission,ExecutionRisk
from jarvis.integrations import *

class Transport:
 sent=[]
 def health(self,connector):return True
 def send(self,connector,destination,body,subject):self.sent.append((connector.provider_id,destination,subject,body));return "external-1"

class OutboundConnectorTests(unittest.TestCase):
 def setUp(self):
  Transport.sent=[];self.b=ExecutionBroker();self.creds=lambda key:"configured";self.items=build_outbound_connectors(broker=self.b,transport=Transport(),credential_getter=self.creds)
  for c in self.items.values():c.policy=ConnectorPolicy(enabled=True,allow_send=True,max_message_chars=100,max_sends_per_window=2);self.assertTrue(c.health().executed)
 def approval(self,c,destination,body,subject=""):
  req,_,_=c.plan(destination,body,subject);perm=ExecutionPermission.SEND_EMAIL if c.provider_id.startswith("email") else ExecutionPermission.SEND_MESSAGE;action="email_send" if c.provider_id.startswith("email") else f"{c.provider_id}_send";resources=(req.destination_ref,__import__('hashlib').sha256(f"{subject}:{body}".encode()).hexdigest()[:16]);a=self.b.approvals.create("send",action,(perm,ExecutionPermission.NETWORK_ACCESS),resources,risk=ExecutionRisk.HIGH);self.b.approvals.decide(a.approval_id,ApprovalDecisionType.APPROVE);return a.approval_id
 def test_states_and_credentials_hidden(self):
  for c in self.items.values():self.assertEqual(c.status()["state"],"ready");self.assertNotIn("configured",str(c.status().values()))
  missing=OutboundConnector("discord",("TOKEN",),credential_getter=lambda _:"");self.assertEqual(missing.status()["state"],"disabled")
 def test_destinations(self):
  self.assertTrue(self.items["discord"].validate_destination("channel_123")[0]);self.assertFalse(self.items["discord"].validate_destination("https://hook/secret")[0]);self.assertTrue(self.items["email_smtp"].validate_destination("a@example.com")[0]);self.assertFalse(self.items["email_smtp"].validate_destination("a@example.com\nBcc:x@y.com")[0]);self.assertTrue(self.items["slack"].validate_destination("C123ABC")[0])
 def test_secret_spam_mentions_and_header_injection_blocked(self):
  c=self.items["discord"]
  for body in ("api key=abc","hello @everyone","bulk send this"):self.assertFalse(c.plan("channel",body)[1])
  self.assertFalse(self.items["email_smtp"].plan("a@example.com","hello","ok\nBcc:x@y.com")[1])
 def test_send_requires_exact_approval(self):
  c=self.items["discord"];self.assertEqual(c.send("channel","hello").error,"approval_required");aid=self.approval(c,"channel","hello");self.assertTrue(c.send("channel","hello",aid).executed);self.assertEqual(len(Transport.sent),1)
 def test_changed_destination_or_content_invalidates_approval(self):
  c=self.items["slack"];aid=self.approval(c,"C123","hello");self.assertEqual(c.send("C999","hello",aid).error,"approval_required");self.assertEqual(c.send("C123","changed",aid).error,"approval_required")
 def test_each_provider_uses_distinct_broker_tool(self):
  for pid,dest in (("discord","chan"),("email_smtp","a@example.com"),("email_api","a@example.com"),("slack","C123")):
   c=self.items[pid];aid=self.approval(c,dest,"hello", "subject" if pid.startswith("email") else "");self.assertTrue(c.send(dest,"hello",aid,"subject" if pid.startswith("email") else "").executed)
  self.assertIn("discord_send_tool",self.b.tools);self.assertIn("email_send_tool",self.b.tools);self.assertIn("slack_send_tool",self.b.tools)
 def test_duplicate_and_rate_limit(self):
  c=self.items["discord"]
  for body in ("one","two"):
   self.assertTrue(c.send("chan",body,self.approval(c,"chan",body)).executed)
  self.assertEqual(c.send("chan","one",self.approval(c,"chan","one")).error,"duplicate_blocked");self.assertEqual(c.send("chan","three",self.approval(c,"chan","three")).error,"rate_limited")
 def test_future_capabilities_disabled(self):
  for c in self.items.values():self.assertFalse(c.policy.allow_inbound);self.assertFalse(c.policy.allow_attachments);self.assertFalse(c.policy.allow_bulk);self.assertFalse(c.policy.allow_scheduled_send)
  self.assertFalse(EmailConnectorConfig().allow_read);self.assertFalse(DiscordConfig().allow_webhook);self.assertFalse(SlackConfig().allow_inbound)
 def test_history_contains_no_body_or_recipient(self):
  c=self.items["email_smtp"];aid=self.approval(c,"private@example.com","private body","subject");c.send("private@example.com","private body",aid,"subject");value=str(c.history);self.assertNotIn("private body",value);self.assertNotIn("private@example.com",value)
 def test_cli(self):
  m=CommandManager();m.initialize()
  commands=("discord status","discord help","discord health","discord destinations","discord validate-destination C123","discord send-plan hello","discord send-dry-run hello","discord send C123 hello","discord rate-status","discord history","email status","email help","email providers","email health","email validate-address a@example.com","email send-plan hello","email send-dry-run hello","email send a@example.com hello","email rate-status","email history","slack status","slack help","slack health","slack destinations","slack validate-destination C123","slack send-plan hello","slack send-dry-run hello","slack send C123 hello","slack rate-status","slack history")
  for command in commands:
   out=m.execute(command).response;self.assertLess(len(out),3000);self.assertNotIn("unknown command",out.lower());self.assertNotIn("C:\\Users",out);self.assertNotIn("configured",out.split("credential_value=")[-1])
 def test_prime_routes_and_blocks_broadcast(self):
  from jarvis.agents import AgentRegistry,PrimeAgent,PrimeRequest,register_specialist_agents
  p=PrimeAgent(register_specialist_agents(AgentRegistry()))
  for text in ("send this to Discord","email this to my mentor","send this to Slack"):self.assertEqual(p.route(PrimeRequest(text)).selected_agent,"communication_agent")
  self.assertEqual(p.route(PrimeRequest("send this on Slack")).risk_level.value,"high")
  self.assertEqual(p.route(PrimeRequest("send this everywhere")).risk_level.value,"high")

if __name__=="__main__":unittest.main()
