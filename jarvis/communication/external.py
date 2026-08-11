"""Provider-neutral, non-sending external communication foundation."""
from __future__ import annotations
import hashlib,re
from collections import deque
from dataclasses import dataclass,field
from enum import StrEnum
from pathlib import Path
from jarvis.foundation_common import new_id,now,bounded
from jarvis.integrations import ExternalIntegrationControlPlane,classify_data,redact
from jarvis.integrations.models import DataClassification

class CommunicationProviderState(StrEnum):
 REGISTERED="registered";ENABLED="enabled";CONFIGURED="configured";CREDENTIAL_MISSING="credential_missing";CREDENTIAL_AVAILABLE="credential_available";AUTH_UNVERIFIED="auth_unverified";AUTHENTICATED="authenticated";REACHABLE="reachable";READY="ready";DEGRADED="degraded";RATE_LIMITED="rate_limited";BLOCKED="blocked";DISABLED="disabled";UNAVAILABLE="unavailable"
@dataclass(frozen=True,slots=True)
class CommunicationProviderProfile:
 provider_id:str;display_name:str;provider_type:str;state:CommunicationProviderState=CommunicationProviderState.DISABLED;enabled:bool=False;configured:bool=False;authenticated:bool=False;reachable:bool=False;ready:bool=False;local_or_remote:str="remote";requires_credentials:bool=True;credential_refs:tuple[str,...]=();supported_actions:tuple[str,...]=("provider_status","message_draft","destination_validate");unsupported_actions:tuple[str,...]=("message_send","attachment_send","bulk_send","scheduled_send");permissions:tuple[str,...]=();risk_level:str="high";rate_limit_state:str="available";health_status:str="not_checked";limitations:tuple[str,...]=();warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class CommunicationDestination:
 destination_id:str;provider_id:str;destination_type:str;display_name:str;safe_identifier:str;verified:bool=False;requires_resolution:bool=True;writable:bool=False;warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class CommunicationAttachment:
 attachment_id:str;safe_file_ref:str;display_name:str;content_type:str;size_category:str;sensitive:bool;allowed:bool;blocked_reason:str="";warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class ExternalMessageRequest:
 provider_id:str;destination:CommunicationDestination|None;message_type:str="text";subject:str="";body_preview:str="";attachment_refs:tuple[str,...]=();approval_id:str|None=None;risk_level:str="high";request_id:str=field(default_factory=new_id);created_at:str=field(default_factory=now);warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class ExternalMessagePlan:
 request_id:str;provider_id:str;destination_summary:str;message_summary:str;attachments_summary:str;required_permissions:tuple[str,...];data_egress_classification:DataClassification;approval_required:bool=True;provider_ready:bool=False;risk_level:str="high";proposed_steps:tuple[str,...]=();blocked_actions:tuple[str,...]=("send","bulk_send","scheduled_send");warnings:tuple[str,...]=();plan_id:str=field(default_factory=new_id)
@dataclass(frozen=True,slots=True)
class ExternalMessageValidation:
 provider_ready:bool;credential_state_valid:bool;auth_valid:bool;destination_valid:bool;content_safe:bool;attachment_safe:bool;approval_valid:bool;rate_limit_allowed:bool;policy_allowed:bool;blocked_reason:str="";warnings:tuple[str,...]=();validation_id:str=field(default_factory=new_id)
@dataclass(frozen=True,slots=True)
class ExternalMessageResult:
 request_id:str;provider_id:str;status:str;destination_summary:str;external_reference:str="";delivered:bool=False;duration_ms:int=0;warnings:tuple[str,...]=();error:str|None=None
@dataclass(frozen=True,slots=True)
class CommunicationProviderPolicy:
 provider_id:str;enabled:bool=False;allow_read:bool=False;allow_send:bool=False;allow_attachments:bool=False;allow_group_send:bool=False;allow_bulk_send:bool=False;allow_scheduled_send:bool=False;require_approval:bool=True;max_message_chars:int=4000;max_attachments:int=0;allowed_attachment_types:tuple[str,...]=();rate_limits:tuple[int,int]=(3,60);warnings:tuple[str,...]=()

