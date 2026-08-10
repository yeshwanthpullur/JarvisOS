"""Central, metadata-only external provider registry."""
from __future__ import annotations
from .models import *

def _cap(name,desc,permissions=(),risk=ProviderRisk.LOW,approval=False,side_effects=()):return ProviderCapability(name,desc,tuple(permissions),tuple(side_effects),risk,approval)
def _provider(pid,name,cat,caps,*,local=False,cost=CostClass.UNKNOWN,credentials=(),reason="Not configured."):
 policy=ProviderPolicy(local_only=local,network_allowed=False,paid_allowed=False,execution_allowed=False,approval_required=True)
 return ExternalProvider(pid,name,cat,tuple(caps),credential_refs=tuple(credentials),local=local,cost_class=cost,policy=policy,reason=reason,limitations=("Execution is disabled in Prompt 71.",))
def default_providers()->tuple[ExternalProvider,...]:
 send=(_cap("send_message","Send an external message",("send_message","network_access"),ProviderRisk.HIGH,True,("external_message",)),)
 model=(_cap("model_inference","Run model inference",("network_access",),ProviderRisk.MEDIUM,True,("data_egress",)),)
 tool=(_cap("tool_execution","Invoke an external tool",("network_access","execute_tools"),ProviderRisk.HIGH,True,("external_execution",)),)
 return (
  _provider("telegram","Telegram",ProviderCategory.COMMUNICATION,send,credentials=("TELEGRAM_BOT_TOKEN",)),_provider("discord","Discord",ProviderCategory.COMMUNICATION,send,credentials=("DISCORD_BOT_TOKEN",)),_provider("email_smtp","Email SMTP",ProviderCategory.COMMUNICATION,send,credentials=("SMTP_PASSWORD",)),_provider("email_api","Email API",ProviderCategory.COMMUNICATION,send,credentials=("EMAIL_API_TOKEN",)),_provider("slack","Slack",ProviderCategory.COMMUNICATION,send,credentials=("SLACK_BOT_TOKEN",)),_provider("whatsapp_future","WhatsApp (future)",ProviderCategory.COMMUNICATION,send,reason="Future provider; no adapter exists."),
  _provider("github","GitHub remote service",ProviderCategory.DEVELOPER,(_cap("github_remote","Remote GitHub operations",("git_write","network_access"),ProviderRisk.HIGH,True,("remote_repository_change",)),),credentials=("GITHUB_TOKEN",),reason="Remote GitHub adapter is not configured; local Git remains separate."),
  _provider("ollama","Ollama local runtime",ProviderCategory.MODEL,model,local=True,cost=CostClass.FREE_LOCAL,reason="Existing local model runtime is represented but not probed here."),_provider("llama_cpp","llama.cpp",ProviderCategory.MODEL,model,local=True,cost=CostClass.FREE_LOCAL),_provider("vllm","vLLM",ProviderCategory.MODEL,model,local=True,cost=CostClass.FREE_LOCAL),_provider("nvidia_nim","NVIDIA NIM",ProviderCategory.MODEL,model,credentials=("NVIDIA_API_KEY",),cost=CostClass.PAID),_provider("nemotron_provider","Nemotron",ProviderCategory.MODEL,model,reason="No Nemotron runtime is installed or configured."),_provider("openai_compatible_endpoint","OpenAI-compatible endpoint",ProviderCategory.MODEL,model,credentials=("MODEL_API_KEY",),cost=CostClass.UNKNOWN),
  _provider("mcp_local","Local MCP",ProviderCategory.TOOLING,tool,local=True,reason="MCP execution remains disabled."),_provider("mcp_remote","Remote MCP",ProviderCategory.TOOLING,tool,credentials=("MCP_AUTH_TOKEN",),reason="Remote MCP is untrusted and disabled."),_provider("external_plugin","External plugin",ProviderCategory.TOOLING,tool,reason="External plugin loading and execution are disabled."),
 )
class ExternalProviderRegistry:
 def __init__(self,providers=()):self._providers={};[self.register(p) for p in providers]
 def register(self,p):
  if p.provider_id in self._providers:raise ValueError(f"duplicate provider: {p.provider_id}")
  if len({c.name for c in p.capabilities})!=len(p.capabilities):raise ValueError(f"duplicate capability in {p.provider_id}")
  self._providers[p.provider_id]=p
 def get(self,pid):return self._providers.get(pid)
 def list(self):return tuple(self._providers.values())
 def find(self,capability):return tuple(p for p in self.list() if any(c.name==capability for c in p.capabilities))
 def validate(self):return not any(not p.provider_id or not p.capabilities for p in self.list())
 def summary(self):
  values=self.list();return {"total":len(values),"ready":sum(p.state==ProviderState.READY for p in values),"enabled":sum(p.enabled for p in values),"configured":sum(p.configured for p in values),"execution_enabled":sum(p.policy.execution_allowed for p in values),"valid":self.validate()}
def build_external_provider_registry():return ExternalProviderRegistry(default_providers())
