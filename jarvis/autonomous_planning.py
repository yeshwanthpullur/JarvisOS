"""Governed autonomous planning without execution authority."""
from __future__ import annotations

import json, logging, re
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4


def now() -> str: return datetime.now(UTC).isoformat()


class PlanningMode(StrEnum):
    OFF="off"; SUGGEST="suggest"; CONFIRM="confirm"; AUTOMATIC_SAFE="automatic-safe"
class PlanStatus(StrEnum):
    DRAFT="draft"; AWAITING_CLARIFICATION="awaiting_clarification"; AWAITING_REVIEW="awaiting_review"; AWAITING_APPROVAL="awaiting_approval"; APPROVED="approved"; READY="ready"; ACTIVE="active"; PAUSED="paused"; PARTIALLY_COMPLETED="partially_completed"; COMPLETED="completed"; FAILED="failed"; BLOCKED="blocked"; CANCELLED="cancelled"; SUPERSEDED="superseded"; INVALID="invalid"
class StepStatus(StrEnum):
    PENDING="pending"; READY="ready"; AWAITING_APPROVAL="awaiting_approval"; RUNNING="running"; COMPLETED="completed"; PARTIALLY_COMPLETED="partially_completed"; FAILED="failed"; BLOCKED="blocked"; SKIPPED="skipped"; CANCELLED="cancelled"; TIMED_OUT="timed_out"


@dataclass(frozen=True, slots=True)
class PlanningLimits:
    maximum_steps:int=12; maximum_milestones:int=5; maximum_alternatives:int=3; maximum_dependencies_per_step:int=4; maximum_plan_depth:int=2; maximum_retries:int=1; maximum_replans:int=3; maximum_concurrent:int=2; maximum_agents:int=3; maximum_tools:int=4; maximum_timeout_seconds:int=90; maximum_versions:int=10; maximum_output_bytes:int=100_000; maximum_assumptions:int=8
@dataclass(frozen=True, slots=True)
class PlanningNeedAssessment:
    requires_plan:bool; reason:str; objective_type:str="general"; complexity:str="simple"; estimated_scope:str="small"; distinct_domains:tuple[str,...]=(); expected_steps:int=1; expected_dependencies:int=0; expected_duration_class:str="short"; expected_cost_class:str="none"; risk_class:str="minimal"; mutation_expected:bool=False; external_action_expected:bool=False; missing_information:tuple[str,...]=(); approval_required:bool=False; confidence:float=.8; recommended_planning_mode:str="none"
@dataclass(frozen=True, slots=True)
class PlanningObjective:
    objective_id:str; parent_request_id:str; user_objective:str; normalized_objective:str; desired_outcome:str; success_criteria:tuple[str,...]; constraints:tuple[str,...]=(); preferences:tuple[str,...]=(); deadlines:tuple[str,...]=(); priority:str="normal"; required_capabilities:tuple[str,...]=(); prohibited_actions:tuple[str,...]=(); safety_requirements:tuple[str,...]=(); approval_requirements:tuple[str,...]=(); related_goal_ids:tuple[str,...]=(); related_task_ids:tuple[str,...]=(); related_workflow_ids:tuple[str,...]=(); context_references:tuple[str,...]=(); evidence_references:tuple[str,...]=(); assumptions:tuple[str,...]=(); unresolved_questions:tuple[str,...]=(); created_at:str=field(default_factory=now); updated_at:str=field(default_factory=now)
@dataclass(frozen=True, slots=True)
class PlanStep:
    step_id:str; plan_id:str; title:str; objective:str; description:str; sequence:int; status:StepStatus=StepStatus.PENDING; dependencies:tuple[str,...]=(); parallel_group:str|None=None; assigned_agent_id:str|None=None; required_capabilities:tuple[str,...]=(); required_tool_ids:tuple[str,...]=(); required_workflow_id:str|None=None; related_task_id:str|None=None; inputs:dict[str,object]=field(default_factory=dict); expected_outputs:tuple[str,...]=(); evidence_requirements:tuple[str,...]=(); permissions:tuple[str,...]=(); approvals:tuple[str,...]=(); risk_class:str="minimal"; timeout:int=60; retry_policy:str="bounded"; idempotency_requirement:bool=False; rollback_guidance:str="No mutation is performed by planning."; completion_criteria:tuple[str,...]=(); failure_behavior:str="block dependants"; optional:bool=False; estimated_duration:str="unknown"; estimated_cost:str="unknown"; created_at:str=field(default_factory=now); updated_at:str=field(default_factory=now)
@dataclass(frozen=True, slots=True)
class PlanValidation:
    valid:bool; errors:tuple[str,...]=(); warnings:tuple[str,...]=(); blocked_reasons:tuple[str,...]=(); required_clarifications:tuple[str,...]=(); required_permissions:tuple[str,...]=(); required_approvals:tuple[str,...]=(); unavailable_dependencies:tuple[str,...]=(); confidence:float=.9
