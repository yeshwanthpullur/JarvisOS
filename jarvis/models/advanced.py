"""Advanced provider planning only; never installs, downloads, starts, or calls providers."""
from dataclasses import dataclass,field
from enum import StrEnum
import platform
from jarvis.foundation_common import contains_secret,new_id,now
class AdvancedProviderStatus(StrEnum):READY="ready";PLANNED="planned";DISABLED="disabled";NOT_CONFIGURED="not_configured";BLOCKED="blocked"
class AdvancedModelRiskLevel(StrEnum):LOW="low";MEDIUM="medium";HIGH="high";CRITICAL="critical"
@dataclass(frozen=True,slots=True)
class AdvancedProviderProfile:
 provider_id:str;display_name:str;provider_family:str;status:AdvancedProviderStatus=AdvancedProviderStatus.NOT_CONFIGURED;configured:bool=False;enabled:bool=False;execution_available:bool=False;install_available:bool=False;cloud_required:bool=False;local_supported:bool=True;requires_gpu:bool=False;requires_credentials:bool=False;supported_capabilities:tuple[str,...]=();missing_requirements:tuple[str,...]=();warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class HardwareCapability:
 cpu_available:bool=True;gpu_detected:bool=False;gpu_vendor:str="unknown";gpu_memory_category:str="unknown";system_memory_category:str="unknown";cuda_available:bool=False;metal_available:bool=False;rocm_available:bool=False;directml_available:bool=False;detection_method:str="safe_standard_library";confidence:float=.3;warnings:tuple[str,...]=("No heavy GPU diagnostics were run.",);hardware_id:str=field(default_factory=new_id)
@dataclass(frozen=True,slots=True)
class ModelRuntimePlan:
 provider_id:str;target_use_case:str;recommended_runtime:str;hardware_requirements:tuple[str,...];setup_steps:tuple[str,...];blocked_steps:tuple[str,...];configuration_needed:tuple[str,...];risk_level:AdvancedModelRiskLevel=AdvancedModelRiskLevel.MEDIUM;approval_required:bool=True;status:AdvancedProviderStatus=AdvancedProviderStatus.PLANNED;warnings:tuple[str,...]=();plan_id:str=field(default_factory=new_id)
@dataclass(frozen=True,slots=True)
class ModelSelectionPlan:
 use_case:str;candidate_providers:tuple[str,...];candidate_model_families:tuple[str,...];local_first_recommendation:str;fallback_route:str;constraints:tuple[str,...]=();missing_information:tuple[str,...]=();warnings:tuple[str,...]=();selection_id:str=field(default_factory=new_id)
@dataclass(frozen=True,slots=True)
class ProviderComparison:
 providers:tuple[str,...];use_case:str;criteria:tuple[str,...];summary:str;tradeoffs:tuple[str,...];recommended_next_step:str;confidence:float=.5;warnings:tuple[str,...]=();comparison_id:str=field(default_factory=new_id)
@dataclass(frozen=True,slots=True)
class AdvancedModelResult:
 request_id:str;status:AdvancedProviderStatus;request:str;profiles:tuple[AdvancedProviderProfile,...]=();plan:ModelRuntimePlan|None=None;hardware:HardwareCapability|None=None;selection:ModelSelectionPlan|None=None;comparison:ProviderComparison|None=None;output:str="";warnings:tuple[str,...]=();error:str|None=None
def default_advanced_providers():
 specs=(("nemotron","Nemotron","nemotron",True,False),("nvidia_nim","NVIDIA NIM","nvidia_nim",True,True),("vllm","vLLM","vllm",True,False),("llama_cpp","llama.cpp","llama_cpp",False,False),("tensorrt_llm","TensorRT-LLM","tensorrt_llm",True,False),("litellm","LiteLLM","litellm",False,False),("openai_compatible_local","Local OpenAI-compatible endpoint","openai_compatible_local",False,False),("huggingface_tgi","Hugging Face TGI","huggingface_tgi",True,False),("sglang","SGLang","sglang",True,False),("localai","LocalAI","localai",False,False),("custom_local_server","Custom local server","custom_local_server",False,False),("cloud_api_disabled","Cloud API","cloud_api_disabled",False,True))
 return tuple(AdvancedProviderProfile(i,n,f,AdvancedProviderStatus.DISABLED if i=="cloud_api_disabled" else AdvancedProviderStatus.NOT_CONFIGURED,requires_gpu=g,requires_credentials=c,supported_capabilities=("planning",),missing_requirements=("runtime_not_configured",),warnings=("No installation, download, startup, credential access, or provider call is performed.",)) for i,n,f,g,c in specs)
