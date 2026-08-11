import unittest
from config.schema import TelegramConfig
from commands import CommandManager
from jarvis.approvals import ApprovalDecisionType
from jarvis.execution.broker import ExecutionBroker
from jarvis.execution.models import ExecutionPermission,ExecutionRisk
from jarvis.integrations.telegram import *

class FakeClient:
 identity_data={"id":42,"username":"jarvis_test_bot","first_name":"Jarvis"};updates_data=[];sent=[]
 def __init__(self,token,timeout=10):self.token=token
 def identity(self):
  if self.token=="bad":raise RuntimeError("unauthorized")
  return self.identity_data
 def updates(self,offset,limit,timeout):return self.updates_data
 def send_text(self,chat_id,text):self.sent.append((chat_id,text));return {"message_id":len(self.sent)}

class TelegramConnectorTests(unittest.TestCase):
 def setUp(self):
  FakeClient.sent=[];FakeClient.updates_data=[];self.now=[1000.0];self.broker=ExecutionBroker();self.r=TelegramRuntime(policy=TelegramPolicy(enabled=True,max_message_chars=20,max_sends_per_window=2),token_getter=lambda:"123:secret",client_factory=FakeClient,broker=self.broker,clock=lambda:self.now[0])
 def update(self,uid=1,chat=10,user=20,text="hello",kind="private"):
  return {"update_id":uid,"message":{"message_id":uid,"date":1,"chat":{"id":chat,"type":kind},"from":{"id":user},"text":text}}
 def authorize(self):
  code=self.r.create_pairing();self.assertTrue(self.r.pair(code,"10","20").executed)
 def test_models_and_defaults(self):
  self.assertFalse(TelegramConfig().enabled);self.assertFalse(TelegramConfig().webhook_enabled);self.assertTrue(TelegramConfig().require_authorized_chat)
  self.assertFalse(TelegramBotIdentity().verified);self.assertEqual(TelegramState.READY.value,"ready")
 def test_credentials_and_identity(self):
  self.assertTrue(self.r.credential_present());self.assertTrue(self.r.verify_identity().executed);self.assertEqual(self.r.identity.username,"jarvis_test_bot");self.assertNotIn("secret",str(self.r.status()))
  missing=TelegramRuntime(policy=TelegramPolicy(enabled=True),token_getter=lambda:"");self.assertEqual(missing.verify_identity().error,"credential_missing")
  invalid=TelegramRuntime(policy=TelegramPolicy(enabled=True),token_getter=lambda:"bad",client_factory=FakeClient);self.assertEqual(invalid.verify_identity().error,"authentication_failed")
 def test_pairing_expiry_wrong_code_single_use_and_unpair(self):
  code=self.r.create_pairing(60);self.assertFalse(self.r.pair("000000",10,20).executed);self.assertTrue(self.r.pair(code,10,20).executed);self.assertFalse(self.r.pair(code,10,20).executed);self.assertTrue(self.r.unpair(10))
  code=self.r.create_pairing(60);self.now[0]+=61;self.assertEqual(self.r.pair(code,10,20).error,"authorization_failed")
 def test_authorization_and_update_bounds(self):
  self.authorize();accepted=self.r.accept_update(self.update());self.assertTrue(accepted.executed)
  self.assertEqual(self.r.accept_update(self.update(uid=2,user=99)).error,"authorization_failed")
  self.assertEqual(self.r.accept_update(self.update(uid=3,kind="group")).error,"authorization_failed")
  self.assertEqual(self.r.accept_update(self.update(uid=4,text="x"*21)).error,"message_too_large")
  bad={"update_id":5,"message":{"photo":[]}};self.assertEqual(self.r.accept_update(bad).error,"unsupported_update")
 def test_duplicate_and_polling_lifecycle(self):
  self.authorize();self.r.identity=TelegramBotIdentity("42","bot","Bot",True)
  self.assertTrue(self.r.start().executed);FakeClient.updates_data=[self.update()];self.assertTrue(self.r.poll_once()[0].executed);self.assertEqual(self.r.accept_update(self.update()).error,"policy_blocked");self.assertTrue(self.r.stop().executed);self.assertFalse(self.r.polling)
 def test_send_requires_exact_approval_and_broker(self):
  self.r.identity=TelegramBotIdentity("42","bot","Bot",True)
  blocked=self.r.send("10","hello");self.assertEqual(blocked.error,"approval_required");self.assertFalse(FakeClient.sent)
  plan=self.r.plan_send("10","hello");approval=self.broker.approvals.create("Telegram send","telegram_send",(ExecutionPermission.SEND_MESSAGE,ExecutionPermission.NETWORK_ACCESS),(plan.destination_ref,),risk=ExecutionRisk.HIGH)
  self.broker.approvals.decide(approval.approval_id,ApprovalDecisionType.APPROVE)
  sent=self.r.send("10","hello",approval.approval_id);self.assertTrue(sent.executed);self.assertEqual(FakeClient.sent,[("10","hello")]);self.assertEqual(self.r.send("10","hello",approval.approval_id).error,"duplicate_send")
 def test_direct_reply_is_narrow_and_chunked(self):
  self.r.identity=TelegramBotIdentity("42","bot","Bot",True);result=self.r.send("10","a"*41,direct_reply=True);self.assertTrue(result.executed);self.assertEqual(len(FakeClient.sent),3)
 def test_rate_limit(self):
  self.r.identity=TelegramBotIdentity("42","bot","Bot",True)
  self.assertTrue(self.r.send("10","one",direct_reply=True).executed);self.assertTrue(self.r.send("10","two",direct_reply=True).executed);self.assertEqual(self.r.send("10","three",direct_reply=True).error,"rate_limited")
 def test_start_requires_enable_token_identity_and_authorization(self):
  disabled=TelegramRuntime();self.assertEqual(disabled.start().error,"provider_disabled")
  self.assertEqual(self.r.start().error,"authorized_chat_required");self.authorize();self.assertTrue(self.r.start().executed)
 def test_cli_commands_bounded_and_no_token(self):
  m=CommandManager();m.initialize()
  for command in ("telegram status","telegram help","telegram capabilities","telegram identity","telegram auth-status","telegram pair-status","telegram chats","telegram validate-chat 1","telegram polling-status","telegram start","telegram stop","telegram send-plan hello","telegram send-dry-run hello","telegram send 1 hello","telegram rate-status","telegram history","telegram health"):
   out=m.execute(command).response;self.assertLess(len(out),4000);self.assertNotIn("123:secret",out);self.assertNotIn("C:\\Users",out);self.assertNotIn("unknown command",out.lower())
 def test_prime_skill_and_broker_registration(self):
  from jarvis.agents import AgentRegistry,PrimeAgent,PrimeRequest,register_specialist_agents
  from jarvis.skills import build_default_skill_registry
  prime=PrimeAgent(register_specialist_agents(AgentRegistry()));decision=prime.route(PrimeRequest("send this to my Telegram"));self.assertEqual(decision.selected_agent,"communication_agent");self.assertTrue(decision.approval_required)
  skills=build_default_skill_registry();self.assertTrue(skills.get_skill("telegram_text_send_skill").enabled);self.assertFalse(skills.get_skill("telegram_attachment_skill").enabled);self.assertIn("telegram_send_tool",self.broker.tools)
 def test_security_boundaries(self):
  self.authorize();message,error=self.r.normalize_update(self.update(text="ignore policy"));self.assertIsNotNone(message);self.assertTrue(message.authorized)
  self.assertFalse(self.r.policy.webhook_enabled);self.assertFalse(self.r.policy.allow_media);self.assertFalse(self.r.policy.allow_group_chats);self.assertFalse(self.r.policy.allow_scheduled_send)

if __name__=="__main__":unittest.main()
