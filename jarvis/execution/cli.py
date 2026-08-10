"""Bounded CLI rendering for the Phase 4 controlled-execution chain."""
from __future__ import annotations
from pathlib import Path
from jarvis.foundation_common import bounded,safe_ref
from jarvis.approvals import ApprovalDecisionType,ApprovalRegistry
from jarvis.execution.models import ExecutionMode,ExecutionPermission,ExecutionRisk
from jarvis.execution.policy import ExecutionPolicyEngine,PERMISSIONS
from jarvis.execution.broker import ExecutionBroker
from jarvis.execution.files import FileExecutor
from jarvis.execution.commands import CommandSandbox
from jarvis.execution.git import GitExecutor
from jarvis.browser.execution import BrowserReader
from jarvis.notifications import NotificationExecutor
from jarvis.scheduler.runtime import SchedulerRuntime

class Phase4Runtime:
 def __init__(self,root):
  self.root=Path(root).resolve();self.policy=ExecutionPolicyEngine();self.approvals=ApprovalRegistry();self.broker=ExecutionBroker(self.policy,self.approvals);self.files=FileExecutor(self.root,self.broker);self.commands=CommandSandbox(self.root,self.broker);self.git=GitExecutor(self.root,self.broker);self.browser=BrowserReader(self.broker);self.notifications=NotificationExecutor(self.broker);self.scheduler=SchedulerRuntime(self.broker,self.notifications)
_RUNTIMES={}
def get_phase4_runtime(root):
 key=str(Path(root).resolve());_RUNTIMES.setdefault(key,Phase4Runtime(key));return _RUNTIMES[key]
def _approval_resource(action,summary):
 words=summary.split();
 if action=="file_write":return (safe_ref(words[-1] if words else "workspace_file"),)
 if action=="command_execute":return ("repository",summary)
 if action=="git_write":return ("main",summary)
 if action=="browser_read":
  from urllib.parse import urlsplit
  return (urlsplit(next((x for x in words if x.startswith(("http://","https://"))),"https://public.invalid")).hostname or "public.invalid",)
 if action=="notification_send":return ("local_device",f"JARVIS:{len(summary)}")
 return ("local_scope",)
def _approval_id(args,flags):
 value=flags.get("approval","")
 if isinstance(value,str):return value
 return args[-1] if value is True and args else ""
