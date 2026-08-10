"""Typed draft-only Communication Gateway models."""
from dataclasses import dataclass,field
from enum import StrEnum
from jarvis.foundation_common import new_id,now,validate_items,validate_request_text,validate_text
class CommunicationIntent(StrEnum): DRAFT_MESSAGE="draft_message";DRAFT_EMAIL="draft_email";DRAFT_NOTIFICATION="draft_notification";REMINDER_DELIVERY_PLAN="reminder_delivery_plan";REPORT_DELIVERY_PLAN="report_delivery_plan";PROVIDER_STATUS="provider_status";CONTACT_RESOLUTION_PLAN="contact_resolution_plan";MESSAGING_INTEGRATION_PLAN="messaging_integration_plan";SOCIAL_POST_PLAN="social_post_plan";BULK_MESSAGE_REQUEST="bulk_message_request";SEND_MESSAGE_REQUEST="send_message_request";UNSAFE_OR_ABUSIVE_REQUEST="unsafe_or_abusive_request";UNKNOWN="unknown"
class CommunicationRiskLevel(StrEnum):LOW="low";MEDIUM="medium";HIGH="high";CRITICAL="critical"
class CommunicationStatus(StrEnum):DRAFTED="drafted";PLANNED="planned";BLOCKED="blocked";UNAVAILABLE="unavailable"
class CommunicationProviderType(StrEnum):LOCAL_NOTIFICATION="local_notification";TELEGRAM="telegram";DISCORD="discord";EMAIL_SMTP="email_smtp";EMAIL_IMAP="email_imap";SLACK="slack";SOCIAL="social";UNKNOWN="unknown"
@dataclass(frozen=True,slots=True)
class CommunicationRequest:
 request:str;normalized_request:str;intent:CommunicationIntent=CommunicationIntent.UNKNOWN;scope:str="draft_only";risk_level:CommunicationRiskLevel=CommunicationRiskLevel.LOW;request_id:str=field(default_factory=new_id);created_at:str=field(default_factory=now)
 def __post_init__(self):validate_request_text(self.request);validate_request_text(self.normalized_request)
@dataclass(frozen=True,slots=True)
class CommunicationProvider:
 provider_id:str;display_name:str;provider_type:CommunicationProviderType;status:str="not_configured";configured:bool=False;send_available:bool=False;requires_credentials:bool=True;supported_actions:tuple[str,...]=("draft",);warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class RecipientReference:
 recipient_id:str;display_name:str;address_hint:str;recipient_type:str;verified:bool=False;requires_resolution:bool=True;warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class MessageDraft:
 channel:str;recipient_summary:str;subject:str;body_preview:str;full_body_available:bool=True;approval_required:bool=True;send_available:bool=False;warnings:tuple[str,...]=();draft_id:str=field(default_factory=new_id)
 def __post_init__(self):validate_text(self.body_preview);validate_text(self.subject,required=False)
@dataclass(frozen=True,slots=True)
class CommunicationPlan:
 request_id:str;intent:CommunicationIntent;summary:str;provider:CommunicationProvider|None;recipients:tuple[RecipientReference,...];draft:MessageDraft|None;proposed_steps:tuple[str,...];required_permissions:tuple[str,...]=();blocked_actions:tuple[str,...]=("send","bulk_send","contact_scrape","token_access");risk_level:CommunicationRiskLevel=CommunicationRiskLevel.LOW;approval_required:bool=True;status:CommunicationStatus=CommunicationStatus.PLANNED;warnings:tuple[str,...]=();plan_id:str=field(default_factory=new_id)
@dataclass(frozen=True,slots=True)
class CommunicationResult:
 request_id:str;status:CommunicationStatus;request:CommunicationRequest|None=None;plan:CommunicationPlan|None=None;providers:tuple[CommunicationProvider,...]=();draft:MessageDraft|None=None;output:str="";warnings:tuple[str,...]=();error:str|None=None
