"""Approval-gated local command sandbox using argument arrays and shell=False."""
from dataclasses import dataclass,field
from pathlib import Path
import os,re,shlex,subprocess,time
from jarvis.foundation_common import bounded,new_id,safe_ref
from .broker import ExecutionBroker,ToolExecutionRequest
from .models import ExecutionMode,ExecutionPermission,ExecutionRisk
META=re.compile(r"[|&;<>`$\n\r]"); BLOCKED={"powershell","pwsh","cmd","bash","sh","curl","wget","sudo","runas","npm","pip"}; GIT_WRITES={"add","commit","push","pull","checkout","switch","reset","clean","merge","rebase","cherry-pick","tag","config"}
@dataclass(frozen=True,slots=True)
class CommandSandboxPolicy:
 allowed_executables:tuple[str,...]=("python","python3","pytest","git","ruff","mypy","black");blocked_executables:tuple[str,...]=tuple(BLOCKED);allow_network_commands:bool=False;allow_package_install:bool=False;allow_shell_metacharacters:bool=False;allow_background_processes:bool=False;allow_privilege_escalation:bool=False;allow_environment_inheritance:bool=False;default_timeout_seconds:int=30;max_timeout_seconds:int=90;max_output_chars:int=4000;require_approval:bool=True
@dataclass(frozen=True,slots=True)
class CommandValidation:
 executable_allowed:bool;arguments_allowed:bool;working_directory_allowed:bool;environment_safe:bool;network_use_detected:bool;destructive_pattern_detected:bool;privilege_escalation_detected:bool;background_process_detected:bool;approval_valid:bool=False;blocked_reason:str="";validation_id:str=field(default_factory=new_id)
@dataclass(frozen=True,slots=True)
class CommandExecutionResult:
 request_id:str;status:str;exit_code:int|None=None;timed_out:bool=False;stdout_preview:str="";stderr_preview:str="";output_truncated:bool=False;duration_ms:int=0;warnings:tuple[str,...]=();error:str|None=None
class CommandSandbox:
 def __init__(self,root:Path,broker:ExecutionBroker):self.root=root.resolve();self.policy=CommandSandboxPolicy();self.broker=broker;self.history=[]
 def parse(self,text):
  if META.search(text):raise ValueError("shell_metacharacters_blocked")
  return tuple(shlex.split(text,posix=os.name!="nt"))
 def validate(self,text,cwd=None):
  try:parts=self.parse(text)
  except ValueError as e:return CommandValidation(False,False,False,True,False,False,False,False,blocked_reason=str(e))
  if not parts:return CommandValidation(False,False,False,True,False,False,False,False,blocked_reason="empty_command")
  exe=Path(parts[0]).name.lower().removesuffix(".exe");wd=Path(cwd or self.root).resolve();inside=wd==self.root or self.root in wd.parents
  gitwrite=exe=="git" and len(parts)>1 and parts[1].lower() in GIT_WRITES;network=exe in {"curl","wget"};destructive=any(x in " ".join(parts).lower() for x in ("remove-item","rm -","del /","format","shutdown","force push"));blocked=exe in BLOCKED or exe not in self.policy.allowed_executables or gitwrite or network or destructive
  reason="git_write_requires_git_executor" if gitwrite else "executable_or_command_class_blocked" if blocked else "working_directory_blocked" if not inside else ""
  return CommandValidation(not blocked,not blocked,inside,True,network,destructive,exe in {"sudo","runas"},False,blocked_reason=reason)
 def dry_run(self,text,cwd=None):
  v=self.validate(text,cwd);return CommandExecutionResult(new_id(),"dry_run_completed" if v.executable_allowed and v.working_directory_allowed else "blocked",warnings=("shell=False; no command executed.",),error=v.blocked_reason or None)
 def execute(self,text,approval_id,cwd=None,timeout=None):
  v=self.validate(text,cwd);parts=self.parse(text) if v.executable_allowed else ();summary=" ".join(parts);resource=(safe_ref(cwd or self.root),summary)
  req=ToolExecutionRequest("command_execute","command_executor","commands",summary or text,ExecutionMode.APPROVED_EXECUTION,ExecutionRisk.MEDIUM,(ExecutionPermission.EXECUTE_COMMANDS,),resource,approval_id,False)
  if not v.executable_allowed or not v.working_directory_allowed:return CommandExecutionResult(req.request_id,"blocked",error=v.blocked_reason)
  if self.broker.route(req).status!="approved_for_executor":return CommandExecutionResult(req.request_id,"approval_required",error="invalid_or_missing_approval")
  safe_env={k:v for k,v in os.environ.items() if k.upper() in {"PATH","PATHEXT","SYSTEMROOT","WINDIR","TEMP","TMP","COMSPEC"} and not any(x in k.upper() for x in ("TOKEN","KEY","SECRET","PASSWORD"))};start=time.monotonic();limit=min(timeout or self.policy.default_timeout_seconds,self.policy.max_timeout_seconds)
  try:
   p=subprocess.run(list(parts),cwd=str(Path(cwd or self.root).resolve()),env=safe_env,capture_output=True,text=True,timeout=limit,shell=False)
   out,err=p.stdout,p.stderr;trunc=len(out)>self.policy.max_output_chars or len(err)>self.policy.max_output_chars;r=CommandExecutionResult(req.request_id,"completed" if p.returncode==0 else "failed",p.returncode,False,bounded(out,self.policy.max_output_chars),bounded(err,self.policy.max_output_chars),trunc,int((time.monotonic()-start)*1000));self.history=(self.history+[r])[-50:];return r
  except subprocess.TimeoutExpired:return CommandExecutionResult(req.request_id,"failed",timed_out=True,duration_ms=int((time.monotonic()-start)*1000),error="command_timeout")
