from dataclasses import dataclass,field
import re
from jarvis.foundation_common import contains_secret,new_id
from .models import *
def classify_schedule_intent(t):
 v=t.lower()
 if contains_secret(t) or any(x in v for x in ("friend's location","track person","every second","hidden")):return ScheduleIntent.UNSAFE_BACKGROUND_TASK
 if "every" in v or "daily" in v or "weekly" in v:return ScheduleIntent.RECURRING_REMINDER_PLAN
 if "monitor" in v or "watch" in v:return ScheduleIntent.CONDITION_WATCH_PLAN
 return ScheduleIntent.ONE_TIME_REMINDER_PLAN
def schedule_safety(t):
 i=classify_schedule_intent(t)
 if i is ScheduleIntent.UNSAFE_BACKGROUND_TASK:return ScheduleRiskLevel.CRITICAL,False,"Hidden, private-person, secret, or abusive background monitoring is blocked."
 return (ScheduleRiskLevel.MEDIUM if i is ScheduleIntent.CONDITION_WATCH_PLAN else ScheduleRiskLevel.LOW),True,"Planning is allowed; no job is installed or run."
@dataclass(slots=True)
class SchedulerAgent:
 enabled:bool=True;max_history_items:int=25;history:list[ScheduleResult]=field(default_factory=list)
 def _record(self,r):self.history=(self.history+[r])[-self.max_history_items:];return r
 def status(self):return {"status":"ready_plan_only" if self.enabled else "disabled","background_runner":"disabled","os_cron":"disabled","task_scheduler":"disabled","notifications":"disabled","max_cadence":"hourly"}
 def validate(self,t):
  issues=[]
  if not t.strip():issues.append("Schedule text is required.")
  if re.search(r"every\s+(second|minute)",t,re.I):issues.append("Cadence below hourly is blocked by default.")
  if classify_schedule_intent(t) is ScheduleIntent.UNSAFE_BACKGROUND_TASK:issues.append("Unsafe background request.")
  return ScheduleValidation(not issues," ".join(t.lower().split()),tuple(issues),("No active task is created.",))
 def plan(self,t):
  risk,ok,reason=schedule_safety(t);intent=classify_schedule_intent(t);req=ScheduleRequest(t," ".join(t.lower().split()),intent,risk_level=risk);validation=self.validate(t);stype=ScheduleType.RECURRING if intent is ScheduleIntent.RECURRING_REMINDER_PLAN else ScheduleType.CONDITION_WATCH if intent is ScheduleIntent.CONDITION_WATCH_PLAN else ScheduleType.ONE_TIME
  spec=ScheduleSpec(stype,"user_supplied_unresolved",recurrence_rule="bounded_plan",cadence="hourly_or_slower" if stype is not ScheduleType.ONE_TIME else "one_time",human_readable_schedule=t)
  action=ScheduledAction("notification_plan","scheduler_agent","scheduler_planning_skill","User-supplied task summary")
  status=ScheduleStatus.PLANNED if ok and validation.valid else ScheduleStatus.BLOCKED if not ok else ScheduleStatus.INVALID
  plan=SchedulePlan(req.request_id,intent,"Plan a bounded schedule without installing or running it.",spec,action,("Validate cadence and timezone.","Create metadata-only plan.","Require a future approved runner for execution."),risk_level=risk,status=status,warnings=(() if ok else(reason,)))
  return self._record(ScheduleResult(req.request_id,status,req,plan,validation,warnings=plan.warnings,error=None if status is ScheduleStatus.PLANNED else "schedule_not_executable"))
 def show(self,i):return next((x for x in reversed(self.history) if x.request_id==i),None)
