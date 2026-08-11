"""Bounded Telegram connector models with no credential or message persistence."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from jarvis.foundation_common import new_id, now


class TelegramState(StrEnum):
    REGISTERED="registered"; DISABLED="disabled"; UNCONFIGURED="unconfigured"; CREDENTIAL_MISSING="credential_missing"; CONFIGURED="configured"; AUTH_UNVERIFIED="auth_unverified"; AUTHENTICATED="authenticated"; REACHABLE="reachable"; READY="ready"; DEGRADED="degraded"; RATE_LIMITED="rate_limited"; BLOCKED="blocked"; ERROR="error"

class TelegramError(StrEnum):
    CREDENTIAL_MISSING="credential_missing"; AUTHENTICATION_FAILED="authentication_failed"; AUTHORIZATION_FAILED="authorization_failed"; DESTINATION_INVALID="destination_invalid"; RATE_LIMITED="rate_limited"; NETWORK_TIMEOUT="network_timeout"; NETWORK_UNREACHABLE="network_unreachable"; PROVIDER_ERROR="provider_error"; MESSAGE_TOO_LARGE="message_too_large"; UNSUPPORTED_UPDATE="unsupported_update"; POLICY_BLOCKED="policy_blocked"; APPROVAL_REQUIRED="approval_required"; APPROVAL_INVALID="approval_invalid"; INTERNAL_ERROR="internal_error"

@dataclass(frozen=True, slots=True)
class TelegramBotIdentity:
    bot_id:str=""; username:str=""; display_name:str=""; verified:bool=False; checked_at:str=field(default_factory=now); warnings:tuple[str,...]=()

@dataclass(frozen=True, slots=True)
class TelegramChatAuthorization:
    chat_id_ref:str; user_id_ref:str; chat_type:str="private"; authorized:bool=True; permission_scope:tuple[str,...]=("conversation",); created_at:str=field(default_factory=now); expires_at:str=""; warnings:tuple[str,...]=()

@dataclass(slots=True)
class TelegramPairingRequest:
    code_fingerprint:str; expires_at_epoch:float; pairing_id:str=field(default_factory=new_id); created_at:str=field(default_factory=now); used:bool=False; allowed_chat_type:str="private"; warnings:tuple[str,...]=()

@dataclass(frozen=True, slots=True)
class TelegramInboundMessage:
    update_id:int; message_id:int; chat_ref:str; user_ref:str; chat_type:str; timestamp:int; text:str; command:str=""; reply_to_ref:str=""; authorized:bool=False; warnings:tuple[str,...]=()

@dataclass(frozen=True, slots=True)
class TelegramSendPlan:
    destination_ref:str; message_preview:str; chunks:int; direct_reply:bool; approval_required:bool; policy_allowed:bool; request_id:str=field(default_factory=new_id); warnings:tuple[str,...]=()

@dataclass(frozen=True, slots=True)
class TelegramResult:
    status:str; executed:bool=False; request_id:str=field(default_factory=new_id); external_ref:str=""; warnings:tuple[str,...]=(); error:str|None=None

