"""Typed models for the read-only Browser Agent foundation."""
from dataclasses import dataclass, field
from enum import StrEnum
from jarvis.foundation_common import new_id, now, validate_items, validate_request_text, validate_text

class BrowserIntent(StrEnum):
    READ_WEBPAGE="read_webpage"; SUMMARIZE_WEBPAGE="summarize_webpage"; COMPARE_PAGES="compare_pages"; RESEARCH_WEB="research_web"; BROWSER_TASK_PLAN="browser_task_plan"; FORM_TASK_REQUEST="form_task_request"; LOGIN_TASK_REQUEST="login_task_request"; DOWNLOAD_TASK_REQUEST="download_task_request"; SCREENSHOT_TASK_REQUEST="screenshot_task_request"; BROWSER_AUTOMATION_REQUEST="browser_automation_request"; SHOPPING_OR_PURCHASE_REQUEST="shopping_or_purchase_request"; ACCOUNT_OR_MESSAGE_REQUEST="account_or_message_request"; UNSAFE_OR_PRIVATE_REQUEST="unsafe_or_private_request"; UNKNOWN="unknown"
class BrowserRiskLevel(StrEnum): LOW="low"; MEDIUM="medium"; HIGH="high"; CRITICAL="critical"
class BrowserStatus(StrEnum): PLANNED="planned"; READ_ONLY="read_only"; BLOCKED="blocked"; UNAVAILABLE="unavailable"; FAILED="failed"
@dataclass(frozen=True,slots=True)
class BrowserRequest:
 request:str; normalized_request:str; intent:BrowserIntent=BrowserIntent.UNKNOWN; scope:str="public_web"; risk_level:BrowserRiskLevel=BrowserRiskLevel.LOW; request_id:str=field(default_factory=new_id); created_at:str=field(default_factory=now)
 def __post_init__(self): validate_request_text(self.request); validate_request_text(self.normalized_request)
@dataclass(frozen=True,slots=True)
class BrowserCapabilityStatus:
 read_only_web_available:bool=True; interactive_browser_available:bool=False; screenshots_available:bool=False; form_submission_allowed:bool=False; login_allowed:bool=False; downloads_allowed:bool=False; cookies_allowed:bool=False; external_browser_automation_available:bool=False; warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class BrowserSource:
 source_id:str; source_type:str; url_or_ref:str; title:str; allowed:bool; reason:str; retrieved:bool=False; warnings:tuple[str,...]=()
 def __post_init__(self): validate_text(self.url_or_ref); validate_text(self.title,required=False); validate_items(self.warnings)
@dataclass(frozen=True,slots=True)
class BrowserPlan:
 request_id:str; intent:BrowserIntent; summary:str; proposed_steps:tuple[str,...]; allowed_actions:tuple[str,...]=("read_public_page","summarize_supplied_evidence"); blocked_actions:tuple[str,...]=("login","submit_form","purchase","browser_write","cookies"); required_permissions:tuple[str,...]=("browser_read",); needs_web_read:bool=True; needs_interactive_browser:bool=False; risk_level:BrowserRiskLevel=BrowserRiskLevel.LOW; approval_required:bool=False; status:BrowserStatus=BrowserStatus.PLANNED; warnings:tuple[str,...]=(); plan_id:str=field(default_factory=new_id)
 def __post_init__(self): validate_text(self.summary); validate_items(self.proposed_steps); validate_items(self.warnings)
@dataclass(frozen=True,slots=True)
class BrowserResult:
 request_id:str; status:BrowserStatus; request:BrowserRequest|None=None; plan:BrowserPlan|None=None; capability_status:BrowserCapabilityStatus|None=None; sources:tuple[BrowserSource,...]=(); output:str=""; warnings:tuple[str,...]=(); error:str|None=None
 def __post_init__(self): validate_text(self.output,required=False); validate_items(self.sources); validate_items(self.warnings)
