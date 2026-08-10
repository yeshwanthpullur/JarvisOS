import unittest
from jarvis.browser import *
from jarvis.scheduler import *
from jarvis.communication import *

class Batch2PlanningAgentTests(unittest.TestCase):
 def test_browser_read_only_and_unsafe_block(self):
  a=BrowserAgent();self.assertEqual(a.plan("summarize this webpage").status,BrowserStatus.PLANNED);self.assertEqual(a.plan("bypass CAPTCHA").status,BrowserStatus.BLOCKED);self.assertFalse(a.capabilities().login_allowed)
 def test_browser_commands(self):
  a=BrowserAgent()
  for c,args in (("browser status",()),("browser help",()),("browser capabilities",()),("browser plan",("summarize webpage",)),("browser safety",("login",)),("browser history",())):self.assertLess(len(render_browser_command(a,c,args)),5000)
 def test_scheduler_validation_and_no_runner(self):
  a=SchedulerAgent();self.assertTrue(a.validate("tomorrow at 8").valid);self.assertFalse(a.validate("every second").valid);self.assertFalse(a.plan("remind me tomorrow at 8").plan.background_execution_available);self.assertEqual(a.plan("monitor my friend's location every hour").status,ScheduleStatus.BLOCKED)
 def test_scheduler_commands(self):
  a=SchedulerAgent()
  for c,args in (("scheduler status",()),("scheduler capabilities",()),("scheduler validate",("tomorrow",)),("scheduler plan",("tomorrow",)),("scheduler history",())):self.assertLess(len(render_scheduler_command(a,c,args)),5000)
 def test_communication_draft_only(self):
  a=CommunicationAgent();r=a.plan("draft an email asking for internship opportunities",True);self.assertEqual(r.status,CommunicationStatus.DRAFTED);self.assertFalse(r.draft.send_available);self.assertEqual(a.plan("spam this to 100 people").status,CommunicationStatus.BLOCKED);self.assertTrue(all(not p.send_available for p in a.providers))
 def test_communication_commands(self):
  a=CommunicationAgent()
  for c,args in (("communication status",()),("communication providers",()),("communication draft",("hello",)),("communication safety",("spam 100 people",)),("communication history",())):self.assertLess(len(render_communication_command(a,c,args)),5000)
if __name__=="__main__":unittest.main()
