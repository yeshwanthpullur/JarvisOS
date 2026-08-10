import unittest
from jarvis.adapters import *
from jarvis.models.advanced import *

class AdapterAndAdvancedModelTests(unittest.TestCase):
 def test_adapter_manifest_only_and_policy(self):
  a=AdapterAgent();self.assertTrue(a.capabilities().mcp_supported_as_manifest);self.assertFalse(a.capabilities().mcp_runtime_available);self.assertTrue(all(not x.execution_available for x in a.manifests));self.assertEqual(a.plan("connect GitHub MCP to JARVIS").status,AdapterStatus.PLANNED);self.assertEqual(a.plan("make MCP read my .env").status,AdapterStatus.BLOCKED)
 def test_adapter_cli(self):
  a=AdapterAgent()
  for c,args in (("adapter status",()),("adapter list",()),("adapter show",("mcp_github_adapter",)),("adapter plan",("connect GitHub MCP",)),("adapter safety",("read .env",)),("adapter permissions",("mcp_github_adapter",)),("adapter capabilities",()),("adapter history",())):self.assertLess(len(render_adapter_command(a,c,args)),8000)
 def test_advanced_profiles_truthful(self):
  p=AdvancedModelPlanner();ids={x.provider_id for x in p.profiles};self.assertTrue({"nemotron","nvidia_nim","vllm","llama_cpp"}<=ids);self.assertTrue(all(not x.configured and not x.execution_available for x in p.profiles));self.assertEqual(p.plan("add Nemotron to JARVIS").status,AdvancedProviderStatus.PLANNED);self.assertEqual(p.plan("use API key from .env").status,AdvancedProviderStatus.BLOCKED)
 def test_advanced_cli_and_hardware_are_bounded(self):
  p=AdvancedModelPlanner()
  commands=(("model advanced status",()),("model advanced providers",()),("model advanced show",("nemotron",)),("model advanced plan",("add nemotron",)),("model advanced compare",("vllm","llama_cpp")),("model advanced hardware",()),("model advanced route",("coding",)),("model advanced safety",("use .env",)),("model advanced checklist",("nvidia_nim",)),("model advanced history",()))
  for c,args in commands:self.assertLess(len(render_advanced_model_command(p,c,args)),10000)
if __name__=="__main__":unittest.main()
