"""Manual-only local scheduler runtime; no daemon or OS schedule registration."""
from dataclasses import dataclass,field
from datetime import UTC,datetime,timedelta
from enum import StrEnum
from jarvis.foundation_common import new_id,now,validate_request_text
from jarvis.execution.broker import ExecutionBroker,ToolExecutionRequest
from jarvis.execution.models import ExecutionMode,ExecutionPermission,ExecutionRisk
class JobStatus(StrEnum): PLANNED="planned";ACTIVE="active";DUE="due";RUNNING="running";COMPLETED="completed";PAUSED="paused";CANCELLED="cancelled";BLOCKED="blocked";FAILED="failed";EXPIRED="expired"
@dataclass(slots=True)
class ScheduledJob:
 schedule_type:str;schedule_spec:str;target_action:str;action_summary:str;approval_id:str;next_run_at:str;target_subsystem:str="notifications";status:JobStatus=JobStatus.ACTIVE;job_id:str=field(default_factory=new_id);created_at:str=field(default_factory=now);last_run_at:str="";run_count:int=0;max_runs:int=1;cadence_minutes:int=60;warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class ScheduledRun:
 job_id:str;target_action:str;approval_status:str;execution_status:str;attempt:int=1;run_id:str=field(default_factory=new_id);started_at:str=field(default_factory=now);completed_at:str=field(default_factory=now);warnings:tuple[str,...]=();error:str|None=None
@dataclass(frozen=True,slots=True)
class SchedulerRuntimePolicy:
 enabled:bool=True;default_mode:str="manual_run";allow_background_runner:bool=False;allow_manual_runner:bool=True;allow_one_time:bool=True;allow_recurring:bool=True;allow_condition_watch_execution:bool=False;allow_scheduled_notifications:bool=True;allow_scheduled_browser_read:bool=False;allow_scheduled_file_write:bool=False;allow_scheduled_commands:bool=False;allow_scheduled_git:bool=False;allow_scheduled_communication:bool=False;min_cadence_minutes:int=60;max_jobs:int=50;max_due_per_run:int=5;max_concurrent_runs:int=1;max_retries:int=1;require_approval:bool=True;revalidate_approval_each_run:bool=True
class SchedulerRuntime:
 def __init__(self,broker:ExecutionBroker,notification_executor=None,clock=None):self.broker=broker;self.notification_executor=notification_executor;self.clock=clock or (lambda:datetime.now(UTC));self.policy=SchedulerRuntimePolicy();self.jobs={};self.runs=[]
 def create(self,summary,approval_id,*,when=None,recurring=False,cadence_minutes=60,max_runs=1,target="notification_send"):
  validate_request_text(summary)
  if len(self.jobs)>=self.policy.max_jobs or cadence_minutes<self.policy.min_cadence_minutes or target!="notification_send":raise ValueError("schedule_blocked")
  job=ScheduledJob("recurring" if recurring else "one_time",f"cadence_minutes={cadence_minutes}",target,summary,approval_id,(when or self.clock()).isoformat(),max_runs=max_runs,cadence_minutes=cadence_minutes);self.jobs[job.job_id]=job;return job
 def due(self):return tuple(j for j in self.jobs.values() if j.status is JobStatus.ACTIVE and datetime.fromisoformat(j.next_run_at)<=self.clock())[:self.policy.max_due_per_run]
 def run(self,job_id):
  j=self.jobs.get(job_id)
  if not j or j.status is not JobStatus.ACTIVE:return ScheduledRun(job_id,"unknown","invalid","blocked",error="job_not_runnable")
  if datetime.fromisoformat(j.next_run_at)>self.clock():return ScheduledRun(job_id,j.target_action,"not_due","blocked",error="job_not_due")
  fingerprint=f"Scheduled reminder:{len(j.action_summary)}";valid=self.broker.approvals.validate(j.approval_id,"notification_send",(ExecutionPermission.SEND_NOTIFICATION,),("local_device",fingerprint))
  if not valid:return ScheduledRun(job_id,j.target_action,"invalid","blocked",error="approval_invalid")
  j.status=JobStatus.RUNNING
  result=self.notification_executor.send("Scheduled reminder",j.action_summary,j.approval_id) if self.notification_executor else None;status=result.status if result else "unavailable";j.last_run_at=self.clock().isoformat();j.run_count+=1
  if status=="completed" and j.schedule_type=="recurring" and j.run_count<j.max_runs:j.status=JobStatus.ACTIVE;j.next_run_at=(self.clock()+timedelta(minutes=j.cadence_minutes)).isoformat()
  else:j.status=JobStatus.COMPLETED if status=="completed" else JobStatus.FAILED
  run=ScheduledRun(j.job_id,j.target_action,"approved",status,error=None if status=="completed" else "target_failed");self.runs=(self.runs+[run])[-100:];return run
 def run_due(self):return tuple(self.run(j.job_id) for j in self.due())
 def pause(self,i):
  if i in self.jobs and self.jobs[i].status is JobStatus.ACTIVE:self.jobs[i].status=JobStatus.PAUSED;return True
  return False
 def resume(self,i):
  if i in self.jobs and self.jobs[i].status is JobStatus.PAUSED:self.jobs[i].status=JobStatus.ACTIVE;return True
  return False
 def cancel(self,i):
  if i in self.jobs and self.jobs[i].status not in {JobStatus.COMPLETED,JobStatus.CANCELLED}:self.jobs[i].status=JobStatus.CANCELLED;return True
  return False
