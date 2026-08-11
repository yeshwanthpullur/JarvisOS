"""Advanced multi-runtime model control plane with conservative local-first policy."""
from __future__ import annotations
import json,platform,shutil,time
from collections import deque
from dataclasses import dataclass,field
from enum import StrEnum
from typing import Any,Protocol
from urllib.parse import urlsplit
from jarvis.foundation_common import bounded,contains_secret,new_id

class ArtifactState(StrEnum):UNKNOWN="unknown";KNOWN="known";METADATA_ONLY="metadata_only";DOWNLOAD_REQUIRED="download_required";DOWNLOAD_PLANNED="download_planned";DOWNLOADING="downloading";DOWNLOADED="downloaded";VERIFIED="verified";INCOMPATIBLE="incompatible";CORRUPT="corrupt";READY="ready";LOADED="loaded";UNLOADED="unloaded";ERROR="error"
class RuntimeType(StrEnum):OLLAMA="ollama";VLLM="vllm";LLAMA_CPP="llama_cpp";NVIDIA_NIM="nvidia_nim";OPENAI_COMPATIBLE="openai_compatible";OTHER="other_future"
class RuntimeState(StrEnum):NOT_INSTALLED="not_installed";INSTALLED="installed";MISCONFIGURED="misconfigured";STOPPED="stopped";STARTING="starting";RUNNING="running";HEALTHY="healthy";DEGRADED="degraded";UNREACHABLE="unreachable";INCOMPATIBLE="incompatible";BLOCKED="blocked";ERROR="error"
class RouteMode(StrEnum):LOCAL_ONLY="local_only";LOCAL_PREFERRED="local_preferred";BALANCED="balanced";QUALITY="quality_preferred";FASTEST="fastest_available";SPECIFIC_PROVIDER="specific_provider";SPECIFIC_MODEL="specific_model"
class CircuitState(StrEnum):CLOSED="closed";OPEN="open";HALF_OPEN="half_open"

@dataclass(frozen=True,slots=True)
class ModelProfile:
 model_id:str;display_name:str;family:str;variant:str="";provider_ids:tuple[str,...]=();runtime_ids:tuple[str,...]=();local_capable:bool=True;remote_capable:bool=False;architecture:str="unknown";parameter_class:str="unknown";quantization:str="unknown";context_window:int=0;max_output_tokens:int=0;capabilities:tuple[str,...]=();tool_use:bool=False;structured_output:bool=False;vision:bool=False;reasoning:bool=False;coding:bool=False;research:bool=False;long_context:bool=False;multilingual:bool=False;hardware_requirements:tuple[str,...]=();memory_requirements:str="unknown";cost_class:str="free_local";privacy_class:str="local";artifact_state:ArtifactState=ArtifactState.METADATA_ONLY;readiness:str="unavailable";limitations:tuple[str,...]=();warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class InferenceRuntime:
 runtime_id:str;runtime_type:RuntimeType;display_name:str;installed:bool=False;executable_available:bool=False;server_capable:bool=True;local_or_remote:str="local";running:bool=False;endpoint:str="";version:str="unknown";gpu_support:bool=False;cpu_support:bool=True;supported_model_formats:tuple[str,...]=();state:RuntimeState=RuntimeState.NOT_INSTALLED;health:str="unknown";concurrency:int=1;owned_process:bool=False;limitations:tuple[str,...]=();warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class InferenceEndpoint:
 endpoint_id:str;provider_id:str;base_url:str;local_or_remote:str;authenticated:bool=False;model_listing_supported:bool=True;chat_supported:bool=True;embeddings_supported:bool=False;health:str="unknown";allowed:bool=False;warnings:tuple[str,...]=()
 def __post_init__(self):
  p=urlsplit(self.base_url)
  if p.username or p.password:raise ValueError("credential_in_model_endpoint")
  if self.local_or_remote=="local" and (p.hostname or "").lower() not in {"localhost","127.0.0.1","::1"}:raise ValueError("unsafe_local_model_bind")
  if self.local_or_remote=="remote" and p.scheme!="https":raise ValueError("remote_model_endpoint_requires_https")
