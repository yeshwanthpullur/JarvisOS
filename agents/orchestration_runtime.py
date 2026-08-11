"""Unified bounded coordination runtime; coordination never grants authority."""
from __future__ import annotations
from dataclasses import dataclass,field,replace
from datetime import UTC,datetime
from enum import StrEnum
import re
from uuid import uuid4

def now():return datetime.now(UTC).isoformat()
SECRET=re.compile(r"(?i)(api[_-]?key|access[_-]?token|authorization|password|secret|cookie)\s*[:=]\s*\S+")
def safe(v:object,n:int=1000)->str:
 s=SECRET.sub("[REDACTED]"," ".join(str(v or "").split()));return s if len(s)<=n else s[:n-3]+"..."
class SessionState(StrEnum):
 CREATED="created";PLANNING="planning";WAITING_FOR_APPROVAL="waiting_for_approval";DELEGATING="delegating";RUNNING="running";WAITING="waiting";COLLECTING="collecting";MERGING="merging";COMPLETED="completed";CANCELLED="cancelled";TIMED_OUT="timed_out";FAILED="failed";BLOCKED="blocked";PARTIAL_SUCCESS="partial_success"
class NodeStatus(StrEnum): PENDING="pending";READY="ready";RUNNING="running";COMPLETED="completed";BLOCKED="blocked";FAILED="failed";CANCELLED="cancelled";TIMED_OUT="timed_out"
class DependencyType(StrEnum): HARD="hard";SOFT="soft";OPTIONAL="optional";PARALLEL="parallel";FALLBACK="fallback"
class MessageType(StrEnum): REQUEST="request";RESPONSE="response";PROGRESS="progress";STATUS="status";WARNING="warning";ERROR="error";DEPENDENCY_READY="dependency_ready";APPROVAL_REQUIRED="approval_required";APPROVAL_GRANTED="approval_granted";APPROVAL_DENIED="approval_denied";CANCEL="cancel";TIMEOUT="timeout";RETRY="retry";RESOURCE_UPDATE="resource_update";COMPLETION="completion"
class Priority(StrEnum): CRITICAL="critical";HIGH="high";NORMAL="normal";LOW="low";BACKGROUND="background"
@dataclass(frozen=True,slots=True)
class ExecutionBudget:
 max_runtime:int=180;max_parallel_tasks:int=2;max_provider_calls:int=8;max_browser_reads:int=6;max_model_calls:int=6;max_tokens:int=20000;max_memory_usage:int=64_000_000;max_disk_usage:int=10_000_000;max_network_requests:int=10
 def narrowed(self,**values):
  current=self.__dict__ if hasattr(self,"__dict__") else {k:getattr(self,k) for k in self.__slots__}
  if any(values.get(k,current[k])>current[k] for k in values):raise ValueError("subtask_budget_cannot_expand")
  return replace(self,**values)
@dataclass(slots=True)
class BudgetUsage:
 provider_calls:int=0;browser_reads:int=0;model_calls:int=0;tokens:int=0;network_requests:int=0
 def consume(self,b:ExecutionBudget,**v):
  for k,x in v.items():setattr(self,k,getattr(self,k)+max(0,int(x)))
  return self.provider_calls<=b.max_provider_calls and self.browser_reads<=b.max_browser_reads and self.model_calls<=b.max_model_calls and self.tokens<=b.max_tokens and self.network_requests<=b.max_network_requests
@dataclass(frozen=True,slots=True)
class AgentTaskNode:
 node_id:str;owner_agent:str;task_type:str;dependencies:tuple[str,...]=();dependency_type:DependencyType=DependencyType.HARD;input_refs:tuple[str,...]=();output_refs:tuple[str,...]=();privacy_scope:tuple[str,...]=("public",);policy_id:str="execution-policy";policy_version:str="1";effective_permissions:tuple[str,...]=();execution_class:str="plan_only";status:NodeStatus=NodeStatus.PENDING;retry_count:int=0;max_retries:int=1;warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class AgentMessage:
 session_id:str;sender_agent:str;receiver_agent:str;message_type:MessageType;payload_reference:str;privacy_scope:tuple[str,...];trust_class:str="untrusted";priority:Priority=Priority.NORMAL;correlation_id:str="";message_id:str=field(default_factory=lambda:str(uuid4()));created_at:str=field(default_factory=now);expires_at:str|None=None;warnings:tuple[str,...]=()
 def __post_init__(self):
  if SECRET.search(self.payload_reference) or len(self.payload_reference)>500:raise ValueError("unsafe_orchestration_message")
