import tempfile, unittest
from dataclasses import replace
from pathlib import Path
from commands.command_parser import CommandParser
from jarvis.autonomous_planning import AutonomousPlanning, PlanStatus, PlanningLimits, StepStatus
from jarvis.jarvis_tools import JarvisTools

class AutonomousPlanningTests(unittest.TestCase):
 def setUp(self):self.p=AutonomousPlanning(tool_manager=JarvisTools())
 def make(self,text="Create a plan for adding a read-only system tool. Do not execute the plan."):
  o=self.p.create_objective("r",text,("Do not execute the plan",));return o,self.p.generate(o,"Provider-generated planning summary")
 def test_simple_avoids(self):self.assertFalse(self.p.assess("Hello").requires_plan)
 def test_complex_triggers(self):self.assertTrue(self.p.assess("Create a plan for implementation, testing and docs").requires_plan)
 def test_disabled_mode(self):self.assertEqual(self.p.set_mode("off").value,"off")
 def test_objective_normalized(self):o,_=self.make();self.assertEqual(o.parent_request_id,"r")
 def test_constraints_preserved(self):o,p=self.make();self.assertIn("Do not execute the plan",p.constraints)
 def test_unique_ids(self):_,p=self.make();self.assertEqual(len({s.step_id for s in p.steps}),len(p.steps))
 def test_plan_valid(self):_,p=self.make();self.assertTrue(p.validation.valid)
 def test_dependencies_valid(self):_,p=self.make();self.assertTrue(self.p.validate(p).valid)
 def test_cycle_detected(self):
  _,p=self.make(); a,b=p.steps[:2]; steps=(replace(a,dependencies=(b.step_id,)),replace(b,dependencies=(a.step_id,)),*p.steps[2:]);self.assertIn("dependency_cycle",self.p.validate(replace(p,steps=steps)).errors)
 def test_missing_dependency(self):_,p=self.make();self.assertIn("missing_dependency",self.p.validate(replace(p,steps=(replace(p.steps[0],dependencies=("missing",)),*p.steps[1:]))).errors)
 def test_step_limit(self):
  p=AutonomousPlanning(limits=PlanningLimits(maximum_steps=2));o=p.create_objective("r","Create a plan");plan=p.generate(o);self.assertIn("step_limit_exceeded",plan.validation.errors)
 def test_risk_escalates(self):_,p=self.make();self.assertEqual(p.risk_summary,"low")
 def test_permissions_planned(self):_,p=self.make();self.assertIn("plan.review",p.required_permissions)
 def test_approval_planned(self):_,p=self.make();self.assertTrue(p.required_approvals)
 def test_unavailable_tool(self):_,p=self.make();q=replace(p,required_tools=("missing",));self.assertIn("unavailable_tool",self.p.validate(q).errors)
 def test_handoff_blocked(self):_,p=self.make();self.assertEqual(self.p.handoff(p.plan_id)["status"],"blocked")
 def test_approved_handoff(self):_,p=self.make();self.p.approve(p.plan_id,"a");self.assertEqual(self.p.handoff(p.plan_id)["status"],"execution_ready")
 def test_handoff_does_not_mutate(self):_,p=self.make();self.p.approve(p.plan_id,"a");h=self.p.handoff(p.plan_id);self.assertIn("workflow_request",h)
 def test_pause_resume(self):_,p=self.make();self.p.pause(p.plan_id);self.assertEqual(self.p.resume(p.plan_id).status,PlanStatus.AWAITING_REVIEW)
 def test_cancel(self):_,p=self.make();self.assertEqual(self.p.cancel(p.plan_id).status,PlanStatus.CANCELLED)
 def test_invalid_resume(self):_,p=self.make();self.assertRaises(ValueError,self.p.resume,p.plan_id)
 def test_replan_versions(self):_,p=self.make();new=self.p.replan(p.plan_id,"change");self.assertEqual(new.version,2)
 def test_replan_supersedes(self):_,p=self.make();self.p.replan(p.plan_id,"change");self.assertEqual(self.p.plans[p.plan_id].status,PlanStatus.SUPERSEDED)
 def test_replan_limit(self):
  p=AutonomousPlanning(limits=PlanningLimits(maximum_replans=0));o=p.create_objective("r","Create a plan");plan=p.generate(o);self.assertRaises(ValueError,p.replan,plan.plan_id,"x")
 def test_persistence(self):
  with tempfile.TemporaryDirectory() as d:
   p=AutonomousPlanning(Path(d));o=p.create_objective("r","Create a plan");p.generate(o);self.assertTrue((Path(d)/"plans.json").exists())
 def test_command_separation(self):self.assertEqual(CommandParser().parse("plan status").name,"plan status")
 def test_no_tool_execution(self):
  tools=JarvisTools();_,p=self.make();self.assertEqual(tools.history(),())
 def test_steps_pending(self):_,p=self.make();self.assertTrue(all(s.status==StepStatus.PENDING for s in p.steps))
 def test_provider_summary_used(self):_,p=self.make();self.assertIn("Provider-generated",p.summary)

if __name__=="__main__":unittest.main()