@dataclass(frozen=True,slots=True)
class HardwareSnapshot:
 os_name:str;architecture:str;logical_cores:int;ram_class:str="unknown";gpu_available:bool=False;gpu_vendor:str="unknown";vram_class:str="unknown";cuda_available:bool=False;driver_state:str="unknown";disk_class:str="unknown";warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class InferenceResourcePlan:
 profile_id:str;compatibility:str;ram_requirement:str;vram_requirement:str;disk_requirement:str;quantization_recommendation:str;offload_possible:bool;concurrency_recommendation:int;context_recommendation:int;warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class AdvancedRoute:
 request_id:str;status:str;profile_id:str="";provider_id:str="";runtime_id:str="";local:bool=True;reason:str="";fallbacks:tuple[str,...]=();warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class InferenceResult:
 request_id:str;status:str;output:str="";provider_id:str="";model_id:str="";latency_ms:int=0;fallback_used:bool=False;error:str="";warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class RuntimePolicy:
 enabled:bool=True;default_policy:RouteMode=RouteMode.LOCAL_PREFERRED;prefer_local:bool=True;allow_remote:bool=False;allow_paid:bool=False;allow_auto_start:bool=False;allow_auto_download:bool=False;max_concurrent:int=2;default_timeout_seconds:int=60;health_cache_seconds:int=60;max_fallbacks:int=2;resource_reserve_ratio:float=.2;save_history:bool=True;redact_sensitive_values:bool=True

class RuntimeAdapter(Protocol):
 def health(self)->bool:...
 def models(self)->tuple[str,...]:...
 def infer(self,model_id:str,prompt:str,timeout:int)->str:...

class CircuitBreaker:
 def __init__(self,threshold=3,cooldown=30,clock=time.monotonic):self.threshold=threshold;self.cooldown=cooldown;self.clock=clock;self.failures=0;self.opened=0.;self.state=CircuitState.CLOSED
 def allow(self):
  if self.state is CircuitState.OPEN and self.clock()-self.opened>=self.cooldown:self.state=CircuitState.HALF_OPEN
  return self.state is not CircuitState.OPEN
 def success(self):self.failures=0;self.state=CircuitState.CLOSED
 def failure(self,category="provider"):
  if category in {"policy","user","validation"}:return
  self.failures+=1
  if self.failures>=self.threshold:self.state=CircuitState.OPEN;self.opened=self.clock()

