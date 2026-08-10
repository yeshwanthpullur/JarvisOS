import unittest
from jarvis.agents import AgentRegistry,PrimeAgent,register_specialist_agents
from jarvis.models import ModelRouter,build_default_model_registry
from jarvis.skills import build_default_skill_registry
from jarvis.evaluation import *
class EvaluationTests(unittest.TestCase):
 def build(self):
  registry=register_specialist_agents(AgentRegistry());model=ModelRouter(build_default_model_registry());skills=build_default_skill_registry();return EvaluationRunner(PrimeAgent(registry,model_router=model,skill_registry=skills))
 def test_models_and_local_policy(self):
  e=EvaluationCase("x","safety","input",expected_blocked=True);self.assertTrue(e.expected_blocked);self.assertEqual(self.build().status()["cloud_telemetry"],"disabled")
 def test_routing_safety_truthfulness(self):
  a=self.build();self.assertTrue(all(x.passed for x in a.routing()));self.assertTrue(all(x.passed and x.actual_blocked for x in a.safety()));self.assertTrue(all(x.passed for x in a.truthfulness()))
 def test_observability_bounded_and_run(self):
  a=self.build();s=a.observability();self.assertIn("total_agents",s.agents_summary);r=a.run();self.assertEqual(r.status,"passed");self.assertEqual(r.evaluation_summary.failed,0)
 def test_cli(self):
  a=self.build()
  for c in ("evaluation status","evaluation help","evaluation routing","evaluation safety","evaluation truthfulness","evaluation observability","evaluation run","evaluation history"):self.assertLess(len(render_evaluation_command(a,c,())),5000)
if __name__=="__main__":unittest.main()
