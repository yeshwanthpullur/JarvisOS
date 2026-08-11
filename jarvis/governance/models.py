"""Bounded enterprise-governance models with no execution authority."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from jarvis.foundation_common import new_id, now, validate_items, validate_text


class IdentityType(StrEnum):
    USER="user"; AGENT="agent"; PROVIDER="provider"; PLUGIN="plugin"; MCP_SERVER="mcp_server"; RUNTIME="runtime"; WORKFLOW="workflow"; SERVICE="service"; EXTERNAL="future_external_identity"
class AuthenticationState(StrEnum): UNKNOWN="unknown"; VERIFIED="verified"; FAILED="failed"; EXPIRED="expired"
class AuthorizationState(StrEnum): UNKNOWN="unknown"; AUTHORIZED="authorized"; DENIED="denied"; RESTRICTED="restricted"
class TrustLevel(StrEnum): UNTRUSTED="untrusted"; LOW="low"; MEDIUM="medium"; HIGH="high"; REVOKED="revoked"
class PrivacyClass(StrEnum): PUBLIC="public"; INTERNAL="internal"; PROJECT="project"; PRIVATE="private"; RESTRICTED="restricted"; CONFIDENTIAL="confidential"
class GovernanceRisk(StrEnum): MINIMAL="minimal"; LOW="low"; MEDIUM="medium"; HIGH="high"; CRITICAL="critical"
class PolicyState(StrEnum): DRAFT="draft"; REVIEW="review"; APPROVED="approved"; ACTIVE="active"; DEPRECATED="deprecated"; DISABLED="disabled"; ARCHIVED="archived"
class ComplianceState(StrEnum): UNKNOWN="unknown"; COMPLIANT="compliant"; WARNING="warning"; NON_COMPLIANT="non_compliant"; MANUAL_REVIEW="manual_review"
class SecuritySeverity(StrEnum): INFORMATIONAL="informational"; WARNING="warning"; HIGH="high"; CRITICAL="critical"
class IncidentState(StrEnum): DETECTED="detected"; INVESTIGATING="investigating"; CONTAINED="contained"; RESOLVED="resolved"; CLOSED="closed"; MANUAL_REVIEW="manual_review"
class RetentionClass(StrEnum): SHORT_TERM="short_term"; STANDARD="standard"; LONG_TERM="long_term"; MANUAL="manual_retention"


@dataclass(frozen=True, slots=True)
class Identity:
    identity_id:str; identity_type:IdentityType; display_name:str; trust_level:TrustLevel=TrustLevel.UNTRUSTED; authentication_state:AuthenticationState=AuthenticationState.UNKNOWN; authorization_state:AuthorizationState=AuthorizationState.UNKNOWN; privacy_scope:PrivacyClass=PrivacyClass.PRIVATE; roles:tuple[str,...]=(); attributes:tuple[str,...]=(); created_at:str=field(default_factory=now); updated_at:str=field(default_factory=now)
    def __post_init__(self):
        validate_text(self.identity_id,limit=120);validate_text(self.display_name,limit=160);validate_items(self.roles);validate_items(self.attributes)
        if not isinstance(self.identity_type,IdentityType) or not isinstance(self.authentication_state,AuthenticationState) or not isinstance(self.authorization_state,AuthorizationState):raise ValueError("invalid_identity_state")


@dataclass(frozen=True, slots=True)
class Role:
    role_id:str; role_name:str; description:str; assigned_permissions:tuple[str,...]=(); restrictions:tuple[str,...]=()
    def __post_init__(self): validate_text(self.role_id,limit=120);validate_text(self.role_name,limit=120);validate_text(self.description,limit=400);validate_items(self.assigned_permissions);validate_items(self.restrictions)


@dataclass(frozen=True, slots=True)
class Policy:
    policy_id:str; policy_name:str; version:str; scope:str; owner:str; conditions:tuple[str,...]; actions:tuple[str,...]; priority:int=0; status:PolicyState=PolicyState.DRAFT; created_at:str=field(default_factory=now); activation_date:str=""; deprecation_date:str=""; compatibility:tuple[str,...]=()
    def __post_init__(self):
        for value in (self.policy_id,self.policy_name,self.version,self.scope,self.owner): validate_text(value,limit=160)
        validate_items(self.conditions);validate_items(self.actions)
        if not 0<=self.priority<=1000: raise ValueError("invalid_policy_priority")
        if any(not action.startswith(("allow:","deny:")) for action in self.actions):raise ValueError("unsupported_policy_action")


@dataclass(frozen=True, slots=True)
class IdentityChain:
    originating_identity:str; delegated_identities:tuple[str,...]; acting_component:str; effective_permissions:tuple[str,...]; effective_privacy_scope:PrivacyClass; effective_policy_set:tuple[str,...]; chain_id:str=field(default_factory=new_id); created_at:str=field(default_factory=now)
    def __post_init__(self): validate_items(self.delegated_identities);validate_items(self.effective_permissions);validate_items(self.effective_policy_set)


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    identity_id:str; operation:str; allowed:bool; effective_permissions:tuple[str,...]; reason:str; policy_references:tuple[str,...]=(); risk_level:GovernanceRisk=GovernanceRisk.LOW; approval_still_required:bool=False; decision_id:str=field(default_factory=new_id); created_at:str=field(default_factory=now)


@dataclass(frozen=True, slots=True)
class TrustScore:
    entity_id:str; entity_type:str; current_score:float; trust_level:TrustLevel; evaluation_time:str=field(default_factory=now); supporting_factors:tuple[str,...]=(); warnings:tuple[str,...]=()
    def __post_init__(self):
        if not 0<=self.current_score<=1: raise ValueError("invalid_trust_score")
        validate_items(self.supporting_factors);validate_items(self.warnings)


@dataclass(frozen=True, slots=True)
class AuditRecord:
    event_type:str; component:str; actor:str; target:str; result:str; severity:SecuritySeverity=SecuritySeverity.INFORMATIONAL; workflow_reference:str=""; session_reference:str=""; policy_reference:str=""; approval_reference:str=""; broker_reference:str=""; warnings:tuple[str,...]=(); retention:RetentionClass=RetentionClass.STANDARD; previous_digest:str=""; digest:str=""; audit_id:str=field(default_factory=new_id); timestamp:str=field(default_factory=now); schema_version:str="1.0"


@dataclass(frozen=True, slots=True)
class ComplianceResult:
    policy_set:tuple[str,...]; component:str; status:ComplianceState; violations:tuple[str,...]=(); warnings:tuple[str,...]=(); recommendations:tuple[str,...]=(); compliance_id:str=field(default_factory=new_id); timestamp:str=field(default_factory=now)


@dataclass(frozen=True, slots=True)
class SecurityEvent:
    event_type:str; component:str; severity:SecuritySeverity; summary:str; identity_id:str=""; workflow_id:str=""; policy_id:str=""; correlation_id:str=""; event_id:str=field(default_factory=new_id); created_at:str=field(default_factory=now)


@dataclass(frozen=True, slots=True)
class SecurityIncident:
    severity:SecuritySeverity; affected_components:tuple[str,...]; affected_workflows:tuple[str,...]; risk_level:GovernanceRisk; status:IncidentState=IncidentState.DETECTED; recommended_actions:tuple[str,...]=(); related_events:tuple[str,...]=(); incident_id:str=field(default_factory=new_id); detected_time:str=field(default_factory=now)


@dataclass(frozen=True, slots=True)
class GovernanceLimits:
    max_audit_records:int=500; max_security_events:int=200; max_policy_cache:int=100; max_trust_cache:int=100; max_incidents:int=100; max_search_results:int=25
    def __post_init__(self):
        if any(value<1 or value>5000 for value in (self.max_audit_records,self.max_security_events,self.max_policy_cache,self.max_trust_cache,self.max_incidents,self.max_search_results)): raise ValueError("invalid_governance_limits")