@dataclass(frozen=True,slots=True)
class ContextVersion:
 version:int;segments:tuple[tuple[str,tuple[tuple[str,str],...]],...];author:str;reason:str;created_at:str=field(default_factory=now)
@dataclass(slots=True)
class SharedExecutionContext:
 context_id:str;session_id:str;privacy_scope:tuple[str,...];versions:list[ContextVersion]=field(default_factory=list);max_versions:int=10
 def update(self,author:str,reason:str,segments:dict[str,dict[str,object]]):
  allowed={"conversation","research","knowledge","documents","browser","github","mcp","plugins","model_routing","provider_metadata","execution_metadata"}
  cleaned=[]
  for name,values in segments.items():
   if name not in allowed:continue
   sensitive={"api_key","access_token","authorization","password","secret","cookie","credential","private_header"}
   cleaned.append((name,tuple(sorted((safe(k,80),safe(v,500)) for k,v in values.items() if str(k).lower() not in sensitive and not SECRET.search(f"{k}={v}")))))
  version=ContextVersion(len(self.versions)+1,tuple(cleaned),author,safe(reason,200));self.versions=(self.versions+[version])[-self.max_versions:];return version
 def segment(self,name:str):
  if not self.versions:return ()
  return next((v for k,v in self.versions[-1].segments if k==name),())
@dataclass(frozen=True,slots=True)
class AuditEvent:
 event_type:str;session_id:str;node_id:str|None=None;status:str="";correlation_id:str="";created_at:str=field(default_factory=now);warning:str=""
@dataclass(slots=True)
class OrchestrationSession:
 request_id:str;owner:str="prime_agent";initiating_agent:str="prime_agent";execution_mode:str="plan_only";current_state:SessionState=SessionState.CREATED;nodes:dict[str,AgentTaskNode]=field(default_factory=dict);active_agents:tuple[str,...]=();completed_agents:tuple[str,...]=();blocked_agents:tuple[str,...]=();failed_agents:tuple[str,...]=();cancelled_agents:tuple[str,...]=();shared_context_id:str="";resource_budget:ExecutionBudget=field(default_factory=ExecutionBudget);approval_state:str="not_required";session_id:str=field(default_factory=lambda:str(uuid4()));created_at:str=field(default_factory=now);updated_at:str=field(default_factory=now);finished_at:str|None=None;warnings:tuple[str,...]=();errors:tuple[str,...]=()
