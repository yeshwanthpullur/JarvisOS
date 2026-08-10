from .agent import SchedulerAgent,schedule_safety
def render_scheduler_command(a,c,args):
 t=" ".join(args).strip()
 if c=="scheduler status":return "Scheduler status: "+" ".join(f"{k}={v}" for k,v in a.status().items())
 if c=="scheduler help":return "Scheduler commands: status, help, plan, safety, validate, preview, capabilities, show, history. Planning only; no background runner, cron, Task Scheduler, or notifications."
 if c=="scheduler capabilities":return "Scheduler capabilities: one_time_plan=yes recurring_plan=yes condition_watch_plan=yes background_runner=no os_cron=no task_scheduler=no notifications=no."
 if c=="scheduler safety":
  r,ok,why=schedule_safety(t);return f"Scheduler safety: risk={r.value} allowed={'yes' if ok else 'no'} reason={why}"
 if c=="scheduler validate":
  v=a.validate(t);return f"Scheduler validation: valid={'yes' if v.valid else 'no'} normalized={v.normalized_schedule} issues={'; '.join(v.issues) or 'none'}."
 if c=="scheduler preview":
  v=a.validate(t);return f"Scheduler preview: valid={'yes' if v.valid else 'no'} next_run={v.next_run_preview} active_task_created=no."
 if c=="scheduler plan":
  r=a.plan(t);return f"Scheduler plan: status={r.status.value} type={r.plan.schedule.schedule_type.value} background_execution=no steps="+" | ".join(r.plan.proposed_steps)
 if c=="scheduler show":
  r=a.show(t);return "Schedule job unavailable." if r is None else f"Schedule job: id={r.request_id} status={r.status.value}."
 if c=="scheduler history":return "Scheduler history: "+(", ".join(f"{x.request_id}:{x.status.value}" for x in a.history[-10:]) or "empty")
 return "Scheduler command unavailable."
