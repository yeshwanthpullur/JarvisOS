import unittest
from commands import CommandManager
from config.schema import CommunicationConfig,ExternalProviderFlagsConfig
from jarvis.communication import *
from jarvis.integrations.models import DataClassification
from jarvis.skills import build_default_skill_registry

class ExternalCommunicationTests(unittest.TestCase):
 def setUp(self):self.f=ExternalCommunicationFoundation()
 def test_profiles_truthful(self):
  self.assertGreaterEqual(len(self.f.profiles),13);self.assertFalse(any(x.ready for x in self.f.profiles));self.assertEqual(self.f.profile("telegram").state,CommunicationProviderState.DISABLED)
 def test_models(self):
  d=self.f.validate_destination("telegram","12345");r=ExternalMessageRequest("telegram",d,body_preview="hello");p,v=self.f.plan("hello","telegram","12345");self.assertIsInstance(r,ExternalMessageRequest);self.assertIsInstance(p,ExternalMessagePlan);self.assertIsInstance(v,ExternalMessageValidation);self.assertFalse(v.provider_ready)
 def test_destination(self):
  self.assertTrue(self.f.validate_destination("telegram","12345").verified);self.assertFalse(self.f.validate_destination("email_smtp","bad").verified);self.assertTrue(self.f.validate_destination("email_smtp","a@example.com").verified)
 def test_content_classes_and_secrets(self):
  self.assertEqual(self.f.safety("project update")[0],DataClassification.PROJECT_INTERNAL);self.assertFalse(self.f.safety("password=hunter2")[1]);self.assertFalse(self.f.safety("send to 500 people")[1])
 def test_attachment_blocks(self):
  for name in (".env","private.key","credentials.json","data.db","model.bin"):self.assertFalse(self.f.check_attachment(name).allowed)
  self.assertEqual(self.f.check_attachment("notes.txt").blocked_reason,"attachments_disabled");self.assertEqual(self.f.check_attachment("run.exe").blocked_reason,"unsupported_type")
 def test_send_is_unavailable(self):
  p,v=self.f.plan("send hello","telegram","12345");self.assertFalse(v.policy_allowed);self.assertFalse(v.approval_valid);self.assertIn("send",p.blocked_actions)
 def test_rate_and_duplicate_metadata(self):self.assertFalse(self.f.rate_status("telegram")["rate_limited"]);self.assertEqual(len(self.f.fingerprints),0)
 def test_adapter_cannot_send(self):
  with self.assertRaises(RuntimeError):CommunicationProviderAdapter().send(None)
 def test_config_defaults(self):
  c=CommunicationConfig();f=ExternalProviderFlagsConfig();self.assertTrue(c.external_require_approval);self.assertFalse(c.external_allow_attachments);self.assertFalse(c.allow_bulk_messages);self.assertFalse(f.telegram_enabled)
 def test_skills(self):
  r=build_default_skill_registry();self.assertIsNotNone(r.get_skill("destination_validation_skill"));self.assertFalse(r.get_skill("bulk_message_skill").enabled)
 def test_cli(self):
  m=CommandManager();m.initialize()
  cmds=("communication provider-status","communication provider-show telegram","communication provider-health telegram","communication destination-validate telegram 12345","communication send-plan send a test message on Telegram","communication send-safety send a test message on Telegram","communication send-dry-run send a test message on Telegram","communication attachment-check .env","communication rate-status telegram")
  for c in cmds:
   out=m.execute(c).response;self.assertLess(len(out),2000);self.assertNotIn("unknown command",out.lower());self.assertNotIn("C:\\Users",out)
 def test_existing_draft_never_sends(self):
  r=CommunicationAgent().plan("draft hello",True);self.assertFalse(r.draft.send_available)
if __name__=="__main__":unittest.main()
