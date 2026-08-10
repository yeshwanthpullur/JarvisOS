"""Typed local-only Phase 3 evaluation and observability models."""
from dataclasses import dataclass,field
from jarvis.foundation_common import new_id,now
@dataclass(frozen=True,slots=True)
class EvaluationCase:
 case_id:str;category:str;input_text:str;expected_route:str="";expected_risk:str="";expected_status:str="";expected_blocked:bool=False;notes:str=""
@dataclass(frozen=True,slots=True)
class EvaluationResult:
 case_id:str;passed:bool;actual_route:str="";actual_risk:str="";actual_status:str="";actual_blocked:bool=False;warnings:tuple[str,...]=();error:str|None=None
@dataclass(frozen=True,slots=True)
class EvaluationSuiteResult:
 suite_name:str;total_cases:int;passed:int;failed:int;skipped:int=0;warnings:tuple[str,...]=();suite_id:str=field(default_factory=new_id);created_at:str=field(default_factory=now)
@dataclass(frozen=True,slots=True)
class AgentHealthCheck:
 agent_id:str;status:str;expected_status:str;capabilities_count:int;unavailable_reason:str="";warnings:tuple[str,...]=();passed:bool=True
@dataclass(frozen=True,slots=True)
class CapabilityTruthfulnessCheck:
 check_id:str;target_type:str;target_id:str;claimed_capability:str;expected_availability:bool;actual_availability:bool;passed:bool;warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class ObservabilitySnapshot:
 agents_summary:dict[str,object];skills_summary:dict[str,object];model_summary:dict[str,object];adapter_summary:dict[str,object];safety_summary:dict[str,object];limitations_summary:dict[str,object];readiness_summary:dict[str,object];warnings:tuple[str,...]=();snapshot_id:str=field(default_factory=new_id);created_at:str=field(default_factory=now)
@dataclass(frozen=True,slots=True)
class HardeningResult:
 request_id:str;status:str;evaluation_summary:EvaluationSuiteResult|None=None;health_summary:tuple[AgentHealthCheck,...]=();truthfulness_summary:tuple[CapabilityTruthfulnessCheck,...]=();observability_snapshot:ObservabilitySnapshot|None=None;warnings:tuple[str,...]=();error:str|None=None
