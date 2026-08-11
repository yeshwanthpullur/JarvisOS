"""Approval-gated outbound-only Discord, email, and Slack text connectors."""
from __future__ import annotations
import hashlib,os,re,time
from collections import deque
from dataclasses import dataclass,field
from enum import StrEnum
from jarvis.execution.broker import ExecutionBroker,ToolExecutionRequest
from jarvis.execution.models import ExecutionMode,ExecutionPermission,ExecutionRisk
from jarvis.foundation_common import bounded,new_id
from .security import classify_data
from .models import DataClassification

class ConnectorState(StrEnum):
 REGISTERED="registered";DISABLED="disabled";UNCONFIGURED="unconfigured";CREDENTIAL_MISSING="credential_missing";CONFIGURED="configured";AUTH_UNVERIFIED="auth_unverified";AUTHENTICATED="authenticated";REACHABLE="reachable";READY="ready";DEGRADED="degraded";RATE_LIMITED="rate_limited";BLOCKED="blocked";ERROR="error"
@dataclass(frozen=True,slots=True)
class ProviderMessageRequest:
 provider_id:str;destination_ref:str;body_preview:str;subject:str="";recipient_refs:tuple[str,...]=();formatting_mode:str="plain_text";attachment_refs:tuple[str,...]=();approval_id:str="";data_classification:DataClassification=DataClassification.PROJECT_INTERNAL;risk_level:str="high";request_id:str=field(default_factory=new_id)
@dataclass(frozen=True,slots=True)
class ConnectorPolicy:
 enabled:bool=False;allow_send:bool=False;allow_inbound:bool=False;allow_attachments:bool=False;allow_bulk:bool=False;allow_scheduled_send:bool=False;require_approval:bool=True;max_message_chars:int=4000;max_recipients:int=1;max_sends_per_window:int=3;rate_window_seconds:int=60;max_retries:int=1
@dataclass(frozen=True,slots=True)
class ConnectorResult:
 status:str;executed:bool=False;request_id:str=field(default_factory=new_id);external_ref:str="";error:str|None=None;warnings:tuple[str,...]=()

class OutboundConnector:
 def __init__(self,provider_id,credential_refs,*,policy=None,credential_getter=None,transport=None,broker=None,clock=None):
  self.provider_id=provider_id;self.credential_refs=tuple(credential_refs);self.policy=policy or ConnectorPolicy();self._get=credential_getter or (lambda key:os.environ.get(key,""));self.transport=transport;self.broker=broker or ExecutionBroker();self.clock=clock or time.time;self.history=deque(maxlen=50);self.fingerprints=deque(maxlen=100);self.send_times=deque(maxlen=100);self.health_verified=False
 def credential_present(self):return all(bool(self._get(x)) for x in self.credential_refs)
 def status(self):
  state=ConnectorState.DISABLED if not self.policy.enabled else ConnectorState.CREDENTIAL_MISSING if not self.credential_present() else ConnectorState.READY if self.health_verified else ConnectorState.AUTH_UNVERIFIED
  return {"provider":self.provider_id,"implemented":True,"state":state.value,"enabled":self.policy.enabled,"credential_present":self.credential_present(),"ready":state is ConnectorState.READY,"inbound":False,"attachments":False,"bulk":False,"scheduled":False}
 def validate_destination(self,value):
  value=value.strip()
  if self.provider_id.startswith("email"):ok=bool(re.fullmatch(r"[^@\s\r\n]+@[^@\s\r\n]+\.[^@\s\r\n]+",value))
  else:ok=bool(re.fullmatch(r"[A-Za-z0-9_-]{2,80}",value))
  return ok,hashlib.sha256(value.encode()).hexdigest()[:16] if ok else "invalid"
 def content_safe(self,body,subject=""):
  lower=body.lower();classification=classify_data(body)
  bad=classification in {DataClassification.SECRET,DataClassification.CREDENTIAL,DataClassification.RESTRICTED} or any(x in lower for x in ("@everyone","@here","bulk send","mass send","spam")) or any(x in subject for x in ("\r","\n"))
  return not bad,"policy_blocked" if bad else "allowed"
 def plan(self,destination,body,subject=""):
  valid,ref=self.validate_destination(destination);safe,reason=self.content_safe(body,subject);bounded_ok=bool(body.strip()) and len(body)<=self.policy.max_message_chars and len(subject)<=200
  return ProviderMessageRequest(self.provider_id,ref,bounded(body,400),bounded(subject,200),data_classification=classify_data(body)), valid and safe and bounded_ok, reason if not safe else "destination_invalid" if not valid else "message_too_large" if not bounded_ok else "approval_required"
 def health(self):
  if not self.credential_present():return ConnectorResult("unconfigured",error="credential_missing")
  if self.transport is None:return ConnectorResult("unverified",error="provider_unreachable")
  try:self.transport.health(self);self.health_verified=True;return ConnectorResult("authenticated",True)
  except Exception:return ConnectorResult("failed",error="authentication_failed")
 def send(self,destination,body,approval_id="",subject=""):
  request,allowed,reason=self.plan(destination,body,subject)
  if not self.policy.enabled or not self.policy.allow_send or not self.health_verified:return ConnectorResult("unavailable",error="provider_not_ready")
  if not allowed:return ConnectorResult("blocked",error=reason)
  fp=hashlib.sha256(f"{self.provider_id}:{request.destination_ref}:{subject}:{body}".encode()).hexdigest()
  if fp in self.fingerprints:return ConnectorResult("blocked",error="duplicate_blocked")
  now=self.clock();self.send_times=deque((x for x in self.send_times if now-x<self.policy.rate_window_seconds),maxlen=100)
  if len(self.send_times)>=self.policy.max_sends_per_window:return ConnectorResult("blocked",error="rate_limited")
  permission={"discord":ExecutionPermission.SEND_MESSAGE,"slack":ExecutionPermission.SEND_MESSAGE,"email_smtp":ExecutionPermission.SEND_EMAIL,"email_api":ExecutionPermission.SEND_EMAIL}[self.provider_id]
  action="email_send" if self.provider_id.startswith("email") else f"{self.provider_id}_send";tool="email_send_tool" if self.provider_id.startswith("email") else f"{self.provider_id}_send_tool"
  routed=self.broker.route(ToolExecutionRequest(action,tool,"communication",f"Send bounded {self.provider_id} text",ExecutionMode.APPROVED_EXECUTION,ExecutionRisk.HIGH,(permission,ExecutionPermission.NETWORK_ACCESS),(request.destination_ref,hashlib.sha256(f"{subject}:{body}".encode()).hexdigest()[:16]),approval_id,False))
  if routed.status!="approved_for_executor":return ConnectorResult("approval_required",error="approval_required")
  try:external=self.transport.send(self,destination,body,subject);self.fingerprints.append(fp);self.send_times.append(now);self.history.append({"provider":self.provider_id,"status":"completed","destination_ref":request.destination_ref});return ConnectorResult("completed",True,external_ref=str(external or ""))
  except Exception:return ConnectorResult("failed",error="provider_error")

