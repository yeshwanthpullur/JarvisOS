from __future__ import annotations
import unittest
from dataclasses import replace
from commands import CommandManager
from jarvis.models import *

class FakeAdapter:
 def __init__(self,result="ok",error=None):self.result=result;self.error=error;self.calls=[]
 def health(self):return not self.error
 def models(self):return ("model",)
 def infer(self,model,prompt,timeout):
  self.calls.append((model,prompt,timeout))
  if self.error:raise self.error
  return self.result

class AdvancedRuntimeTests(unittest.TestCase):
 def ready(self):
  r=AdvancedModelRuntime();r.runtimes["ollama"]=replace(r.runtimes["ollama"],installed=True,state=RuntimeState.HEALTHY);r.adapters["ollama"]=FakeAdapter();return r
 def test_models_and_states(self):
  r=AdvancedModelRuntime();self.assertEqual(r.profiles["nemotron_ultra"].artifact_state,ArtifactState.METADATA_ONLY);self.assertEqual(r.runtimes["nvidia_nim"].state,RuntimeState.NOT_INSTALLED)
 def test_endpoint_security(self):
  InferenceEndpoint("local","vllm","http://127.0.0.1:8000/v1","local",allowed=True)
  with self.assertRaises(ValueError):InferenceEndpoint("bad","vllm","http://0.0.0.0:8000","local")
  with self.assertRaises(ValueError):InferenceEndpoint("bad","nim","http://example.com","remote")
  with self.assertRaises(ValueError):InferenceEndpoint("bad","nim","https://user:pass@example.com","remote")
 def test_hardware_privacy_and_cpu_only(self):
  h=AdvancedModelRuntime.discover_hardware();self.assertGreaterEqual(h.logical_cores,1);self.assertFalse(hasattr(h,"serial_number"));self.assertFalse(hasattr(h,"hostname"))
 def test_mock_nvidia_hardware_and_resource_plan(self):
  h=HardwareSnapshot("Windows","AMD64",16,"32-64GB",True,"NVIDIA","16-24GB",True,"available","100GB+");r=AdvancedModelRuntime(hardware=h);self.assertTrue(r.hardware.cuda_available);self.assertIn(r.resource_plan("nemotron_ultra").compatibility,{"runtime_missing","likely_compatible"})
 def test_aliases_unresolved(self):
  r=AdvancedModelRuntime();self.assertEqual(r.route("use Nemotron Ultra").status,"unavailable");self.assertEqual(r.route("use Nemotron Super").status,"unavailable")
 def test_resolved_nim_remote_obeys_egress(self):
  r=AdvancedModelRuntime();r.add_endpoint(InferenceEndpoint("nim","nvidia_nim","https://nim.example.com/v1","remote",authenticated=True,allowed=True));self.assertEqual(r.route("Nemotron Ultra",allow_remote=False).status,"unavailable");self.assertEqual(r.route("Nemotron Ultra",allow_remote=True).runtime_id,"nvidia_nim")
 def test_vllm_local_and_llama_cpp_optional(self):
  r=AdvancedModelRuntime();self.assertIn(r.runtimes["vllm"].state,{RuntimeState.NOT_INSTALLED,RuntimeState.INSTALLED});self.assertIn("gguf",r.runtimes["llama_cpp"].supported_model_formats)
 def test_ollama_peer_route_preserved(self):
  r=self.ready();self.assertEqual(r.route("chat").runtime_id,"ollama")
 def test_capability_and_context_checks(self):
  r=self.ready();self.assertEqual(r.route("chat",required=("vision",)).reason,"capability_mismatch")
  r.profiles["small"]=replace(r.profiles["ollama_local"],model_id="small",context_window=100);self.assertEqual(r.route("x",specific="small",context_tokens=200).status,"needs_context_reduction")
 def test_secret_and_paid_remote_blocked(self):
  r=self.ready();self.assertEqual(r.route("api key=supersecretvalue").status,"blocked");self.assertFalse(r.policy.allow_paid);self.assertFalse(r.policy.allow_remote)
 def test_inference_and_bounded_output(self):
  r=self.ready();r.adapters["ollama"].result="x"*9000;result=r.infer("hello");self.assertEqual(result.status,"completed");self.assertLessEqual(len(result.output),8000)
 def test_timeout_and_circuit_breaker(self):
  r=self.ready();r.adapters["ollama"]=FakeAdapter(error=TimeoutError())
  for _ in range(3):r.infer("hello")
  self.assertEqual(r.circuits["ollama"].state,CircuitState.OPEN)
 def test_policy_errors_do_not_open_circuit(self):
  c=CircuitBreaker(threshold=1);c.failure("policy");self.assertEqual(c.state,CircuitState.CLOSED)
 def test_half_open_and_recovery(self):
  clock=[0.0];c=CircuitBreaker(threshold=1,cooldown=1,clock=lambda:clock[0]);c.failure();clock[0]=2;self.assertTrue(c.allow());self.assertEqual(c.state,CircuitState.HALF_OPEN);c.success();self.assertEqual(c.state,CircuitState.CLOSED)
 def test_fallback_preserves_profile(self):
  r=AdvancedModelRuntime(policy=RuntimePolicy(allow_remote=True,max_fallbacks=1));r.profiles["test"]=ModelProfile("test","Test","test",runtime_ids=("vllm","llama_cpp"),capabilities=("reasoning",),readiness="ready");r.runtimes["vllm"]=replace(r.runtimes["vllm"],installed=True);r.runtimes["llama_cpp"]=replace(r.runtimes["llama_cpp"],installed=True);r.adapters={"vllm":FakeAdapter(error=TimeoutError()),"llama_cpp":FakeAdapter("fallback")};x=r.infer("reason",profile_id="test",required=("reasoning",));self.assertTrue(x.fallback_used);self.assertEqual(x.output,"fallback")
 def test_structured_output_validation(self):
  r=self.ready();r.adapters["ollama"].result="not-json";self.assertEqual(r.infer("x",structured=True).error,"invalid_structured_output")
 def test_model_output_has_no_tool_authority(self):
  r=self.ready();r.adapters["ollama"].result='{"tool":"delete"}';x=r.infer("x");self.assertIn("cannot execute tools",x.warnings[0])
 def test_lifecycle_is_plan_only(self):
  r=AdvancedModelRuntime();self.assertIn("executed=no",r.lifecycle_plan("start","vllm"));self.assertFalse(r.policy.allow_auto_start);self.assertFalse(r.policy.allow_auto_download)
 def test_bounded_queue_and_cancellation(self):
  r=AdvancedModelRuntime();request_id=r.enqueue("private content is preview bounded");self.assertTrue(r.cancel(request_id));self.assertEqual(r.queue[0]["status"],"cancelled");self.assertLessEqual(len(r.queue[0]["prompt_preview"]),80)
 def test_provider_registry_reference_is_preserved(self):
  marker=object();self.assertIs(AdvancedModelRuntime(provider_registry=marker).provider_registry,marker)
 def test_cli_commands(self):
  m=CommandManager();m.initialize();cmds=("model runtime-status","model runtimes","model runtime-show vllm","model runtime-health vllm","model profiles","model profile-show nemotron_ultra","model provider-health nvidia_nim","model hardware","model compatibility nemotron_ultra","model resource-plan nemotron_ultra","model route-explain Nemotron Ultra","model start-plan vllm","model start vllm","model stop vllm","model download-plan nemotron_ultra","model download-status nemotron_ultra","model fallback-status","model circuit-status","model aliases","model alias-show nemotron_super")
  for cmd in cmds:
   out=m.execute(cmd).response;self.assertNotIn("unknown command",out.lower());self.assertLess(len(out),3000);self.assertNotIn("C:\\Users",out)
 def test_config_defaults(self):
  from config import load_settings
  c=load_settings().models;self.assertTrue(c.runtime_enabled);self.assertFalse(c.runtime_allow_remote);self.assertFalse(c.runtime_allow_paid);self.assertFalse(c.runtime_allow_auto_download)

if __name__=="__main__":unittest.main()