class AdvancedModelRuntime:
 def __init__(self,*,policy=None,hardware=None,adapters=None,provider_registry=None):
  self.policy=policy or RuntimePolicy();self.hardware=hardware or self.discover_hardware();self.adapters=adapters or {};self.provider_registry=provider_registry;self.runtimes=self._runtimes();self.profiles=self._profiles();self.endpoints={};self.circuits={k:CircuitBreaker() for k in self.runtimes};self.history=deque(maxlen=100);self.queue=deque(maxlen=20);self.cancelled=set()
 @staticmethod
 def discover_hardware():
  cores=__import__('os').cpu_count() or 0;return HardwareSnapshot(platform.system()[:30],platform.machine()[:30],cores,warnings=("GPU, VRAM, CUDA, driver, RAM, and disk remain unknown unless supplied by an approved detector.",))
 def _runtimes(self):
  found=lambda *names:any(shutil.which(x) for x in names)
  specs=(("ollama",RuntimeType.OLLAMA,"Ollama",found("ollama"),("gguf","ollama")),("vllm",RuntimeType.VLLM,"vLLM",found("vllm"),("huggingface",)),("llama_cpp",RuntimeType.LLAMA_CPP,"llama.cpp",found("llama-cli","llama-server"),("gguf",)),("nvidia_nim",RuntimeType.NVIDIA_NIM,"NVIDIA NIM",False,("nim",)),("openai_compatible",RuntimeType.OPENAI_COMPATIBLE,"OpenAI-compatible",False,("endpoint",)))
  return {i:InferenceRuntime(i,t,n,installed=f,executable_available=f,state=RuntimeState.INSTALLED if f else RuntimeState.NOT_INSTALLED,supported_model_formats=formats,limitations=(("No automatic start, install, container pull, or model download.",))) for i,t,n,f,formats in specs}
 def _profiles(self):
  return {"nemotron_ultra":ModelProfile("nemotron_ultra","Nemotron Ultra logical profile","nemotron","ultra",("nvidia_nim","vllm","openai_compatible"),("nvidia_nim","vllm","openai_compatible"),True,True,capabilities=("reasoning","research","long_context"),reasoning=True,research=True,long_context=True,cost_class="unknown",privacy_class="route_dependent",limitations=("Alias is unresolved until an actual configured model ID is verified.",)),"nemotron_super":ModelProfile("nemotron_super","Nemotron Super logical profile","nemotron","super",("nvidia_nim","vllm","openai_compatible"),("nvidia_nim","vllm","openai_compatible"),True,True,capabilities=("reasoning","coding","research"),reasoning=True,coding=True,research=True,cost_class="unknown",privacy_class="route_dependent",limitations=("Alias is unresolved until an actual configured model ID is verified.",)),"ollama_local":ModelProfile("ollama_local","Configured Ollama model","ollama",provider_ids=("ollama",),runtime_ids=("ollama",),capabilities=("chat","reasoning","coding","research"),readiness="detected" if self.runtimes["ollama"].installed else "unavailable",artifact_state=ArtifactState.KNOWN if self.runtimes["ollama"].installed else ArtifactState.UNKNOWN)}
 def status(self):return {"implemented":True,"ollama":self.runtimes["ollama"].state.value,"vllm":self.runtimes["vllm"].state.value,"llama_cpp":self.runtimes["llama_cpp"].state.value,"nim":"not_configured","nemotron_ultra":"unresolved","nemotron_super":"unresolved","local_first":True,"remote":self.policy.allow_remote,"paid":False,"auto_start":False,"auto_download":False}
 def add_endpoint(self,e):self.endpoints[e.endpoint_id]=e
 def enqueue(self,prompt,profile_id="ollama_local"):
  request_id=new_id();self.queue.append({"request_id":request_id,"profile_id":profile_id,"status":"queued","prompt_preview":bounded(prompt,80)});return request_id
 def cancel(self,request_id):
  self.cancelled.add(request_id)
  for item in self.queue:
   if item["request_id"]==request_id:item["status"]="cancelled";return True
  return False
 def resource_plan(self,profile_id):
  p=self.profiles.get(profile_id);return InferenceResourcePlan(profile_id,"unknown" if not p else "runtime_missing" if not any(self.runtimes[x].installed for x in p.runtime_ids) else "likely_compatible",p.memory_requirements if p else "unknown","unknown","unknown","Use a verified quantization fitting conservative reserve margins.",True,1,min(p.context_window or 4096,8192) if p else 4096,("No exact resource guarantee is made.",))
 def route(self,request,required=(),mode=None,specific="",allow_remote=None,context_tokens=0):
  mode=mode or self.policy.default_policy;remote=self.policy.allow_remote if allow_remote is None else allow_remote
  lowered=request.lower()
  if contains_secret(request) or any(x in lowered for x in ("api key=","api_key=","access token=","password=","secret=")):return AdvancedRoute(new_id(),"blocked",reason="secret_or_credential_input_blocked")
  key=specific or ("nemotron_ultra" if "nemotron ultra" in request.lower() else "nemotron_super" if "nemotron super" in request.lower() else "ollama_local")
  profile=self.profiles.get(key)
  if not profile:return AdvancedRoute(new_id(),"unavailable",reason="unknown_model_profile")
  if required and not set(required).issubset(profile.capabilities):return AdvancedRoute(new_id(),"unavailable",key,reason="capability_mismatch")
  if context_tokens and profile.context_window and context_tokens>profile.context_window:return AdvancedRoute(new_id(),"needs_context_reduction",key,reason="context_window_exceeded")
  candidates=[]
  for rid in profile.runtime_ids:
   rt=self.runtimes[rid];endpoint=next((e for e in self.endpoints.values() if e.provider_id==rid and e.allowed),None);local=rt.local_or_remote=="local" and (not endpoint or endpoint.local_or_remote=="local")
   if not local and not remote:continue
   if rt.installed or endpoint:candidates.append((rid,local))
  if not candidates:return AdvancedRoute(new_id(),"unavailable",key,reason="no configured compatible runtime",fallbacks=("ollama_local",) if key!="ollama_local" else ())
  rid,local=candidates[0];return AdvancedRoute(new_id(),"ready",key,rid,rid,local,"Selected configured healthy route under local-first policy.",tuple(x[0] for x in candidates[1:self.policy.max_fallbacks+1]))
 def infer(self,prompt,*,profile_id="ollama_local",required=(),timeout=None,structured=False):
  route=self.route(prompt,required,specific=profile_id)
  if route.status!="ready":return InferenceResult(route.request_id,route.status,error=route.reason)
  order=(route.runtime_id,)+route.fallbacks
  for index,rid in enumerate(order[:self.policy.max_fallbacks+1]):
   adapter=self.adapters.get(rid);circuit=self.circuits[rid]
   if not adapter or not circuit.allow():continue
   started=time.monotonic()
   try:
    output=bounded(adapter.infer(profile_id,prompt,timeout or self.policy.default_timeout_seconds),8000)
    if structured:
     try:json.loads(output)
     except (TypeError,ValueError):circuit.failure("validation");return InferenceResult(route.request_id,"failed",error="invalid_structured_output")
    circuit.success();result=InferenceResult(route.request_id,"completed",output,rid,profile_id,int((time.monotonic()-started)*1000),index>0,warnings=("Model output cannot execute tools or change policy.",));self.history.append({"request_id":route.request_id,"provider":rid,"status":"completed","fallback":str(index>0).lower()});return result
   except TimeoutError:circuit.failure("timeout")
   except Exception:circuit.failure("provider")
  result=InferenceResult(route.request_id,"failed",error="all_routes_failed");self.history.append({"request_id":route.request_id,"status":"failed","error":"all_routes_failed"});return result
 def lifecycle_plan(self,action,target):return f"{action} plan for {target}: approval_required=yes broker_required=yes auto_start=no auto_download=no executed=no"

