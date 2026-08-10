"""Dedicated approval-gated Git mutations; generic command execution cannot bypass it."""
from dataclasses import dataclass,field
from pathlib import Path
import re,subprocess
from jarvis.foundation_common import bounded,contains_secret,new_id,safe_ref
from .broker import ExecutionBroker,ToolExecutionRequest
from .models import ExecutionMode,ExecutionPermission,ExecutionRisk
PROTECTED=(".env",".pem",".key",".pfx",".p12",".backup",".db",".sqlite")
@dataclass(frozen=True,slots=True)
class GitExecutionPolicy:
 allowed_remotes:tuple[str,...]=("origin",);allowed_branches:tuple[str,...]=("main",);require_approval:bool=True;allow_stage:bool=True;allow_unstage:bool=True;allow_commit:bool=True;allow_push:bool=True;allow_tag_create:bool=False;allow_force_push:bool=False;allow_reset:bool=False;allow_clean:bool=False;allow_merge:bool=False;allow_rebase:bool=False;allow_remote_modify:bool=False;block_sensitive_files:bool=True
@dataclass(frozen=True,slots=True)
class GitFileAssessment:
 file_ref:str;tracked:bool=False;staged:bool=False;modified:bool=False;untracked:bool=False;ignored:bool=False;sensitive:bool=False;runtime_generated:bool=False;model_file:bool=False;media_file:bool=False;backup_file:bool=False;allowed_to_stage:bool=True;blocked_reason:str=""
@dataclass(frozen=True,slots=True)
class GitOperationResult:
 request_id:str;operation:str;status:str;commit_ref:str="";push_status:str="";remote_ref:str="";files_changed_count:int=0;warnings:tuple[str,...]=();error:str|None=None
class GitExecutor:
 def __init__(self,repo:Path,broker:ExecutionBroker,allowed_branches=("main",)):self.repo=repo.resolve();self.broker=broker;self.policy=GitExecutionPolicy(allowed_branches=allowed_branches);self.history=[]
 def _git(self,*args,timeout=30):return subprocess.run(["git",*args],cwd=self.repo,capture_output=True,text=True,timeout=timeout,shell=False)
 def branch(self):return self._git("branch","--show-current").stdout.strip()
 def inspect(self):return bounded(self._git("status","--short").stdout,2000)
 def assess(self,ref):
  p=Path(ref);low=p.name.lower();sensitive=low==".env" or low.startswith(".env.") or p.suffix.lower() in PROTECTED or any(x in low for x in ("secret","credential","token"));model="models" in [x.lower() for x in p.parts];runtime=any(x.lower() in {"data","logs","cache","__pycache__"} for x in p.parts);backup=low.endswith(".backup");media=p.suffix.lower() in {".png",".jpg",".wav",".mp3",".mp4",".bin",".gguf"};allowed=not(sensitive or model or runtime or backup or media or p.is_absolute() or ".." in p.parts)
  return GitFileAssessment(safe_ref(ref),sensitive=sensitive,runtime_generated=runtime,model_file=model,media_file=media,backup_file=backup,allowed_to_stage=allowed,blocked_reason="protected_or_runtime_file" if not allowed else "")
 def _approved(self,operation,resources,approval):
  req=ToolExecutionRequest("git_write","git_executor","git",operation,ExecutionMode.APPROVED_EXECUTION,ExecutionRisk.HIGH,(ExecutionPermission.GIT_WRITE,),tuple(resources),approval,False);return req,self.broker.route(req).status=="approved_for_executor"
 def stage(self,files,approval):
  items=tuple(files);checks=[self.assess(x) for x in items]
  if not items or any(not x.allowed_to_stage for x in checks):return GitOperationResult(new_id(),"stage","blocked",error="explicit_safe_files_required")
  req,ok=self._approved("stage",tuple(safe_ref(x) for x in items),approval)
  if not ok:return GitOperationResult(req.request_id,"stage","approval_required",error="invalid_approval")
  p=self._git("add","--",*items);return GitOperationResult(req.request_id,"stage","completed" if p.returncode==0 else "failed",files_changed_count=len(items),error=bounded(p.stderr,160) or None)
 def unstage(self,files,approval):
  req,ok=self._approved("unstage",tuple(safe_ref(x) for x in files),approval)
  if not ok:return GitOperationResult(req.request_id,"unstage","approval_required")
  p=self._git("restore","--staged","--",*files);return GitOperationResult(req.request_id,"unstage","completed" if p.returncode==0 else "failed",error=bounded(p.stderr,160) or None)
 def _staged_safe(self):
  names=tuple(x for x in self._git("diff","--cached","--name-only").stdout.splitlines() if x)
  if not names or any(not self.assess(x).allowed_to_stage for x in names):return False,names
  diff=self._git("diff","--cached").stdout
  return not contains_secret(diff),names
 def commit(self,message,approval):
  safe,files=self._staged_safe()
  if not safe:return GitOperationResult(new_id(),"commit","blocked",error="protected_file_or_secret_detected")
  if not message.strip() or len(message)>120 or contains_secret(message) or re.search(r"[\x00-\x1f]",message):return GitOperationResult(new_id(),"commit","blocked",error="invalid_commit_message")
  resources=(self.branch(),message,*tuple(safe_ref(x) for x in files));req,ok=self._approved("commit",resources,approval)
  if not ok:return GitOperationResult(req.request_id,"commit","approval_required")
  p=self._git("commit","-m",message);ref=self._git("rev-parse","HEAD").stdout.strip() if p.returncode==0 else "";return GitOperationResult(req.request_id,"commit","completed" if ref else "failed",ref,files_changed_count=len(files),error=bounded(p.stderr,160) or None)
 def push(self,approval,remote="origin",branch=None):
  branch=branch or self.branch()
  if remote not in self.policy.allowed_remotes or branch not in self.policy.allowed_branches:return GitOperationResult(new_id(),"push","blocked",error="remote_or_branch_blocked")
  head=self._git("rev-parse","HEAD").stdout.strip();req,ok=self._approved("push",(remote,branch,head),approval)
  if not ok:return GitOperationResult(req.request_id,"push","approval_required")
  p=self._git("push",remote,branch);return GitOperationResult(req.request_id,"push","completed" if p.returncode==0 else "failed",head,"pushed" if p.returncode==0 else "remote_incomplete",f"{remote}/{branch}",error=bounded(p.stderr,200) or None)