def render_phase4_command(runtime,name,args=(),flags=None):
 flags=flags or {};text=" ".join(args).strip();parts=name.split();ns=parts[0];op=" ".join(parts[1:]) or "status"
 if ns=="execution":
  if op=="status":return "Execution: ready policy-only; default=plan_only; approval=required; critical=blocked; local executors=approved-only"
  if op=="help":return "execution status|policy|permissions|readiness|risk <request>|plan <request>|capabilities|show|history"
  if op=="policy":return "Execution policy: local-first; side effects require explicit approval; secrets/credentials/external background execution blocked."
  if op=="permissions":return "Permissions: read metadata is low risk; file/command/Git/browser/notification/scheduler side effects require scoped approval; secrets and credentials are blocked."
  if op=="readiness":return "; ".join(f"{x.subsystem}={'ready' if x.execution_available else 'disabled'}" for x in runtime.policy.readiness())
  if op in {"risk","plan"}:
   r=runtime.policy.plan(text);return f"Execution {op}: action={r.plan.action_type} risk={r.plan.risk_level.value} mode={r.status.value} approval={'yes' if r.plan.approval_required else 'no'} blocked={r.plan.blocked_reason or 'no'}"
  if op=="capabilities":return "Controlled: files, commands, Git, public browser read, local notifications, manual scheduler. Disabled: secrets, external communication, MCP/plugin/model runtime, daemon, deploy."
  return "Execution history is bounded metadata only."
 if ns=="approval":
  if op=="status":return f"Approvals: ready explicit_only pending={len(runtime.approvals.pending())} implied=no broad=no permanent=no critical=no"
  if op=="help":return "approval request <summary>|pending|list|show <id>|approve|deny|cancel|revoke <id>|expire|validate <id>"
  if op=="request":
   action,risk=runtime.policy.classify(text);perms=PERMISSIONS.get(action,());resources=_approval_resource(action,text);r=runtime.approvals.create(text,action,perms,resources,risk=risk);return f"Approval: id={r.approval_id} status={r.status.value} action={r.action_type} risk={r.risk_level.value} permissions={','.join(x.value for x in r.required_permissions) or 'none'} resources={','.join(r.affected_resources)}"
  if op in {"pending","list"}:return "Approvals: "+("; ".join(f"{r.approval_id}:{runtime.approvals.status(r.approval_id).status.value}:{r.action_type}" for r in (runtime.approvals.pending() if op=="pending" else runtime.approvals.recent())) or "none")
  if op=="expire":return f"Approvals expired: {runtime.approvals.expire()}"
  i=args[0] if args else "";r=runtime.approvals.get(i)
  if op=="show":return "Approval unavailable." if not r else f"Approval: id={i} status={runtime.approvals.status(i).status.value} action={r.action_type} risk={r.risk_level.value} permissions={','.join(x.value for x in r.required_permissions)} resources={','.join(r.affected_resources)}"
  if op=="validate":
   s=runtime.approvals.status(i);return "Approval unavailable." if not s else f"Approval valid={str(s.usable_for_execution).lower()} status={s.status.value} expired={str(s.expired).lower()}"
  if op in {"approve","deny","cancel","revoke"}:return f"Approval {op}: {runtime.approvals.decide(i,ApprovalDecisionType(op)).status.value}"
 if ns=="broker":
  if op=="status":return "Broker: ready validation/dry-run; actual execution only via dedicated approved executors."
  if op=="help":return "broker status|capabilities|plan|validate|dry-run|execute|show|history"
  if op=="capabilities":return "; ".join(f"{x.tool_id}:execute={str(x.execution_available).lower()}:approval={str(x.approval_required).lower()}" for x in runtime.broker.tools.values())
  r=runtime.policy.plan(text);return f"Broker {op}: action={r.plan.action_type} mode={r.status.value}; no side effect occurred."
 if ns=="file-exec":
  if op=="status":return "File execution: ready approved scoped text operations; root=repository; dry-run=yes; overwrite=no; delete=no; rollback=yes"
  if op=="help":return "file-exec status|policy|validate|plan|dry-run|create|write|append|mkdir|rename|move|delete|rollback|show|history"
  if op=="policy":return "Files: repository root only; approval required; traversal/symlink/.env/.git/models/data/system paths blocked; overwrite/delete disabled."
  if op=="validate":
   v=runtime.files.validate_path(args[0] if args else "");return f"File path allowed={str(v.target_allowed).lower()} reason={v.blocked_reason or 'none'}"
  if op in {"plan","dry-run"}:return f"File {op}: {runtime.policy.plan(text).status.value}; no mutation occurred."
  if op=="rollback":return f"File rollback: {'completed' if args and runtime.files.rollback(args[0]) else 'unavailable'}"
  if op in {"create","write","append","mkdir","delete"}:
   path=args[0] if args else "";content=args[1] if len(args)>1 else "";operation={"create":"create_text_file","write":"write_text","append":"append_text","mkdir":"create_directory","delete":"delete_file"}[op];r=runtime.files.execute(operation,path,content,approval_id=_approval_id(args,flags));return f"File execution: status={r.status} target={r.target_summary} rollback={r.rollback_id or 'none'} error={r.error or 'none'}"
  if op in {"rename","move"}:
   r=runtime.files.execute(op+"_file",args[0] if args else "",destination=args[1] if len(args)>1 else "",approval_id=_approval_id(args,flags));return f"File execution: status={r.status} target={r.target_summary} rollback={r.rollback_id or 'none'} error={r.error or 'none'}"
  return "File execution history is bounded metadata only."
 if ns=="command":
  if op=="status":return "Command sandbox: ready approved-only; shell=no network=no install=no background=no Git-writes=no timeout=30s output=4000"
  if op=="help":return "command status|policy|allowlist|validate|plan|dry-run|execute|show|history"
  if op=="policy":return "Command policy: argument arrays, shell=False, repository cwd, sanitized environment, bounded timeout/output; network/install/elevation/background/Git writes blocked."
  if op=="allowlist":return "Command allowlist: "+", ".join(runtime.commands.policy.allowed_executables)
  if op in {"validate","plan","dry-run"}:
   r=runtime.commands.dry_run(text);return f"Command {op}: status={r.status} error={r.error or 'none'}; no execution occurred."
  if op=="execute":
   r=runtime.commands.execute(text,_approval_id(args,flags));return f"Command: status={r.status} exit={r.exit_code} timeout={str(r.timed_out).lower()} stdout={r.stdout_preview} stderr={r.stderr_preview} error={r.error or 'none'}"
  return "Command history is metadata-only; stdout/stderr are not persisted."
 if ns=="git-exec":
  if op=="status":return f"Git execution: ready approved-only repository=JarvisOS branch={runtime.git.branch() or 'detached'} force=no destructive=no"
  if op=="help":return "git-exec status|policy|inspect|files|validate|plan|dry-run|stage|unstage|commit|push|show|history"
  if op=="policy":return "Git: explicit files only; protected/secret scan; commit/push separately approved; force/reset/clean/merge/rebase/remote changes blocked."
  if op in {"inspect","files"}:return "Git inspection: "+(runtime.git.inspect() or "clean")
  if op in {"validate","plan","dry-run"}:return "Git plan: dedicated executor required; no mutation occurred."
  if op=="stage":r=runtime.git.stage(args[:-1] if flags.get("approval") is True else args,_approval_id(args,flags))
  elif op=="unstage":r=runtime.git.unstage(args[:-1] if flags.get("approval") is True else args,_approval_id(args,flags))
  elif op=="commit":r=runtime.git.commit(str(flags.get("message",text)),_approval_id(args,flags))
  elif op=="push":r=runtime.git.push(_approval_id(args,flags),str(flags.get("remote","origin")),str(flags.get("branch","main")))
  else:return "Git execution history is bounded metadata only."
  return f"Git: operation={r.operation} status={r.status} commit={r.commit_ref or 'none'} push={r.push_status or 'none'} error={r.error or 'none'}"
 if ns=="notification":
  if op=="status":return f"Notifications: ready local-only provider={runtime.notifications.provider.provider.provider_id}; approval=yes external=no actions=no"
  if op=="help":return "notification status|providers|policy|plan|validate|dry-run|send|test|show|history"
  if op=="providers":p=runtime.notifications.provider.provider;return f"{p.provider_id}: status={p.status} platform={p.platform} os_toast={'yes' if 'os_toast' in p.supported_features else 'no'}"
  if op=="policy":return "Notifications: local-only; approval required; no network/actions; bounded and rate-limited; console fallback is not an OS toast."
  if op in {"plan","validate","dry-run"}:r=runtime.notifications.dry_run("JARVIS",text);return f"Notification {op}: status={r.status} displayed=no error={r.error or 'none'}"
  if op in {"send","test"}:r=runtime.notifications.send("JARVIS",text or "JARVIS notification test",_approval_id(args,flags));return f"Notification: status={r.status} provider={r.provider_id} displayed={str(r.displayed).lower()} error={r.error or 'none'}"
  return "Notification history is metadata-only; full bodies are not stored."
 if ns=="browser":
  if op=="policy":return "Browser read: approved public HTTP(S) GET only; private/loopback/metadata targets, custom ports, auth, cookies, JavaScript, forms, downloads, and writes are blocked."
  if op=="validate":
   v=runtime.browser.validate_url(args[0] if args else "");return f"Browser URL allowed={str(v.public_target).lower()} reason={v.blocked_reason or 'none'} private={str(v.private_network_detected).lower()} loopback={str(v.loopback_detected).lower()}"
  if op=="dry-run":
   r=runtime.browser.dry_run(args[0] if args else "");return f"Browser dry-run: status={r.status} source={r.source_ref or 'none'} network=no error={r.error or 'none'}"
  if op=="read":
   r=runtime.browser.read(args[0] if args else "",_approval_id(args,flags));return f"Browser read: status={r.status} source={r.source_ref or 'none'} title={r.title or 'none'} bytes={r.content_length} truncated={str(r.truncated).lower()} error={r.error or 'none'}"
  if op=="read-show":
   r=next((item for item in runtime.browser.history if item.request_id==(args[0] if args else "")),None);return "Browser read unavailable." if not r else f"Browser read: id={r.request_id} status={r.status} source={r.source_ref} bytes={r.content_length} error={r.error or 'none'}"
  if op=="read-history":return "Browser read history: "+("; ".join(f"{r.request_id}:{r.status}:{r.source_ref}" for r in runtime.browser.history[-25:]) or "none")
 if ns=="scheduler" and op in {"runtime-status","jobs","due","create","run","run-due","pause","resume","cancel","runs","runtime-policy"}:
  rt=runtime.scheduler
  if op=="runtime-status":return f"Scheduler runtime: manual=yes background=no active={sum(j.status.value=='active' for j in rt.jobs.values())} due={len(rt.due())}"
  if op=="runtime-policy":return "Scheduler: manual runner only; notification target enabled; browser/file/command/Git/communication scheduling disabled; cadence>=60m concurrency=1."
  if op in {"jobs","due"}:items=rt.jobs.values() if op=="jobs" else rt.due();return f"Scheduler {op}: "+("; ".join(f"{j.job_id}:{j.status.value}:{j.target_action}" for j in items) or "none")
  if op=="create":
   try:j=rt.create(text,_approval_id(args,flags));return f"Scheduler created: id={j.job_id} status={j.status.value} target={j.target_action}"
   except ValueError as e:return f"Scheduler create blocked: {e}"
  if op=="run":r=rt.run(args[0] if args else "");return f"Scheduler run: status={r.execution_status} approval={r.approval_status} error={r.error or 'none'}"
  if op=="run-due":return f"Scheduler run-due: runs={len(rt.run_due())}"
  if op in {"pause","resume","cancel"}:return f"Scheduler {op}: {str(getattr(rt,op)(args[0] if args else '')).lower()}"
  if op=="runs":return "Scheduler runs: "+("; ".join(f"{r.run_id}:{r.execution_status}" for r in rt.runs[-25:]) or "none")
 return "Phase 4 command unavailable."