def render_runtime_command(command,args,r):
 op=command.split(" ",1)[1];target=" ".join(args).strip()
 if op=="runtime-status":return "Model runtime: "+" ".join(f"{k}={str(v).lower() if isinstance(v,bool) else v}" for k,v in r.status().items())
 if op=="runtimes":return "Model runtimes: "+", ".join(f"{x.runtime_id}:{x.state.value}" for x in r.runtimes.values())
 if op in {"runtime-show","runtime-health"}:
  x=r.runtimes.get(target);return "Model runtime unavailable." if not x else f"Model runtime {x.runtime_id}: state={x.state.value} installed={str(x.installed).lower()} running={str(x.running).lower()} health={x.health} endpoint={'configured' if x.endpoint else 'none'}"
 if op=="profiles":return "Model profiles: "+", ".join(f"{x.model_id}:{x.readiness}" for x in r.profiles.values())
 if op in {"profile-show","alias-show"}:
  x=r.profiles.get(target);return "Model profile unavailable." if not x else f"Model profile {x.model_id}: family={x.family} ready={str(x.readiness=='ready').lower()} artifact={x.artifact_state.value} providers={','.join(x.provider_ids) or 'none'}"
 if op=="aliases":return "Model aliases: nemotron_ultra:unresolved, nemotron_super:unresolved"
 if op=="hardware":
  h=r.hardware;return f"Model hardware: os={h.os_name} arch={h.architecture} cores={h.logical_cores} ram={h.ram_class} gpu={'available' if h.gpu_available else 'unknown'} vram={h.vram_class} cuda={'available' if h.cuda_available else 'unknown'}"
 if op=="compatibility":return f"Model compatibility: {r.resource_plan(target).compatibility}"
 if op=="resource-plan":
  p=r.resource_plan(target);return f"Model resource plan: profile={p.profile_id} compatibility={p.compatibility} ram={p.ram_requirement} vram={p.vram_requirement} concurrency={p.concurrency_recommendation} context={p.context_recommendation}"
 if op in {"route","route-explain"}:
  x=r.route(target);return f"Advanced model route: status={x.status} profile={x.profile_id or 'none'} runtime={x.runtime_id or 'none'} local={str(x.local).lower()} reason={x.reason} fallbacks={','.join(x.fallbacks) or 'none'}"
 if op in {"start-plan","start","stop","download-plan"}:return "Model "+r.lifecycle_plan(op,target)
 if op=="download-status":return "Model download: disabled; no artifact download is active."
 if op=="fallback-status":return f"Model fallback: max={r.policy.max_fallbacks} local_first=yes remote_allowed={str(r.policy.allow_remote).lower()}"
 if op=="circuit-status":return "Model circuits: "+", ".join(f"{k}:{v.state.value}" for k,v in r.circuits.items())
 if op=="provider-health":return "Model provider health: configured adapter required; no expensive inference probe performed."
 return "model runtime-status"