class AdvancedModelPlanner:
 def __init__(self):self.profiles=default_advanced_providers();self.history=[]
 def status(self):return {"status":"ready_planning_only","local_first":True,"cloud":"disabled","install":"disabled","download":"disabled","runtime_start":"disabled","docker":"disabled","credentials":"blocked"}
 def profile(self,i):return next((p for p in self.profiles if p.provider_id==i),None)
 def safety(self,t):
  v=t.lower()
  if contains_secret(t) or "api key" in v:return AdvancedModelRiskLevel.CRITICAL,False,"Credential and .env access is blocked."
  if any(x in v for x in ("start ","install ","download ","docker","container")):return AdvancedModelRiskLevel.HIGH,False,"Install, download, Docker, and runtime startup are disabled."
  return AdvancedModelRiskLevel.MEDIUM,True,"Provider planning and comparison are allowed."
 def hardware(self):return HardwareCapability(cpu_available=bool(platform.processor() or platform.machine()))
 def plan(self,t):
  risk,ok,why=self.safety(t);v=t.lower();provider=next((p.provider_id for p in self.profiles if p.provider_id.replace("_"," ") in v or p.display_name.lower() in v),"unresolved_provider");plan=ModelRuntimePlan(provider,"local_jARVIS","future_configured_local_runtime",("Review broad CPU/GPU/RAM requirements.",),("Review provider documentation.","Choose local runtime and model intentionally.","Configure only in a future approved milestone."),("install","download","start_server","cloud_call","credential_access"),("runtime","model","hardware confirmation"),risk,True,AdvancedProviderStatus.PLANNED if ok else AdvancedProviderStatus.BLOCKED,(why,));r=AdvancedModelResult(new_id(),plan.status,t,self.profiles,plan,hardware=self.hardware(),warnings=(why,),error=None if ok else "blocked_by_advanced_model_policy");self.history=(self.history+[r])[-25:];return r
 def compare(self,a,b):return ProviderComparison((a,b),"local_jARVIS",("hardware","deployment","privacy","latency","throughput"),f"{a} and {b} remain unconfigured planning candidates.",(f"{a}: review server/deployment fit.",f"{b}: review local runtime and hardware fit."),"Keep Ollama as the current verified local fallback until a separate provider milestone is approved.",.6,("No benchmark or provider call was performed.",))
 def route(self,t):return ModelSelectionPlan(t,("ollama_text","ollama_vision"),("current_local","advanced_planned"),"Use an existing ready local provider when capability matches.","unavailable if no ready local provider",("cloud disabled","advanced runtimes disabled"),("Hardware and model requirements may be unknown.",))
def render_advanced_model_command(p,c,args):
 t=" ".join(args).strip()
 if c=="model advanced status":return "Advanced model status: "+" ".join(f"{k}={v}" for k,v in p.status().items())
 if c=="model advanced providers":return "Advanced providers: "+", ".join(f"{x.provider_id}:{x.status.value}:execute=no" for x in p.profiles)
 if c=="model advanced show":
  x=p.profile(t);return "Advanced provider unavailable." if x is None else f"Advanced provider: id={x.provider_id} status={x.status.value} configured=no enabled=no execution=no requires_gpu={'yes' if x.requires_gpu else 'no'} credentials={'required' if x.requires_credentials else 'not_required'}."
 if c=="model advanced plan":
  r=p.plan(t);return f"Advanced model plan: status={r.status.value} provider={r.plan.provider_id} execution=no steps="+" | ".join(r.plan.setup_steps)
 if c=="model advanced compare":
  x=p.compare(args[0] if args else "unknown",args[1] if len(args)>1 else "unknown");return f"Advanced model comparison: providers={','.join(x.providers)} summary={x.summary} next={x.recommended_next_step}"
 if c=="model advanced hardware":
  h=p.hardware();return f"Advanced hardware: cpu={'available' if h.cpu_available else 'unknown'} gpu={'detected' if h.gpu_detected else 'unknown'} memory={h.system_memory_category} cuda={'available' if h.cuda_available else 'unknown'} method={h.detection_method}."
 if c=="model advanced route":
  x=p.route(t);return f"Advanced route: use_case={x.use_case} recommendation={x.local_first_recommendation} fallback={x.fallback_route}."
 if c=="model advanced safety":
  r,ok,why=p.safety(t);return f"Advanced model safety: risk={r.value} allowed={'yes' if ok else 'no'} reason={why}"
 if c=="model advanced checklist":
  x=p.profile(t);return "Advanced provider unavailable." if x is None else f"Advanced checklist {x.provider_id}: review hardware; select runtime; review privacy; configure in future approved milestone. No install/download/start performed."
 if c=="model advanced history":return "Advanced model history: "+(", ".join(f"{x.request_id}:{x.status.value}" for x in p.history[-10:]) or "empty")
 return "Advanced model command unavailable."