@dataclass(frozen=True, slots=True)
class AutonomousPlan:
    plan_id:str; objective_id:str; parent_request_id:str; title:str; summary:str; status:PlanStatus; planning_mode:str; version:int; milestones:tuple[str,...]; steps:tuple[PlanStep,...]; dependencies:dict[str,tuple[str,...]]; parallel_groups:tuple[tuple[str,...],...]=(); assumptions:tuple[str,...]=(); constraints:tuple[str,...]=(); success_criteria:tuple[str,...]=(); completion_criteria:tuple[str,...]=(); failure_criteria:tuple[str,...]=(); required_agents:tuple[str,...]=(); required_tools:tuple[str,...]=(); required_workflows:tuple[str,...]=(); required_permissions:tuple[str,...]=(); required_approvals:tuple[str,...]=(); provider_policy:str="automatic"; execution_policy:str="advisory"; risk_summary:str="minimal"; estimated_duration:str="unknown"; estimated_cost:str="unknown"; fallback_strategy:str="request review"; rollback_strategy:str="no execution performed"; recovery_strategy:str="revalidate before handoff"; monitoring_strategy:str="authoritative status evidence"; replanning_policy:str="bounded"; cancellation_policy:str="stop planning only"; evidence_requirements:tuple[str,...]=(); validation:PlanValidation|None=None; replanning_count:int=0; created_at:str=field(default_factory=now); updated_at:str=field(default_factory=now)