def default_profiles(plane=None):
 plane=plane or ExternalIntegrationControlPlane();items=[]
 for pid,name,kind,local in (("manual_copy","Manual copy","manual",True),("local_notification","Local notification","local_notification",True),("provider_stub","Provider stub","stub",True),("telegram","Telegram","telegram",False),("discord","Discord","discord",False),("email_smtp","Email SMTP","email",False),("email_api","Email API","email",False),("slack","Slack","slack",False),("matrix","Matrix","matrix",False),("whatsapp","WhatsApp","future",False),("sms","SMS","future",False),("social_media","Social media","future",False),("custom_webhook","Custom webhook","future",False)):
  central=plane.registry.get(pid);refs=central.credential_refs if central else ();state=CommunicationProviderState.DISABLED if kind!="future" else CommunicationProviderState.UNAVAILABLE
  items.append(CommunicationProviderProfile(pid,name,kind,state,local_or_remote="local" if local else "remote",requires_credentials=not local,credential_refs=refs,permissions=(f"{kind}_send" if kind not in {"manual","stub","future"} else "communication_send",),limitations=("External sending is unavailable in Prompt 72.",)))
 return tuple(items)
class CommunicationProviderAdapter:
 def status(self):raise NotImplementedError
 def capabilities(self):raise NotImplementedError
 def health_check(self):raise NotImplementedError
 def validate_destination(self,destination):raise NotImplementedError
 def validate_message(self,request):raise NotImplementedError
 def dry_run_send(self,request):raise NotImplementedError
 def send(self,request):raise RuntimeError("broker_required_and_provider_unavailable")
class ExternalCommunicationFoundation:
 def __init__(self,plane=None,max_history=50):self.plane=plane or ExternalIntegrationControlPlane();self.profiles=default_profiles(self.plane);self.history=deque(maxlen=max_history);self.fingerprints=deque(maxlen=50)
 def profile(self,pid):return next((x for x in self.profiles if x.provider_id==pid),None)
 def validate_destination(self,pid,value):
  value=value.strip();kind="email_address" if pid.startswith("email") else "chat"
  valid=bool(value) and (not pid.startswith("email") or bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+",value))) and len(value)<=160
  safe=(value[:2]+"..."+value[-2:]) if len(value)>5 else value
  return CommunicationDestination(hashlib.sha256(f"{pid}:{value}".encode()).hexdigest()[:16],pid,kind,"explicit destination",safe,valid,not valid,False if not valid else True,() if valid else("Malformed or missing destination.",))
 def check_attachment(self,file_ref):
  name=Path(file_ref).name;lower=name.lower();blocked=lower==".env" or any(x in lower for x in ("key","credential","token","cookie","database",".db","model"));suffix=Path(name).suffix.lower();supported=suffix in {".txt",".md",".pdf",".png",".jpg",".jpeg"}
  allowed=False
  return CommunicationAttachment(new_id(),name,name,suffix or "unknown","unknown",blocked,allowed,"sensitive_file" if blocked else "attachments_disabled" if supported else "unsupported_type")
 def safety(self,text):
  classification=classify_data(text);lower=text.lower();bulk=any(x in lower for x in ("500 people","bulk","spam","mass send"));secret=classification in {DataClassification.SECRET,DataClassification.CREDENTIAL,DataClassification.RESTRICTED};return classification,not(bulk or secret),"bulk_send_blocked" if bulk else "secret_egress_blocked" if secret else "allowed"
 def plan(self,text,provider_id="telegram",destination_text=""):
  profile=self.profile(provider_id);destination=self.validate_destination(provider_id,destination_text);classification,safe,reason=self.safety(text);preview=redact(bounded(text,400));fp=hashlib.sha256(f"{provider_id}:{destination.safe_identifier}:{preview}".encode()).hexdigest();duplicate=fp in self.fingerprints
  ready=bool(profile and profile.ready);validation=ExternalMessageValidation(ready,False,False,destination.verified,safe,True,False,not duplicate,False,reason if not safe else "duplicate_blocked" if duplicate else "provider_unavailable")
  plan=ExternalMessagePlan(new_id(),provider_id,destination.safe_identifier or "missing",preview,"none",(f"{provider_id}_send","communication_send","network_access"),classification,provider_ready=ready,proposed_steps=("Validate explicit destination.","Classify content and attachments.","Require exact Phase 4 approval.","Route a future send through Broker only."),warnings=(validation.blocked_reason,))
  self.history.append({"id":plan.plan_id,"provider":provider_id,"status":"blocked","reason":validation.blocked_reason});return plan,validation
 def rate_status(self,pid):return {"provider":pid,"count":0,"limit":3,"window_seconds":60,"rate_limited":False}
