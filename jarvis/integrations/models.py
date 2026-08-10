"""Bounded models for the external integration control plane."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import uuid4


class ProviderState(StrEnum):
    REGISTERED="registered"; DISABLED="disabled"; ENABLED="enabled"; UNCONFIGURED="unconfigured"; CONFIGURED="configured"; CREDENTIAL_MISSING="credential_missing"; CREDENTIAL_AVAILABLE="credential_available"; AUTHENTICATION_UNVERIFIED="authentication_unverified"; AUTHENTICATED="authenticated"; UNREACHABLE="unreachable"; REACHABLE="reachable"; DEGRADED="degraded"; READY="ready"; RATE_LIMITED="rate_limited"; ERROR="error"; BLOCKED="blocked"
class ProviderCategory(StrEnum):
    COMMUNICATION="communication"; DEVELOPER="developer"; MODEL="model"; TOOLING="tooling"
class ProviderRisk(StrEnum): LOW="low"; MEDIUM="medium"; HIGH="high"; CRITICAL="critical"
class CostClass(StrEnum): FREE_LOCAL="free_local"; FREE_REMOTE="free_remote"; METERED="metered"; PAID="paid"; UNKNOWN="unknown"
class DataClassification(StrEnum): PUBLIC="public"; PROJECT_INTERNAL="project_internal"; PERSONAL="personal"; SENSITIVE="sensitive"; SECRET="secret"; CREDENTIAL="credential"; RESTRICTED="restricted"

@dataclass(frozen=True, slots=True)
class ProviderCapability:
    name:str; description:str; permissions:tuple[str,...]=(); side_effects:tuple[str,...]=(); risk:ProviderRisk=ProviderRisk.LOW; requires_approval:bool=False; data_classes:tuple[DataClassification,...]=(DataClassification.PUBLIC,)

@dataclass(frozen=True, slots=True)
class ProviderHealth:
    state:ProviderState; checked_at:str="not_checked"; latency_ms:int|None=None; reason:str="Health check not performed."; cached:bool=True

@dataclass(frozen=True, slots=True)
class ProviderPolicy:
    local_only:bool=True; network_allowed:bool=False; paid_allowed:bool=False; execution_allowed:bool=False; approval_required:bool=True; max_retries:int=1; health_cache_seconds:int=60; allowed_data_classes:tuple[DataClassification,...]=(DataClassification.PUBLIC,)

@dataclass(frozen=True, slots=True)
class ExternalProvider:
    provider_id:str; display_name:str; category:ProviderCategory; capabilities:tuple[ProviderCapability,...]; state:ProviderState=ProviderState.DISABLED; enabled:bool=False; configured:bool=False; credential_refs:tuple[str,...]=(); local:bool=False; endpoint:str|None=None; cost_class:CostClass=CostClass.UNKNOWN; policy:ProviderPolicy=field(default_factory=ProviderPolicy); health:ProviderHealth=field(default_factory=lambda:ProviderHealth(ProviderState.UNCONFIGURED)); reason:str="Not configured."; limitations:tuple[str,...]=()

@dataclass(frozen=True, slots=True)
class ExternalActionRequest:
    provider_id:str; capability:str; data_classification:DataClassification=DataClassification.PROJECT_INTERNAL; permissions:tuple[str,...]=(); approval_id:str|None=None; request_id:str=field(default_factory=lambda:uuid4().hex); payload_preview:str=""

@dataclass(frozen=True, slots=True)
class ExternalActionResult:
    request_id:str; provider_id:str; status:str; executed:bool=False; reason:str=""; warnings:tuple[str,...]=(); metadata:dict[str,object]=field(default_factory=dict)

@dataclass(frozen=True, slots=True)
class ProviderRoute:
    capability:str; provider_id:str|None; status:str; reason:str; approval_required:bool; data_egress:DataClassification; fallbacks:tuple[str,...]=()
