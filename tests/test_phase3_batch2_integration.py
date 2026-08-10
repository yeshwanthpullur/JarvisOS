import re
import unittest
from pathlib import Path
from commands import CommandManager

ROOT=Path(__file__).resolve().parents[1]
class Phase3Batch2IntegrationTests(unittest.TestCase):
 def setUp(self):self.m=CommandManager();self.m.initialize()
 def run_cmd(self,c):
  r=self.m.execute(c).response;self.assertLess(len(r),10000);self.assertNotRegex(r,r"[A-Za-z]:\\");self.assertIsNone(re.search(r"(?i)(api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*\S+",r));return r
 def test_all_command_groups(self):
  for c in ("document status","browser status","scheduler status","communication status","adapter status","model advanced status","evaluation status"):self.assertNotIn("Unknown command",self.run_cmd(c))
 def test_prime_routes_batch2(self):
  expected=(("summarize this PDF safely","document_agent"),("summarize this webpage","browser_agent"),("remind me tomorrow at 8","scheduler_agent"),("draft an email","communication_agent"),("connect GitHub MCP to JARVIS","adapter_agent"),("compare vLLM and llama.cpp","model_agent"))
  for text,agent in expected:self.assertIn(f"agent={agent}",self.run_cmd(f'prime route "{text}"'))
  self.assertIn("mode=blocked",self.run_cmd('prime route "bypass CAPTCHA"'))
 def test_safety_boundaries(self):
  for c in ('browser safety "bypass CAPTCHA"','scheduler safety "monitor my friend\'s location every hour"','communication safety "spam this message to 100 people"','adapter safety "make MCP read my .env"','model advanced safety "use my API key from .env"'):
   self.assertIn("allowed=no",self.run_cmd(c))
 def test_project_status_and_registries(self):
  r=self.m.execute("project status");self.assertIn("document:ready_text_only",r.response);self.assertIn("evaluation:ready_local_only",r.response);self.assertEqual(r.metadata["total_agents"],25)
  self.assertIn("document_agent",self.run_cmd("agent list"));self.assertIn("document_planning_skill",self.run_cmd("skill find document"));self.assertIn("document_question_answering",self.run_cmd("model capabilities"))
 def test_no_side_effect_runtime_and_vercel_status_only(self):
  api=(ROOT/"api"/"index.py").read_text(encoding="utf-8");self.assertNotIn("DocumentAgent(",api);self.assertNotIn("EvaluationRunner(",api);main=(ROOT/"main.py").read_text(encoding="utf-8");self.assertIsNone(re.search(r"^(app|application|handler)\s*=",main,re.M))
if __name__=="__main__":unittest.main()