class AutonomousPlanning:
    def __init__(self, storage_dir:Path|None=None, tool_manager:Any=None, agent_manager:Any=None, logger:logging.Logger|None=None, limits:PlanningLimits|None=None):
        self.storage_dir=storage_dir; self.tool_manager=tool_manager; self.agent_manager=agent_manager; self.logger=logger or logging.getLogger("autonomous_planning"); self.limits=limits or PlanningLimits(); self.mode=PlanningMode.CONFIRM; self.plans:dict[str,AutonomousPlan]={}; self.objectives:dict[str,PlanningObjective]={}; self.initialized=True; self._load()
    def assess(self,text:str)->PlanningNeedAssessment:
        low=text.lower(); markers=("create a plan","plan for","break down","roadmap","implementation, testing","multiple steps","project plan")
        needs=any(x in low for x in markers) or len(text.split())>45
        missing=("target",) if needs and any(x in low for x in ("delete it","send it","pay it")) else ()
        return PlanningNeedAssessment(needs,"complex multi-step objective" if needs else "existing direct path is sufficient",complexity="complex" if needs else "simple",estimated_scope="medium" if needs else "small",distinct_domains=("implementation","testing","documentation") if needs else (),expected_steps=4 if needs else 1,expected_dependencies=3 if needs else 0,expected_duration_class="medium" if needs else "short",risk_class="low" if needs else "minimal",missing_information=missing,approval_required=needs,recommended_planning_mode="standard" if needs else "none",confidence=.94)
    def create_objective(self,parent_request_id:str,text:str,constraints:tuple[str,...]=())->PlanningObjective:
        if not text.strip(): raise ValueError("missing_objective")
        prohibited=tuple(item for item in constraints if item.lower().startswith(("do not","never")))
        obj=PlanningObjective(str(uuid4()),parent_request_id,text,text.strip(),text.strip(),("All approved deliverables are verified.",),constraints=constraints,prohibited_actions=prohibited)
        self.objectives[obj.objective_id]=obj; self.logger.info("planning_objective_created request_id=%s objective_id=%s",parent_request_id,obj.objective_id); return obj
    def generate(self,obj:PlanningObjective,provider_summary:str="")->AutonomousPlan:
        plan_id=str(uuid4()); titles=("Inspect authoritative interfaces","Implement the bounded change","Add behavioral verification","Document and verify the result")
        steps=[]
        for i,title in enumerate(titles,1):
            deps=(f"{plan_id}-step-{i-1}",) if i>1 else ()
            steps.append(PlanStep(f"{plan_id}-step-{i}",plan_id,title,f"Advance: {obj.desired_outcome}",title,i,dependencies=deps,required_capabilities=(("tool_discovery",) if i==1 else ()),evidence_requirements=("authoritative result",),completion_criteria=(f"{title} is verified",),risk_class="low" if i==2 else "minimal"))
        summary=provider_summary.strip() or f"Reviewable plan for {obj.normalized_objective}"
        plan=AutonomousPlan(plan_id,obj.objective_id,obj.parent_request_id,f"Plan: {obj.normalized_objective[:80]}",summary,PlanStatus.AWAITING_REVIEW,"standard",1,("Design understood","Implementation complete","Verification complete"),tuple(steps),{s.step_id:s.dependencies for s in steps},constraints=obj.constraints,success_criteria=obj.success_criteria,completion_criteria=obj.success_criteria,required_permissions=("plan.review","workflow.create"),required_approvals=("user plan approval",),risk_summary="low",estimated_duration="medium",estimated_cost="unknown",evidence_requirements=("tests","startup verification"))
        plan=replace(plan,validation=self.validate(plan)); self.plans[plan.plan_id]=plan; self._save(); self.logger.info("plan_generation_completed request_id=%s objective_id=%s plan_id=%s",obj.parent_request_id,obj.objective_id,plan.plan_id); return plan
    def generate_with_provider(self,obj:PlanningObjective,execution_manager:Any,metadata:dict[str,object])->AutonomousPlan:
        prompt="Produce a concise implementation plan summary only. Do not execute anything. Objective: "+obj.user_objective+" Constraints: "+"; ".join(obj.constraints)
        req=execution_manager.build_execution_request(intent=prompt,goal=prompt,request_id=obj.parent_request_id,provider=metadata.get("provider_preference"),model=metadata.get("model_preference"),metadata={**metadata,"local_only":metadata.get("local_only",False),"execution_policy":metadata.get("execution_policy","automatic"),"task_type":"planning"})
        result=execution_manager.execute_through_provider_router(req)
        if not result.success: raise RuntimeError("provider_plan_generation_failed")
        return self.generate(obj,result.response)
    def validate(self,plan:AutonomousPlan)->PlanValidation:
        errors=[]; ids=[s.step_id for s in plan.steps]
        if len(ids)!=len(set(ids)): errors.append("duplicate_step_id")
        if len(ids)>self.limits.maximum_steps: errors.append("step_limit_exceeded")
        known=set(ids)
        if any(d not in known for s in plan.steps for d in s.dependencies): errors.append("missing_dependency")
        graph={s.step_id:s.dependencies for s in plan.steps}; visiting=set(); done=set()
        def visit(n):
            if n in visiting: return True
            if n in done:return False
            visiting.add(n); cycle=any(visit(d) for d in graph.get(n,()) if d in graph); visiting.remove(n); done.add(n); return cycle
        if any(visit(n) for n in graph): errors.append("dependency_cycle")
        unavailable=[]
        if self.tool_manager:
            unavailable.extend(t for t in plan.required_tools if self.tool_manager.lookup(t) is None)
        if unavailable: errors.append("unavailable_tool")
        return PlanValidation(not errors,tuple(errors),unavailable_dependencies=tuple(unavailable),required_permissions=plan.required_permissions,required_approvals=plan.required_approvals)
    def approve(self,plan_id:str,approval_reference:str)->AutonomousPlan:
        plan=self.plans[plan_id]
        if not approval_reference or not plan.validation or not plan.validation.valid: raise ValueError("approval_or_validation_missing")
        plan=replace(plan,status=PlanStatus.APPROVED,updated_at=now()); self.plans[plan_id]=plan; self._save(); return plan
    def handoff(self,plan_id:str)->dict[str,object]:
        plan=self.plans[plan_id]
        if plan.status!=PlanStatus.APPROVED:return {"status":"blocked","reason":"approval_required"}
        return {"status":"execution_ready","plan_id":plan.plan_id,"objective_id":plan.objective_id,"request_id":plan.parent_request_id,"immutable_version":plan.version,"workflow_request":{"name":plan.title,"steps":tuple(s.title for s in plan.steps)}}
    def pause(self,pid): self.plans[pid]=replace(self.plans[pid],status=PlanStatus.PAUSED); self._save(); return self.plans[pid]
    def resume(self,pid):
        if self.plans[pid].status!=PlanStatus.PAUSED: raise ValueError("invalid_transition")
        self.plans[pid]=replace(self.plans[pid],status=PlanStatus.AWAITING_REVIEW); self._save(); return self.plans[pid]
    def cancel(self,pid): self.plans[pid]=replace(self.plans[pid],status=PlanStatus.CANCELLED); self._save(); return self.plans[pid]
    def replan(self,pid,trigger):
        old=self.plans[pid]
        if old.replanning_count>=self.limits.maximum_replans: raise ValueError("replanning_limit")
        self.plans[pid]=replace(old,status=PlanStatus.SUPERSEDED); new=self.generate(self.objectives[old.objective_id],old.summary+f" Replanned because: {trigger}"); new=replace(new,version=old.version+1,replanning_count=old.replanning_count+1); self.plans[new.plan_id]=new; self._save(); return new
    def set_mode(self,mode): self.mode=PlanningMode(mode); return self.mode
    def _save(self):
        if not self.storage_dir:return
        self.storage_dir.mkdir(parents=True,exist_ok=True); (self.storage_dir/"plans.json").write_text(json.dumps([asdict(p) for p in self.plans.values()],default=str,indent=2),encoding="utf-8")
    def _load(self):
        # Observable records are retained on disk; unsafe in-progress execution is never resumed.
        return