def build_outbound_connectors(*,broker=None,transport=None,credential_getter=None):
 broker=broker or ExecutionBroker()
 return {pid:OutboundConnector(pid,refs,broker=broker,transport=transport,credential_getter=credential_getter) for pid,refs in {
  "discord":("DISCORD_BOT_TOKEN",),"email_smtp":("EMAIL_SMTP_HOST","EMAIL_SMTP_PORT","EMAIL_SMTP_USERNAME","EMAIL_SMTP_PASSWORD","EMAIL_FROM_ADDRESS"),"email_api":("EMAIL_API_TOKEN",),"slack":("SLACK_BOT_TOKEN",)
 }.items()}

def render_connector_command(command,args,connectors):
 namespace,op=command.split(maxsplit=1);pid="email_smtp" if namespace=="email" else namespace;c=connectors[pid]
 if op=="help":return f"{namespace} status|health|validate-destination|send-plan|send-dry-run|send|rate-status|history"
 if op in {"status","health"}:return f"{namespace.title()}: "+" ".join(f"{k}={str(v).lower() if isinstance(v,bool) else v}" for k,v in c.status().items())+" credential_value=hidden"
 if op in {"destinations","providers"}:return f"{namespace.title()} destinations: explicit_only enumeration=disabled aliases=local_only"
 if op in {"validate-destination","validate-address"}:ok,ref=c.validate_destination(args[0] if args else "");return f"{namespace.title()} destination: valid={str(ok).lower()} ref={ref}"
 if op in {"send-plan","send-dry-run"}:r,ok,reason=c.plan("planned", " ".join(args));return f"{namespace.title()} {op}: allowed={str(ok).lower()} approval_required=yes executed=no reason={reason}"
 if op=="send":return f"{namespace.title()} send: approval_required; exact provider, destination, content, permission, and expiry must pass the authoritative Broker. No message was sent."
 if op=="rate-status":return f"{namespace.title()} rate: sent_window={len(c.send_times)} limit={c.policy.max_sends_per_window}"
 if op=="history":return f"{namespace.title()} history: "+("; ".join(f"{x['provider']}:{x['status']}:{x['destination_ref']}" for x in c.history) or "none")
 return f"{namespace} help"