@dataclass(slots=True)
class MultiAgentOrchestrationRuntime:
 max_sessions:int=25;max_delegation_depth:int=3;max_events:int=200;max_messages:int=100;enable_parallel:bool=True;sessions:dict[str,OrchestrationSession]=field(default_factory=dict);contexts:dict[str,SharedExecutionContext]=field(default_factory=dict);messages:list[AgentMessage]=field(default_factory=list);events:list[AuditEvent]=field(default_factory=list);usage:dict[str,BudgetUsage]=field(default_factory=dict)
 def create(self,request_id:str,nodes:tuple[AgentTaskNode,...],privacy_scope=("public",),owner="prime_agent"):
  if owner!="prime_agent":raise ValueError("orchestration_owner_must_be_prime")
  graph={n.node_id:n for n in nodes};self.validate_graph(graph)
  session=OrchestrationSession(request_id,owner=owner,nodes=graph,current_state=SessionState.PLANNING)
  context=SharedExecutionContext(str(uuid4()),session.session_id,tuple(privacy_scope));session.shared_context_id=context.context_id
  self.sessions[session.session_id]=session;self.contexts[context.context_id]=context;self.usage[session.session_id]=BudgetUsage();self._event("session_created",session);self._trim();return session
 def validate_graph(self,nodes:dict[str,AgentTaskNode]):
  if not nodes or len(nodes)>32:raise ValueError("invalid_orchestration_graph")
  for n in nodes.values():
   if n.owner_agent in {"","orchestrator"} or n.node_id in n.dependencies or any(d not in nodes for d in n.dependencies):raise ValueError("invalid_orchestration_dependency")
  visiting=set();done=set()
  def visit(i):
   if i in visiting:raise ValueError("orchestration_cycle")
   if i in done:return
   visiting.add(i)
   for d in nodes[i].dependencies:visit(d)
   visiting.remove(i);done.add(i)
  for i in nodes:visit(i)
  return True
 def ready_nodes(self,session_id:str):
  s=self.sessions[session_id];completed={i for i,n in s.nodes.items() if n.status is NodeStatus.COMPLETED}
  failed={i for i,n in s.nodes.items() if n.status in {NodeStatus.FAILED,NodeStatus.BLOCKED,NodeStatus.CANCELLED,NodeStatus.TIMED_OUT}}
  out=[]
  for n in s.nodes.values():
   if n.status is not NodeStatus.PENDING:continue
   if n.dependency_type is DependencyType.HARD and any(d in failed for d in n.dependencies):s.nodes[n.node_id]=replace(n,status=NodeStatus.BLOCKED);continue
   if all(d in completed or (n.dependency_type in {DependencyType.SOFT,DependencyType.OPTIONAL,DependencyType.FALLBACK} and d in failed) for d in n.dependencies):out.append(n)
  return tuple(out[:s.resource_budget.max_parallel_tasks if self.enable_parallel else 1])
 def send(self,message:AgentMessage):
  if message.session_id not in self.sessions:raise ValueError("cross_session_message_blocked")
  if message.sender_agent==message.receiver_agent:raise ValueError("self_delegation_blocked")
  self.messages=(self.messages+[message])[-self.max_messages:];self._event("message_routed",self.sessions[message.session_id],correlation=message.correlation_id);return message
 def mark(self,session_id:str,node_id:str,status:NodeStatus,warning=""):
  s=self.sessions[session_id];n=s.nodes[node_id];s.nodes[node_id]=replace(n,status=status,warnings=n.warnings+((safe(warning,200),) if warning else ()))
  if status is NodeStatus.COMPLETED and all(x.status is NodeStatus.COMPLETED for x in s.nodes.values()):s.current_state=SessionState.COMPLETED;s.finished_at=now()
  elif status in {NodeStatus.FAILED,NodeStatus.TIMED_OUT}:
   s.current_state=SessionState.PARTIAL_SUCCESS if any(x.status is NodeStatus.COMPLETED for x in s.nodes.values()) else SessionState.FAILED
  self._event("node_state",s,node_id,status.value,warning);return s.nodes[node_id]
 def consume(self,session_id:str,**usage):
  ok=self.usage[session_id].consume(self.sessions[session_id].resource_budget,**usage)
  if not ok:self.sessions[session_id].current_state=SessionState.PARTIAL_SUCCESS;self.sessions[session_id].warnings+=("resource_budget_exhausted",);self._event("budget_exhausted",self.sessions[session_id])
  return ok
 def cancel(self,session_id:str):
  s=self.sessions.get(session_id)
  if not s or s.current_state in {SessionState.COMPLETED,SessionState.CANCELLED}:return False
  s.current_state=SessionState.CANCELLED;s.finished_at=now();s.nodes={k:replace(v,status=NodeStatus.CANCELLED) if v.status in {NodeStatus.PENDING,NodeStatus.RUNNING,NodeStatus.READY} else v for k,v in s.nodes.items()};self._event("cancelled",s);return True
 def _event(self,t,s,node=None,status="",warning="",correlation=""):
  self.events=(self.events+[AuditEvent(t,s.session_id,node,status,correlation,warning=safe(warning,200))])[-self.max_events:]
 def _trim(self):
  while len(self.sessions)>self.max_sessions:self.sessions.pop(next(iter(self.sessions)))
 def metrics(self):
  states=[s.current_state for s in self.sessions.values()];return {"active":sum(x not in {SessionState.COMPLETED,SessionState.CANCELLED,SessionState.FAILED} for x in states),"completed":states.count(SessionState.COMPLETED),"failed":states.count(SessionState.FAILED),"cancelled":states.count(SessionState.CANCELLED),"partial_success":states.count(SessionState.PARTIAL_SUCCESS),"events":len(self.events),"messages":len(self.messages)}
 def status(self):return {"status":"implemented","authority":"coordination_only","parallel":"bounded" if self.enable_parallel else "disabled","sessions":len(self.sessions),"approval_bypass":False,"broker_bypass":False,"credential_storage":False,**self.metrics()}
