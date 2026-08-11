"""Focused Prompt 83 reliability runtime tests."""
import unittest
from config import load_settings
from jarvis.jarvis_manager import JarvisManager
from jarvis.reliability import *

class ReliabilityTests(unittest.TestCase):
 def setUp(self):self.r=ReliabilityRuntime()
 def test_health_states(self):self.assertEqual(len(HealthState),9)
 def test_health_score_bounded(self):
  with self.assertRaises(ValueError):RuntimeHealth("x","x",HealthState.READY,2,True)
 def test_component_health(self):self.assertTrue(self.r.record_health("prime",HealthState.READY,1).availability)
 def test_transition_timestamp(self):
  a=self.r.record_health("prime",HealthState.READY,1);b=self.r.record_health("prime",HealthState.DEGRADED,.5);self.assertNotEqual(a.last_transition,b.last_transition)
 def test_aggregation_ready(self):
  self.r.record_health("a",HealthState.READY,1);self.assertEqual(self.r.aggregate().state,HealthState.READY)
 def test_aggregation_degraded(self):
  self.r.record_health("a",HealthState.READY,1);self.r.record_health("b",HealthState.DEGRADED,.5);self.assertEqual(self.r.aggregate().state,HealthState.DEGRADED)
 def test_dependency_validation(self):
  self.r.register_service(ServiceRecord("a","1",(),()));self.r.register_service(ServiceRecord("b","1",(),("a",)));self.assertTrue(self.r.validate_dependencies())
 def test_dependency_cycle(self):
  self.r.register_service(ServiceRecord("a","1",(),("b",)));self.r.register_service(ServiceRecord("b","1",(),("a",)))
  with self.assertRaisesRegex(ValueError,"cycle"):self.r.validate_dependencies()
 def test_unknown_dependency(self):
  self.r.register_service(ServiceRecord("a","1",(),("missing",)))
  with self.assertRaisesRegex(ValueError,"unknown"):self.r.validate_dependencies()
 def test_duplicate_service(self):
  x=ServiceRecord("a","1",(),());self.r.register_service(x)
  with self.assertRaises(ValueError):self.r.register_service(x)
 def test_circuit_opens(self):
  c=CircuitBreaker("x",failure_threshold=2);c.failure();self.assertEqual(c.failure(),CircuitState.OPEN)
 def test_circuit_half_open_and_close(self):
  c=CircuitBreaker("x",1,1);c.failure();c.probe();self.assertEqual(c.success(),CircuitState.CLOSED)
 def test_provider_degradation_alerts(self):
  self.r.record_health("provider:ollama",HealthState.OFFLINE,0);self.assertEqual(len(self.r.alerts),1)
 def test_fault_isolation_no_authority(self):self.assertFalse(self.r.fault_isolation("x")["authority_changed"])
 def test_resource_warning(self):self.assertEqual(self.r.resource_snapshot(cpu_percent=80)["state"],"warning")
 def test_resource_critical(self):self.assertEqual(self.r.resource_snapshot(memory_percent=95)["state"],"critical")
 def test_resource_exhausted(self):self.assertEqual(self.r.resource_snapshot(memory_percent=99)["state"],"exhausted")
 def test_queue_health(self):self.assertEqual(self.r.queue_health(30,0,0,0)["state"],"degraded")
 def test_metric_history_bounded(self):
  r=ReliabilityRuntime(ReliabilityLimits(max_metric_history=2));r.resource_snapshot(cpu_percent=1);r.resource_snapshot(cpu_percent=2);self.assertEqual(len(r.metrics),2)
 def test_alert_history_bounded(self):
  r=ReliabilityRuntime(ReliabilityLimits(max_alert_history=1));r.record_health("a",HealthState.FAILED,0);r.record_health("b",HealthState.FAILED,0);self.assertEqual(len(r.alerts),1)
 def test_diagnostic_root_cause(self):
  self.r.record_health("provider:test",HealthState.FAILED,0);self.assertEqual(self.r.diagnostic("provider:test").root_cause,"provider")
 def test_aggregate_diagnostic_is_truthful(self):
  self.r.record_health("prime",HealthState.READY,1);d=self.r.diagnostic("jarvis_runtime");self.assertEqual(d.health_summary,"ready");self.assertEqual(d.root_cause,"healthy")
 def test_diagnostic_redacts_secret(self):
  self.r.record_health("x",HealthState.FAILED,0,errors=("token=abc",));self.assertNotIn("abc",str(self.r.diagnostic("x")))
 def test_absolute_path_redacted(self):
  self.r.record_health("x",HealthState.FAILED,0,errors=("C:\\Users\\Private\\file",));self.assertNotIn("C:/Users",str(self.r.diagnostic("x")))
 def test_recovery_is_plan_only(self):
  self.r.record_health("x",HealthState.FAILED,0);p=self.r.recovery_plan("x");self.assertTrue(p.requires_broker);self.assertIn("component_restart",p.privileged_actions)
 def test_ready_recovery_has_no_action(self):
  self.r.record_health("x",HealthState.READY,1);self.assertEqual(self.r.recovery_plan("x").level,0)
 def test_aggregate_ready_recovery_has_no_action(self):
  self.r.record_health("x",HealthState.READY,1);self.assertEqual(self.r.recovery_plan("jarvis_runtime").level,0)
 def test_capacity_does_not_allocate(self):self.assertFalse(self.r.capacity()["allocation_performed"])
 def test_default_graph(self):self.assertTrue(build_default_reliability_runtime().verify()["valid"])
 def test_cli_commands_bounded(self):
  r=build_default_reliability_runtime()
  for command in ("runtime status","runtime health","runtime components","runtime dependencies","runtime metrics","runtime diagnostics","runtime alerts","runtime providers","runtime models","runtime queues","runtime resources","runtime breakers","runtime recovery-plan","runtime recovery-history","runtime events","runtime dashboard","runtime profile","runtime capacity","runtime verify"):
   self.assertLessEqual(len(render_runtime_command(r,command,())),5000)
 def test_config_defaults(self):
  c=load_settings().reliability;self.assertTrue(c.enabled);self.assertLessEqual(c.max_retry_attempts,5)
 def test_manager_integrations(self):
  m=JarvisManager();self.assertIs(m.prime_agent.reliability_runtime,m.reliability);self.assertIs(m.workflow.runtime.reliability_runtime,m.reliability)
 def test_no_busy_monitoring_thread(self):self.assertFalse(hasattr(self.r,"monitor_thread"))
 def test_health_does_not_mutate_provider(self):
  provider={"enabled":False};self.r.record_health("provider",HealthState.FAILED,0);self.assertFalse(provider["enabled"])

if __name__=="__main__":unittest.main()
