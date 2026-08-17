"""Provider-neutral, metadata-only production reliability runtime."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from collections import deque
import os,re
from typing import Any
from uuid import uuid4

def now()->str:return datetime.now(timezone.utc).isoformat()
def ident(prefix:str)->str:return f"{prefix}-{uuid4().hex[:12]}"
SECRET=re.compile(r"(?i)(token|secret|password|api[_-]?key|authorization)\s*[:=]\s*\S+")
def safe(value:object,limit:int=500)->str:
 text=SECRET.sub(r"\1=[REDACTED]",str(value)).replace("\\","/")
 if re.search(r"[A-Za-z]:/Users/",text):text="[PRIVATE_PATH]"
 return text[:limit]

class HealthState(StrEnum):
 UNKNOWN="unknown";INITIALIZING="initializing";READY="ready";DEGRADED="degraded";RECOVERING="recovering";PAUSED="paused";BLOCKED="blocked";OFFLINE="offline";FAILED="failed"
class HealthSeverity(StrEnum):INFORMATIONAL="informational";WARNING="warning";DEGRADED="degraded";CRITICAL="critical";FATAL="fatal"
class NodeState(StrEnum):REGISTERING="registering";READY="ready";DEGRADED="degraded";MAINTENANCE="maintenance";RECOVERING="recovering";OFFLINE="offline";FAILED="failed";REMOVED="removed"
class CircuitState(StrEnum):CLOSED="closed";OPEN="open";HALF_OPEN="half_open";RECOVERING="recovering"

@dataclass(frozen=True,slots=True)
class ReliabilityLimits:
 monitor_interval_seconds:int=30;max_retry_attempts:int=2;max_health_history:int=200;max_alert_history:int=100;max_metric_history:int=500;max_parallel_health_checks:int=4;failure_threshold:int=3;recovery_success_threshold:int=2
 def __post_init__(self):
  if any(v<1 for v in asdict(self).values()) or self.max_retry_attempts>5:raise ValueError("invalid_reliability_limits")

@dataclass(frozen=True,slots=True)
class RuntimeHealth:
 runtime_id:str;component:str;state:HealthState;health_score:float;availability:bool;last_check:str=field(default_factory=now);last_transition:str=field(default_factory=now);dependency_health:tuple[str,...]=();resource_health:tuple[str,...]=();provider_health:tuple[str,...]=();warnings:tuple[str,...]=();errors:tuple[str,...]=()
 def __post_init__(self):
  if not 0<=self.health_score<=1:raise ValueError("health_score_out_of_range")
  object.__setattr__(self,"component",safe(self.component,100));object.__setattr__(self,"warnings",tuple(safe(x,200) for x in self.warnings[:20]));object.__setattr__(self,"errors",tuple(safe(x,200) for x in self.errors[:20]))

@dataclass(frozen=True,slots=True)
class RuntimeNode:
 node_id:str;node_type:str;display_name:str;runtime_version:str;capabilities:tuple[str,...];registered_components:tuple[str,...];registered_agents:tuple[str,...]=();registered_models:tuple[str,...]=();resource_summary:tuple[str,...]=();health:HealthState=HealthState.UNKNOWN;availability:bool=False;last_heartbeat:str=field(default_factory=now);warnings:tuple[str,...]=()

@dataclass(frozen=True,slots=True)
class ServiceRecord:
 service_id:str;version:str;capabilities:tuple[str,...];dependencies:tuple[str,...];health:HealthState=HealthState.UNKNOWN;availability:bool=False

@dataclass(slots=True)
class CircuitBreaker:
 component:str;failure_threshold:int=3;recovery_success_threshold:int=2;state:CircuitState=CircuitState.CLOSED;failure_count:int=0;success_count:int=0;last_failure:str|None=None;last_success:str|None=None;recovery_timer_seconds:int=30;breaker_id:str=field(default_factory=lambda:ident("breaker"))
 def failure(self)->CircuitState:
  self.failure_count+=1;self.success_count=0;self.last_failure=now()
  if self.failure_count>=self.failure_threshold:self.state=CircuitState.OPEN
  return self.state
 def probe(self)->CircuitState:
  if self.state is CircuitState.OPEN:self.state=CircuitState.HALF_OPEN
  return self.state
 def success(self)->CircuitState:
  self.success_count+=1;self.last_success=now()
  if self.state in {CircuitState.HALF_OPEN,CircuitState.RECOVERING} and self.success_count>=self.recovery_success_threshold:self.state=CircuitState.CLOSED;self.failure_count=0
  return self.state

@dataclass(frozen=True,slots=True)
class RuntimeMetric:
 component:str;metric_name:str;value:float;category:str="runtime";timestamp:str=field(default_factory=now);collection_interval:int=30;warnings:tuple[str,...]=();metric_id:str=field(default_factory=lambda:ident("metric"))

@dataclass(frozen=True,slots=True)
class Alert:
 severity:HealthSeverity;component:str;summary:str;recommended_action:str;timestamp:str=field(default_factory=now);alert_id:str=field(default_factory=lambda:ident("alert"))

@dataclass(frozen=True,slots=True)
class DiagnosticReport:
 runtime_id:str;component:str;health_summary:str;dependency_summary:tuple[str,...];provider_summary:tuple[str,...];resource_summary:tuple[str,...];warnings:tuple[str,...];errors:tuple[str,...];recommendations:tuple[str,...];root_cause:str="unknown";correlation_id:str=field(default_factory=lambda:ident("corr"));created_at:str=field(default_factory=now);report_id:str=field(default_factory=lambda:ident("diag"))

@dataclass(frozen=True,slots=True)
class RecoveryPlan:
 component:str;level:int;actions:tuple[str,...];automatic_actions:tuple[str,...];privileged_actions:tuple[str,...];requires_policy:bool;requires_approval:bool;requires_broker:bool;status:str="planned";plan_id:str=field(default_factory=lambda:ident("recovery"))

class ReliabilityRuntime:
 """Aggregates health without gaining recovery or execution authority."""
 def __init__(self,limits:ReliabilityLimits|None=None):
  self.limits=limits or ReliabilityLimits();self.health:dict[str,RuntimeHealth]={};self.nodes:dict[str,RuntimeNode]={};self.services:dict[str,ServiceRecord]={};self.dependencies:dict[str,set[str]]={};self.breakers:dict[str,CircuitBreaker]={};self.metrics=deque(maxlen=self.limits.max_metric_history);self.alerts=deque(maxlen=self.limits.max_alert_history);self.history=deque(maxlen=self.limits.max_health_history);self.recoveries=deque(maxlen=self.limits.max_health_history);self.events=deque(maxlen=self.limits.max_health_history)
  self._last_transition_ts: str | None = None
 def _transition_timestamp(self) -> str:
  timestamp=now()
  if self._last_transition_ts is not None and timestamp<=self._last_transition_ts:
   previous=datetime.fromisoformat(self._last_transition_ts)
   timestamp=(previous+timedelta(microseconds=1)).isoformat()
  self._last_transition_ts=timestamp
  return timestamp
 def register_service(self,record:ServiceRecord)->None:
  if record.service_id in self.services:raise ValueError("duplicate_reliability_service")
  self.services[record.service_id]=record;self.dependencies[record.service_id]=set(record.dependencies)
 def validate_dependencies(self)->bool:
  visiting:set[str]=set();visited:set[str]=set()
  def visit(node:str):
   if node in visiting:raise ValueError("reliability_dependency_cycle")
   if node in visited:return
   visiting.add(node)
   for dep in self.dependencies.get(node,set()):
    if dep not in self.services:raise ValueError("unknown_reliability_dependency")
    visit(dep)
   visiting.remove(node);visited.add(node)
  for node in self.services:visit(node)
  return True
 def record_health(self,component:str,state:HealthState,score:float,*,warnings:tuple[str,...]=(),errors:tuple[str,...]=())->RuntimeHealth:
  previous=self.health.get(component);dependencies=tuple(f"{dep}:{self.health.get(dep,RuntimeHealth('none',dep,HealthState.UNKNOWN,0,False)).state.value}" for dep in sorted(self.dependencies.get(component,set())))
  item=RuntimeHealth(ident("runtime"),component,state,score,state is HealthState.READY,dependency_health=dependencies,warnings=warnings,errors=errors,last_transition=previous.last_transition if previous and previous.state is state else self._transition_timestamp())
  self.health[component]=item;self.history.append(item);self.events.append((now(),safe(component,100),"health_transition",state.value))
  breaker=self.breakers.setdefault(component,CircuitBreaker(component,self.limits.failure_threshold,self.limits.recovery_success_threshold))
  if state in {HealthState.FAILED,HealthState.OFFLINE}:breaker.failure()
  elif state is HealthState.READY:breaker.success()
  if state in {HealthState.DEGRADED,HealthState.FAILED,HealthState.OFFLINE}:self._alert(component,state)
  return item
 def aggregate(self)->RuntimeHealth:
  if not self.health:return RuntimeHealth("local","jarvis_runtime",HealthState.UNKNOWN,0,False,warnings=("No component health has been recorded.",))
  states=[x.state for x in self.health.values()];score=sum(x.health_score for x in self.health.values())/len(self.health)
  state=HealthState.FAILED if HealthState.FAILED in states else HealthState.DEGRADED if any(x in states for x in (HealthState.DEGRADED,HealthState.OFFLINE,HealthState.BLOCKED)) else HealthState.READY
  return RuntimeHealth("local","jarvis_runtime",state,score,state is HealthState.READY,dependency_health=tuple(f"{k}:{v.state.value}" for k,v in sorted(self.health.items())))
 def resource_snapshot(self,*,cpu_percent:float|None=None,memory_percent:float|None=None,queue_depth:int=0)->dict[str,Any]:
  cpu=float(cpu_percent if cpu_percent is not None else 0);memory=float(memory_percent if memory_percent is not None else 0);queue=max(0,queue_depth);level="exhausted" if max(cpu,memory)>=98 else "critical" if max(cpu,memory)>=90 else "warning" if max(cpu,memory)>=75 or queue>=20 else "ready"
  for name,value in (("cpu_percent",cpu),("memory_percent",memory),("queue_depth",float(queue))):self.metrics.append(RuntimeMetric("resources",name,value,"resource"))
  return {"state":level,"cpu_percent":cpu,"memory_percent":memory,"queue_depth":queue,"load_shedding":"plan_only" if level!="ready" else "not_required"}
 def queue_health(self,pending:int,running:int,waiting:int,failed:int)->dict[str,Any]:
  total=sum(max(0,x) for x in (pending,running,waiting,failed));state="degraded" if failed or pending>20 else "ready";return {"state":state,"pending":pending,"running":running,"waiting":waiting,"failed":failed,"total":total}
 def diagnostic(self,component:str)->DiagnosticReport:
  health=self.aggregate() if component=="jarvis_runtime" else self.health.get(component);root="configuration" if health and any("config" in x.lower() for x in health.errors) else "provider" if "provider" in component else "dependency" if health and health.dependency_health and health.state is not HealthState.READY else "healthy" if health and health.state is HealthState.READY else "unexpected"
  return DiagnosticReport("local",safe(component,100),health.state.value if health else "unknown",health.dependency_health if health else (),health.provider_health if health else (),health.resource_health if health else (),health.warnings if health else ("Component health unavailable.",),health.errors if health else (),self._recommendations(health),root)
 def recovery_plan(self,component:str)->RecoveryPlan:
  health=self.aggregate() if component=="jarvis_runtime" else self.health.get(component);state=health.state if health else HealthState.UNKNOWN;level=1 if state in {HealthState.UNKNOWN,HealthState.DEGRADED} else 2 if state in {HealthState.OFFLINE,HealthState.FAILED} else 0
  automatic=("refresh_health_cache","refresh_internal_metadata") if level else ();privileged=("component_restart","configuration_change") if level>=2 else ()
  plan=RecoveryPlan(component,level,automatic,automatic,privileged,bool(privileged),bool(privileged),bool(privileged));self.recoveries.append(plan);return plan
 def fault_isolation(self,component:str)->dict[str,Any]:
  dependents=tuple(sorted(name for name,deps in self.dependencies.items() if component in deps));return {"component":safe(component,100),"isolated":True,"affected_dependents":dependents,"authority_changed":False}
 def capacity(self)->dict[str,Any]:return {"recommended_health_checks":self.limits.max_parallel_health_checks,"workflow_parallelism":"use workflow limits","provider_capacity":"provider-owned","allocation_performed":False}
 def dashboard(self)->dict[str,Any]:
  overall=self.aggregate();return {"state":overall.state.value,"score":round(overall.health_score,3),"components":len(self.health),"ready":sum(x.state is HealthState.READY for x in self.health.values()),"degraded":sum(x.state is HealthState.DEGRADED for x in self.health.values()),"alerts":len(self.alerts),"open_breakers":sum(x.state is CircuitState.OPEN for x in self.breakers.values()),"privileged_recovery":False}
 def verify(self)->dict[str,Any]:
  try:dependencies=self.validate_dependencies()
  except ValueError as exc:return {"valid":False,"error":safe(exc),"authority":"informational_only"}
  return {"valid":dependencies,"components":len(self.health),"services":len(self.services),"bounded_history":True,"authority":"informational_only"}
 def _alert(self,component:str,state:HealthState):
  severity=HealthSeverity.CRITICAL if state in {HealthState.FAILED,HealthState.OFFLINE} else HealthSeverity.WARNING;self.alerts.append(Alert(severity,component,f"{component} is {state.value}.","Inspect diagnostics and create a governed recovery plan."))
 def _recommendations(self,health:RuntimeHealth|None)->tuple[str,...]:
  if health is None:return ("Register or refresh component health metadata.",)
  if health.state is HealthState.READY:return ("No recovery action required.",)
  return ("Inspect bounded dependency and resource metadata.","Use recovery-plan; privileged actions still require policy, approval, and Broker validation.")

def build_default_reliability_runtime()->ReliabilityRuntime:
 r=ReliabilityRuntime();services=(ServiceRecord("executive","1",("coordination",),()),ServiceRecord("prime","1",("routing",),("executive",)),ServiceRecord("workflow","1",("checkpoint","recovery"),("prime",)),ServiceRecord("providers","1",("model_route",),("executive",)),ServiceRecord("research","1",("evidence",),("prime","providers")),ServiceRecord("knowledge","1",("retrieval",),("executive",)),ServiceRecord("browser","1",("read_only",),("executive",)))
 for item in services:r.register_service(item);r.record_health(item.service_id,HealthState.READY,1.0)
 return r
