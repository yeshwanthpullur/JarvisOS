from dataclasses import dataclass,field
from jarvis.foundation_common import new_id,now
@dataclass(frozen=True,slots=True)
class NotificationProvider:
 provider_id:str;display_name:str;platform:str;status:str;available:bool;local_only:bool=True;requires_external_service:bool=False;supported_features:tuple[str,...]=();unsupported_features:tuple[str,...]=();warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class NotificationPolicy:
 enabled:bool=True;local_only:bool=True;require_approval:bool=True;allow_external_notifications:bool=False;allow_action_buttons:bool=False;allow_command_actions:bool=False;max_title_chars:int=80;max_body_chars:int=500;max_notifications_per_window:int=5;rate_limit_window_seconds:int=300;redact_sensitive_values:bool=True;save_history:bool=True
@dataclass(frozen=True,slots=True)
class NotificationValidation:
 provider_available:bool;approval_valid:bool;content_safe:bool;rate_limit_allowed:bool;title_length_valid:bool;body_length_valid:bool;secret_content_detected:bool;blocked_reason:str="";validation_id:str=field(default_factory=new_id)
@dataclass(frozen=True,slots=True)
class NotificationResult:
 request_id:str;status:str;provider_id:str;displayed:bool;timestamp:str=field(default_factory=now);warnings:tuple[str,...]=();error:str|None=None
