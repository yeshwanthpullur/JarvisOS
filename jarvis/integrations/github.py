"""Repository-scoped GitHub service provider; local Git remains authoritative."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from collections import deque
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from jarvis.execution.broker import ExecutionBroker, ToolExecutionRequest
from jarvis.execution.models import ExecutionMode, ExecutionPermission, ExecutionRisk
from jarvis.foundation_common import bounded, new_id
from .models import DataClassification
from .security import classify_data, redact


class GitHubState(StrEnum):
    REGISTERED="registered"; DISABLED="disabled"; UNCONFIGURED="unconfigured"; CREDENTIAL_MISSING="credential_missing"; AUTH_UNVERIFIED="auth_unverified"; AUTHENTICATED="authenticated"; READY="ready"; DEGRADED="degraded"; RATE_LIMITED="rate_limited"; BLOCKED="blocked"; ERROR="error"


@dataclass(frozen=True, slots=True)
class GitHubPolicy:
    enabled:bool=False; transport:str="gh_cli"; allow_read:bool=True; allow_issue_write:bool=False; allow_pr_write:bool=False; allow_release_write:bool=False; allow_merge:bool=False; allow_workflow_execute:bool=False; allow_admin:bool=False; require_approval_for_writes:bool=True; allowed_repositories:tuple[str,...]=("yeshwanthpullur/JarvisOS",); max_results:int=20; max_body_chars:int=4000; max_retries:int=1; health_cache_seconds:int=60; save_history:bool=True; redact_sensitive_values:bool=True


@dataclass(frozen=True, slots=True)
class GitHubIssuePlan:
    repository:str; title:str; body_summary:str; labels:tuple[str,...]=(); assignee_refs:tuple[str,...]=(); approval_required:bool=True; risk:str="high"; warnings:tuple[str,...]=()


@dataclass(frozen=True, slots=True)
class GitHubPullRequestPlan:
    repository:str; base:str; head:str; title:str; body_summary:str; approval_required:bool=True; risk:str="high"; warnings:tuple[str,...]=()


@dataclass(frozen=True, slots=True)
class GitHubReleasePlan:
    repository:str; tag:str; title:str; notes_summary:str; prerelease:bool=True; draft:bool=True; approval_required:bool=True; risk:str="high"; warnings:tuple[str,...]=()


@dataclass(frozen=True, slots=True)
class GitHubResult:
    status:str; executed:bool=False; items:tuple[dict[str,Any],...]=(); external_ref:str=""; error:str|None=None; warnings:tuple[str,...]=(); request_id:str=field(default_factory=new_id)


class GhCliTransport:
    """Structured gh invocation with fixed commands, bounded output, and no shell."""
    def __init__(self, timeout:int=12, max_output:int=64_000): self.timeout=timeout; self.max_output=max_output
    def available(self)->bool:return shutil.which("gh") is not None
    def _run(self,args:list[str])->Any:
        proc=subprocess.run(["gh",*args],capture_output=True,text=True,timeout=self.timeout,shell=False,check=False)
        text=(proc.stdout or "")[:self.max_output]
        if proc.returncode: raise RuntimeError("github_cli_failed")
        return json.loads(text) if text.strip() else {}
    def auth_status(self)->bool:
        if not self.available():return False
        proc=subprocess.run(["gh","auth","status"],capture_output=True,text=True,timeout=self.timeout,shell=False,check=False)
        return proc.returncode==0
    def read(self,repository:str,resource:str,identifier:str="",limit:int=20)->Any:
        paths={"repo":f"repos/{repository}","issues":f"repos/{repository}/issues?per_page={limit}","prs":f"repos/{repository}/pulls?per_page={limit}","releases":f"repos/{repository}/releases?per_page={limit}","workflows":f"repos/{repository}/actions/runs?per_page={limit}","checks":f"repos/{repository}/commits/{identifier or 'HEAD'}/check-runs"}
        if resource in {"issue","pr","release"}:
            segment={"issue":"issues","pr":"pulls","release":"releases"}[resource];paths[resource]=f"repos/{repository}/{segment}/{identifier}"
        if resource not in paths:raise ValueError("unsupported_github_read")
        return self._run(["api",paths[resource]])
    def mutate(self,repository:str,action:str,payload:dict[str,Any])->Any:
        endpoints={"issue_create":f"repos/{repository}/issues","issue_comment":f"repos/{repository}/issues/{payload.get('target','')}/comments","pr_create":f"repos/{repository}/pulls","pr_comment":f"repos/{repository}/issues/{payload.get('target','')}/comments","release_create":f"repos/{repository}/releases"}
        if action not in endpoints:raise ValueError("github_mutation_blocked")
        args=["api","--method","POST",endpoints[action]]
        for key,value in payload.items():
            if key!="target":args.extend(["-f",f"{key}={value}"])
        return self._run(args)


class GitHubProvider:
    WRITE_TOOLS={"issue_create":"github_issue_create_tool","issue_comment":"github_issue_comment_tool","pr_create":"github_pr_create_tool","pr_comment":"github_pr_comment_tool","release_create":"github_release_create_tool"}
    WRITE_PERMISSIONS={"issue_create":ExecutionPermission.GITHUB_ISSUE_WRITE,"issue_comment":ExecutionPermission.GITHUB_ISSUE_WRITE,"pr_create":ExecutionPermission.GITHUB_PR_WRITE,"pr_comment":ExecutionPermission.GITHUB_PR_WRITE,"release_create":ExecutionPermission.GITHUB_RELEASE_WRITE}
    def __init__(self,*,policy:GitHubPolicy|None=None,transport:Any=None,broker:ExecutionBroker|None=None,clock=None):
        self.policy=policy or GitHubPolicy();self.transport=transport or GhCliTransport();self.broker=broker or ExecutionBroker();self.clock=clock or time.time;self.authenticated=False;self.repository_accessible=False;self.rate_limited=False;self.history=deque(maxlen=50);self.fingerprints=deque(maxlen=100)
    def _allowed(self,repository:str)->bool:return repository.lower() in {x.lower() for x in self.policy.allowed_repositories}
    def status(self)->dict[str,Any]:
        cli=bool(getattr(self.transport,"available",lambda:True)());state=GitHubState.DISABLED if not self.policy.enabled else GitHubState.UNCONFIGURED if not cli and not os.environ.get("GITHUB_TOKEN") else GitHubState.RATE_LIMITED if self.rate_limited else GitHubState.READY if self.authenticated and self.repository_accessible else GitHubState.AUTH_UNVERIFIED
        return {"implemented":True,"state":state.value,"enabled":self.policy.enabled,"git_remote_configured":True,"gh_cli_available":cli,"gh_authenticated":self.authenticated,"api_authenticated":self.authenticated,"repository_accessible":self.repository_accessible,"provider_ready":state is GitHubState.READY,"repository_scope":",".join(self.policy.allowed_repositories),"read":self.policy.allow_read,"issue_write":self.policy.allow_issue_write,"pr_write":self.policy.allow_pr_write,"release_write":self.policy.allow_release_write,"merge":False,"workflow_execute":False,"admin":False}
    def health(self,repository:str="yeshwanthpullur/JarvisOS")->GitHubResult:
        if not self.policy.enabled:return GitHubResult("disabled",error="provider_disabled")
        if not self._allowed(repository):return GitHubResult("blocked",error="repository_not_allowed")
        try:
            self.authenticated=bool(self.transport.auth_status())
            if not self.authenticated:return GitHubResult("unconfigured",error="authentication_unverified")
            self.transport.read(repository,"repo",limit=1);self.repository_accessible=True;return GitHubResult("ready",True)
        except Exception:self.repository_accessible=False;return GitHubResult("degraded",error="github_unreachable_or_unauthorized")
    def read(self,resource:str,repository:str="yeshwanthpullur/JarvisOS",identifier:str="")->GitHubResult:
        if not self.policy.enabled or not self.policy.allow_read:return GitHubResult("unavailable",error="github_read_disabled")
        if not self._allowed(repository):return GitHubResult("blocked",error="repository_not_allowed")
        if not self.authenticated:return GitHubResult("unavailable",error="authentication_unverified")
        try:
            raw=self.transport.read(repository,resource,identifier,self.policy.max_results);values=raw.get("workflow_runs",[]) if isinstance(raw,dict) and "workflow_runs" in raw else raw if isinstance(raw,list) else [raw]
            items=tuple(self._safe_item(x) for x in values[:self.policy.max_results] if isinstance(x,dict));self._audit("read",resource,repository,"completed");return GitHubResult("completed",True,items)
        except Exception:return GitHubResult("failed",error="github_read_failed")
    def plan_issue(self,title:str,body:str,repository:str="yeshwanthpullur/JarvisOS")->GitHubIssuePlan:
        safe,warning=self._content_safe(title+"\n"+body);return GitHubIssuePlan(repository,bounded(title,200),bounded(body,400),warnings=(() if safe else (warning,)))
    def mutate(self,action:str,repository:str,payload:dict[str,Any],approval_id:str="")->GitHubResult:
        flag={"issue_create":self.policy.allow_issue_write,"issue_comment":self.policy.allow_issue_write,"pr_create":self.policy.allow_pr_write,"pr_comment":self.policy.allow_pr_write,"release_create":self.policy.allow_release_write}.get(action,False)
        if not self.policy.enabled or not flag or not self.authenticated:return GitHubResult("unavailable",error="github_write_disabled_or_unverified")
        if not self._allowed(repository):return GitHubResult("blocked",error="repository_not_allowed")
        serialized=json.dumps(payload,sort_keys=True);safe,reason=self._content_safe(serialized)
        if not safe:return GitHubResult("blocked",error=reason)
        fingerprint=hashlib.sha256(f"{repository}:{action}:{serialized}".encode()).hexdigest()[:20]
        if fingerprint in self.fingerprints:return GitHubResult("blocked",error="duplicate_blocked")
        permission=self.WRITE_PERMISSIONS[action];request=ToolExecutionRequest(f"github_{action}",self.WRITE_TOOLS[action],"github",f"Approved GitHub {action}",ExecutionMode.APPROVED_EXECUTION,ExecutionRisk.HIGH,(permission,ExecutionPermission.NETWORK_ACCESS),(repository,fingerprint),approval_id,False)
        routed=self.broker.route(request)
        if routed.status!="approved_for_executor":return GitHubResult("approval_required",error="approval_required")
        try:
            raw=self.transport.mutate(repository,action,payload) or {};ref=str(raw.get("html_url") or raw.get("id") or "");self.fingerprints.append(fingerprint);self._audit("write",action,repository,"completed");return GitHubResult("completed",True,external_ref=bounded(ref,300))
        except Exception:return GitHubResult("failed",error="github_mutation_failed")
    def _content_safe(self,text:str)->tuple[bool,str]:
        classification=classify_data(text)
        if classification in {DataClassification.SECRET,DataClassification.CREDENTIAL,DataClassification.RESTRICTED}:return False,"data_egress_blocked"
        if re_private_path(text):return False,"private_path_blocked"
        return True,"allowed"
    def _safe_item(self,item:dict[str,Any])->dict[str,Any]:
        allowed=("id","number","name","full_name","title","state","default_branch","tag_name","html_url","conclusion","status","head","base")
        return {key:bounded(redact(str(item[key])),500) for key in allowed if key in item and item[key] is not None}
    def _audit(self,kind,action,repository,status):self.history.append({"kind":kind,"action":action,"repository":repository,"status":status})


def re_private_path(text:str)->bool:
    lowered=text.lower().replace("\\\\","\\");return "c:\\users\\" in lowered or "/home/" in lowered or "/users/" in lowered or ".env" in lowered


def render_github_command(command:str,args:list[str],runtime:GitHubProvider)->str:
    op=command.split(maxsplit=1)[1];repo=runtime.policy.allowed_repositories[0]
    if op=="help":return "GitHub: status|auth-status|health|repo|capabilities|rate-status|issues|issue-show|issue-plan|issue-create|prs|pr-show|pr-plan|pr-create|releases|release-show|release-plan|release-create|workflows|checks|history"
    if op in {"status","auth-status","health","repo","capabilities","rate-status"}:
        s=runtime.status();return "GitHub: "+" ".join(f"{k}={str(v).lower() if isinstance(v,bool) else v}" for k,v in s.items())+" credential_value=hidden"
    if op in {"issues","prs","releases","workflows","checks"}:
        resource={"issues":"issues","prs":"prs","releases":"releases","workflows":"workflows","checks":"checks"}[op];result=runtime.read(resource,repo);return f"GitHub {op}: status={result.status} count={len(result.items)} error={result.error or 'none'}"
    if op in {"issue-show","pr-show","release-show"}:
        resource={"issue-show":"issue","pr-show":"pr","release-show":"release"}[op];result=runtime.read(resource,repo,args[0] if args else "");return f"GitHub {op}: status={result.status} count={len(result.items)} error={result.error or 'none'}"
    if op.endswith("-plan"):
        return f"GitHub {op}: repository={repo} approval_required=yes executed=no content_scan=required"
    if op.endswith("-create"):
        return f"GitHub {op}: approval_required; repository, action, target, content fingerprint, permissions, and expiry must match. No mutation occurred."
    if op=="history":return "GitHub history: "+("; ".join(f"{x['kind']}:{x['action']}:{x['status']}" for x in runtime.history) or "none")
    return "github help"
