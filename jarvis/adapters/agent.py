from dataclasses import dataclass,field
from jarvis.foundation_common import contains_secret,new_id
from .models import *
def default_adapter_manifests():
 return (AdapterManifest("mcp_github_adapter","GitHub MCP planning",AdapterType.MCP_SERVER,"github",requires_credentials=True,supported_capabilities=("manifest_review","permission_planning"),warnings=("MCP runtime is disabled.",)),AdapterManifest("mcp_filesystem_adapter","Filesystem MCP planning",AdapterType.MCP_SERVER,"filesystem",requires_credentials=False,required_permissions=("read_files",),warnings=("Execution and private-path access are disabled.",)),AdapterManifest("external_plugin_adapter","External plugin planning",AdapterType.EXTERNAL_PLUGIN,"future",warnings=("Plugin installation and execution are disabled.",)),AdapterManifest("webhook_adapter","Webhook planning",AdapterType.WEBHOOK_CONNECTOR,"future",requires_credentials=True,warnings=("Network calls are disabled.",)))
def classify_adapter_intent(t):
 v=t.lower()
 if contains_secret(t) or any(x in v for x in ("read my .env","steal token","bypass permission")):return AdapterIntent.UNSAFE_TOOL_REQUEST
 if "install" in v:return AdapterIntent.INSTALL_PLUGIN_REQUEST
 if "execute" in v or "run shell" in v:return AdapterIntent.TOOL_EXECUTION_REQUEST
 if "mcp" in v:return AdapterIntent.MCP_SERVER_PLAN
 if "plugin" in v:return AdapterIntent.PLUGIN_INTEGRATION_PLAN
 return AdapterIntent.ADAPTER_PLANNING
def adapter_safety(t):
 i=classify_adapter_intent(t)
 if i is AdapterIntent.UNSAFE_TOOL_REQUEST:return AdapterRiskLevel.CRITICAL,False,"Credential, secret, and permission-bypass requests are blocked."
 if i in {AdapterIntent.INSTALL_PLUGIN_REQUEST,AdapterIntent.TOOL_EXECUTION_REQUEST,AdapterIntent.CREDENTIAL_REQUIRED_REQUEST}:return AdapterRiskLevel.HIGH,False,"Installation, execution, credentials, and server startup are disabled."
 return AdapterRiskLevel.MEDIUM,True,"Manifest and permission planning are allowed; no adapter runs."
@dataclass(slots=True)
class AdapterAgent:
 enabled:bool=True;manifests:tuple[AdapterManifest,...]=field(default_factory=default_adapter_manifests);max_history_items:int=25;history:list[AdapterResult]=field(default_factory=list)
 def _record(self,r):self.history=(self.history+[r])[-self.max_history_items:];return r
 def capabilities(self):return AdapterCapabilityStatus()
 def status(self):return {"status":"ready_manifest_only" if self.enabled else "disabled","mode":"plan_only","mcp_runtime":"disabled","plugin_execution":"disabled","plugin_install":"disabled","network":"disabled","credentials":"blocked","background_servers":"disabled"}
 def plan(self,t):
  risk,ok,reason=adapter_safety(t);intent=classify_adapter_intent(t);req=AdapterRequest(t," ".join(t.lower().split()),intent,risk_level=risk);status=AdapterStatus.PLANNED if ok else AdapterStatus.BLOCKED;target="mcp_github_adapter" if "github" in t.lower() else "unresolved_adapter"
  plan=AdapterPlan(req.request_id,intent,"Plan adapter metadata and permissions without execution.",target,("Select a disabled manifest.","Review declared permissions and risk.","Require a future sandbox, credential vault, approval path, and explicit runtime enablement."),risk_level=risk,status=status,warnings=(() if ok else(reason,)))
  return self._record(AdapterResult(req.request_id,status,req,plan,self.manifests,self.capabilities(),warnings=plan.warnings,error=None if ok else "blocked_by_adapter_policy"))
 def permissions(self,t):
  m=next((x for x in self.manifests if x.adapter_id==t),None);names=m.required_permissions if m else ("network_access","credentials_access","external_tool_execution");return tuple(AdapterPermission(new_id(),n,"adapter",AdapterRiskLevel.HIGH,True,False,"Permission is declared but not granted in this foundation.") for n in names)
 def show(self,i):return next((x for x in self.manifests if x.adapter_id==i),None)
 def show_job(self,i):return next((x for x in reversed(self.history) if x.request_id==i),None)
