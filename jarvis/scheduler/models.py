"""Typed scheduler planning models; no background runner."""
from dataclasses import dataclass,field
from enum import StrEnum
from jarvis.foundation_common import new_id,now,validate_items,validate_request_text,validate_text
class ScheduleIntent(StrEnum): ONE_TIME_REMINDER_PLAN="one_time_reminder_plan"; RECURRING_REMINDER_PLAN="recurring_reminder_plan"; RECURRING_SUMMARY_PLAN="recurring_summary_plan"; CONDITION_WATCH_PLAN="condition_watch_plan"; RESEARCH_CHECK_PLAN="research_check_plan"; WEB_MONITORING_PLAN="web_monitoring_plan"; SYSTEM_MAINTENANCE_PLAN="system_maintenance_plan"; WORKFLOW_PLAN="workflow_plan"; SCHEDULE_STATUS="schedule_status"; SCHEDULE_VALIDATION="schedule_validation"; UNSAFE_BACKGROUND_TASK="unsafe_background_task"; UNKNOWN="unknown"
class ScheduleType(StrEnum): ONE_TIME="one_time"; RECURRING="recurring"; CONDITION_WATCH="condition_watch"; MANUAL_TRIGGER="manual_trigger"; DISABLED_FUTURE="disabled_future"
class ScheduleRiskLevel(StrEnum): LOW="low"; MEDIUM="medium"; HIGH="high"; CRITICAL="critical"
class ScheduleStatus(StrEnum): PLANNED="planned"; VALID="valid"; INVALID="invalid"; BLOCKED="blocked"; UNAVAILABLE="unavailable"
@dataclass(frozen=True,slots=True)
class ScheduleRequest:
 request:str; normalized_request:str; intent:ScheduleIntent=ScheduleIntent.UNKNOWN; scope:str="local_plan"; risk_level:ScheduleRiskLevel=ScheduleRiskLevel.LOW; request_id:str=field(default_factory=new_id); created_at:str=field(default_factory=now)
 def __post_init__(self):validate_request_text(self.request);validate_request_text(self.normalized_request)
@dataclass(frozen=True,slots=True)
class ScheduleSpec:
 schedule_type:ScheduleType; start_time:str; timezone_policy:str="local_explicit"; recurrence_rule:str=""; cadence:str="one_time"; end_condition:str="manual"; max_runs:int=1; human_readable_schedule:str=""; warnings:tuple[str,...]=(); schedule_id:str=field(default_factory=new_id)
@dataclass(frozen=True,slots=True)
class ScheduledAction:
 action_type:str; target_agent:str; target_skill:str; prompt_or_task_summary:str; execution_mode:str="plan_only"; requires_approval:bool=True; allowed:bool=False; blocked_reason:str="Background execution is disabled."; warnings:tuple[str,...]=(); action_id:str=field(default_factory=new_id)
@dataclass(frozen=True,slots=True)
class SchedulePlan:
 request_id:str; intent:ScheduleIntent; summary:str; schedule:ScheduleSpec; action:ScheduledAction; proposed_steps:tuple[str,...]; required_permissions:tuple[str,...]=(); risk_level:ScheduleRiskLevel=ScheduleRiskLevel.LOW; approval_required:bool=True; background_execution_available:bool=False; status:ScheduleStatus=ScheduleStatus.PLANNED; warnings:tuple[str,...]=(); plan_id:str=field(default_factory=new_id)
 def __post_init__(self):validate_text(self.summary);validate_items(self.proposed_steps)
@dataclass(frozen=True,slots=True)
class ScheduleValidation:
 valid:bool; normalized_schedule:str; issues:tuple[str,...]=(); warnings:tuple[str,...]=(); next_run_preview:str="unavailable_without_runtime"; max_run_policy:str="bounded"; validation_id:str=field(default_factory=new_id)
@dataclass(frozen=True,slots=True)
class ScheduleResult:
 request_id:str; status:ScheduleStatus; request:ScheduleRequest|None=None; plan:SchedulePlan|None=None; validation:ScheduleValidation|None=None; output:str=""; warnings:tuple[str,...]=(); error:str|None=None
