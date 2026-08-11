"""Fail-closed, metadata-only enterprise governance runtime."""
from __future__ import annotations

from collections import Counter, deque
from dataclasses import replace
from hashlib import sha256
import re

from jarvis.foundation_common import bounded, contains_secret, safe_ref
from .models import *


PRIVILEGED_PREFIXES=("write","execute","send","deploy","modify","delete","invoke","navigate","resume","pause")
POLICY_PRECEDENCE=("security","execution","approval","workflow","runtime","provider")
SENSITIVE_VALUE_RE=re.compile(r"(?i)(api[_-]?key|access[_-]?token|token|password|authorization|credential|secret)\s*[:=]\s*\S+")


def _clean(value:object,limit:int=300)->str:
    text=bounded(value,limit)
    if contains_secret(text) or SENSITIVE_VALUE_RE.search(text): return "[REDACTED]"
    return safe_ref(text)


class GovernanceRuntime:
    """Coordinates governance metadata; never executes or approves an operation."""
    def __init__(self,limits:GovernanceLimits|None=None):
        self.limits=limits or GovernanceLimits()
        self.identities:dict[str,Identity]={};self.roles:dict[str,Role]={};self.policies:dict[str,Policy]={};self.trust:dict[str,TrustScore]={}
        self.audit_records=deque(maxlen=self.limits.max_audit_records);self.security_events=deque(maxlen=self.limits.max_security_events);self.incidents=deque(maxlen=self.limits.max_incidents)
        self.metrics=Counter();self.zero_trust_enabled=True;self.automatic_permission_escalation=False;self.automatic_policy_override=False;self.execution_authority=False

    def register_identity(self,identity:Identity)->Identity:
        if identity.identity_id in self.identities: raise ValueError("duplicate_identity")
        self.identities[identity.identity_id]=identity;self._audit("identity_registered","governance","system",identity.identity_id,"recorded");return identity

    def register_role(self,role:Role)->Role:
        if role.role_id in self.roles: raise ValueError("duplicate_role")
        self.roles[role.role_id]=role;return role

    def register_policy(self,policy:Policy)->Policy:
        if policy.policy_id in self.policies: raise ValueError("duplicate_policy")
        self.policies[policy.policy_id]=policy
        try:self.validate_policies()
        except ValueError:
            self.policies.pop(policy.policy_id,None);raise
        self._audit("policy_change","governance",policy.owner,policy.policy_id,"registered",policy_reference=policy.policy_id);return policy

    def validate_policies(self)->dict[str,object]:
        conflicts=[];active=[p for p in self.policies.values() if p.status is PolicyState.ACTIVE]
        for i,left in enumerate(active):
            for right in active[i+1:]:
                if left.scope==right.scope and left.priority==right.priority and set(left.conditions)==set(right.conditions) and set(left.actions)!=set(right.actions): conflicts.append(f"{left.policy_id}:{right.policy_id}")
        if conflicts: raise ValueError("policy_conflict:"+",".join(conflicts[:5]))
        return {"valid":True,"policies":len(self.policies),"active":len(active),"conflicts":0}

    def permissions_for(self,identity_id:str)->tuple[str,...]:
        identity=self.identities.get(identity_id)
        if not identity:return ()
        permissions=[]
        for role_id in identity.roles:
            role=self.roles.get(role_id)
            if role:permissions.extend(x for x in role.assigned_permissions if x not in role.restrictions)
        return tuple(sorted(set(permissions)))

    def identity_chain(self,originating_identity:str,delegated:tuple[str,...],component:str,parent_permissions:tuple[str,...]|None=None)->IdentityChain:
        if originating_identity not in self.identities or any(x not in self.identities for x in delegated): raise ValueError("identity_chain_invalid")
        own=set(self.permissions_for(delegated[-1] if delegated else originating_identity));effective=own.intersection(parent_permissions) if parent_permissions is not None else own
        identity=self.identities[originating_identity]
        return IdentityChain(originating_identity,delegated,_clean(component,120),tuple(sorted(effective)),identity.privacy_scope,tuple(sorted(p.policy_id for p in self.policies.values() if p.status is PolicyState.ACTIVE)))

    def authorize(self,identity_id:str,operation:str,parent_permissions:tuple[str,...]|None=None)->AuthorizationDecision:
        operation=_clean(operation,160);identity=self.identities.get(identity_id);permissions=self.permissions_for(identity_id)
        if parent_permissions is not None:permissions=tuple(sorted(set(permissions).intersection(parent_permissions)))
        authenticated=bool(identity and identity.authentication_state is AuthenticationState.VERIFIED)
        permission_match=operation in permissions or "*" in permissions
        policy=self.evaluate_policy(operation)
        allowed=authenticated and permission_match and policy["allowed"]
        reason="allowed_by_explicit_identity_permission_and_policy" if allowed else "identity_not_verified" if not authenticated else "permission_denied" if not permission_match else "policy_denied"
        risk=self.classify_risk((operation,));decision=AuthorizationDecision(identity_id,operation,allowed,permissions,reason,tuple(policy["policies"]),risk,self._is_privileged(operation))
        self.metrics["authorization_evaluations"]+=1;self._audit("authorization","governance",identity_id,operation,"allowed" if allowed else "denied",severity=SecuritySeverity.INFORMATIONAL if allowed else SecuritySeverity.WARNING)
        return decision

    def evaluate_policy(self,operation:str,scope:str="global")->dict[str,object]:
        applicable=[p for p in self.policies.values() if p.status is PolicyState.ACTIVE and p.scope in {scope,"global"} and (not p.conditions or operation in p.conditions or "*" in p.conditions)]
        order={name:index for index,name in enumerate(POLICY_PRECEDENCE)}
        applicable.sort(key=lambda p:(order.get(p.policy_name.split(".")[0].lower(),len(order)),-p.priority,p.policy_id))
        allowed=not self._is_privileged(operation);reason="default_low_risk_allow" if allowed else "default_privileged_deny"
        for policy in applicable:
            if "deny:*" in policy.actions or f"deny:{operation}" in policy.actions:allowed=False;reason=f"denied_by:{policy.policy_id}";break
            if "allow:*" in policy.actions or f"allow:{operation}" in policy.actions:allowed=True;reason=f"allowed_by:{policy.policy_id}"
        self.metrics["policy_evaluations"]+=1
        return {"allowed":allowed,"reason":reason,"policies":tuple(p.policy_id for p in applicable),"execution_authorized":False}

    def zero_trust_validate(self,identity_id:str,operation:str,*,privacy:PrivacyClass=PrivacyClass.PRIVATE,parent_permissions:tuple[str,...]|None=None)->dict[str,object]:
        decision=self.authorize(identity_id,operation,parent_permissions);risk=self.classify_risk((operation,privacy.value));valid=decision.allowed and risk is not GovernanceRisk.CRITICAL
        return {"valid":valid,"identity_verified":identity_id in self.identities and self.identities[identity_id].authentication_state is AuthenticationState.VERIFIED,"permission_valid":decision.allowed,"privacy":privacy.value,"risk":risk.value,"approval_still_required":decision.approval_still_required,"broker_still_required":decision.approval_still_required,"execution_authorized":False,"reason":decision.reason}

    def classify_risk(self,factors:tuple[str,...])->GovernanceRisk:
        text=" ".join(factors).lower();self.metrics["risk_evaluations"]+=1
        if any(x in text for x in ("secret","credential","force push","bypass","hardware control")):return GovernanceRisk.CRITICAL
        if any(x in text for x in ("send","external","write","deploy","plugin","mcp","github mutation")):return GovernanceRisk.HIGH
        if any(x in text for x in ("browser","provider","workflow","private","knowledge persistence")):return GovernanceRisk.MEDIUM
        return GovernanceRisk.LOW if text.strip() else GovernanceRisk.MINIMAL

    def evaluate_trust(self,entity_id:str,entity_type:str,factors:tuple[str,...])->TrustScore:
        score=.2;normalized={x.lower() for x in factors}
        score+=.25 if "identity_verified" in normalized else 0;score+=.2 if "policy_compliant" in normalized else 0;score+=.15 if "runtime_healthy" in normalized else 0;score-=.4 if "policy_violation" in normalized else 0;score=max(0,min(1,score))
        level=TrustLevel.HIGH if score>=.75 else TrustLevel.MEDIUM if score>=.5 else TrustLevel.LOW if score>0 else TrustLevel.UNTRUSTED
        result=TrustScore(_clean(entity_id,120),_clean(entity_type,80),score,level,supporting_factors=tuple(sorted(normalized)),warnings=("Advisory only; trust grants no permission.",));self.trust[entity_id]=result
        while len(self.trust)>self.limits.max_trust_cache:self.trust.pop(next(iter(self.trust)))
        self.metrics["trust_evaluations"]+=1;return result

    def revoke_trust(self,entity_id:str)->TrustScore:
        old=self.trust.get(entity_id);result=TrustScore(_clean(entity_id,120),old.entity_type if old else "unknown",0,TrustLevel.REVOKED,warnings=("Trust revoked; permissions are unchanged and remain independently evaluated.",));self.trust[entity_id]=result;self._audit("trust_change","governance","system",entity_id,"revoked");return result

    def compliance(self,component:str,policy_set:tuple[str,...])->ComplianceResult:
        unknown=tuple(x for x in policy_set if x not in self.policies);inactive=tuple(x for x in policy_set if x in self.policies and self.policies[x].status is not PolicyState.ACTIVE)
        state=ComplianceState.UNKNOWN if not policy_set else ComplianceState.NON_COMPLIANT if unknown else ComplianceState.WARNING if inactive else ComplianceState.COMPLIANT
        result=ComplianceResult(policy_set,_clean(component,120),state,unknown, inactive, ("Review unknown policy references.",) if unknown else ())
        self.metrics["compliance_evaluations"]+=1;self._audit("compliance_evaluation","governance","system",component,state.value,policy_reference=",".join(policy_set));return result

    def security_event(self,event_type:str,component:str,severity:SecuritySeverity,summary:str,**refs:str)->SecurityEvent:
        event=SecurityEvent(_clean(event_type,100),_clean(component,100),severity,_clean(summary,240),_clean(refs.get("identity_id",""),120),_clean(refs.get("workflow_id",""),120),_clean(refs.get("policy_id",""),120),_clean(refs.get("correlation_id",""),120));self.security_events.append(event);self.metrics["security_events"]+=1
        self._audit("security_event",component,refs.get("identity_id","system"),event_type,"recorded",severity=severity);return event

    def correlate_events(self,correlation_id:str)->tuple[SecurityEvent,...]:return tuple(x for x in self.security_events if x.correlation_id==correlation_id)[:self.limits.max_search_results]

    def create_incident(self,event_ids:tuple[str,...])->SecurityIncident:
        events=tuple(x for x in self.security_events if x.event_id in event_ids);severity=SecuritySeverity.CRITICAL if any(x.severity is SecuritySeverity.CRITICAL for x in events) else SecuritySeverity.HIGH if any(x.severity is SecuritySeverity.HIGH for x in events) else SecuritySeverity.WARNING
        incident=SecurityIncident(severity,tuple(sorted({x.component for x in events})),tuple(sorted({x.workflow_id for x in events if x.workflow_id})),GovernanceRisk.CRITICAL if severity is SecuritySeverity.CRITICAL else GovernanceRisk.HIGH,recommended_actions=("pause_affected_workflow","request_operator_review","increase_monitoring"),related_events=tuple(x.event_id for x in events));self.incidents.append(incident);return incident

    def transition_incident(self,incident_id:str,status:IncidentState)->SecurityIncident:
        current=next((x for x in self.incidents if x.incident_id==incident_id),None)
        if not current:raise ValueError("incident_not_found")
        updated=replace(current,status=status);self.incidents=deque((updated if x.incident_id==incident_id else x for x in self.incidents),maxlen=self.limits.max_incidents);self._audit("incident_transition","governance","operator",incident_id,status.value);return updated

    def search_audit(self,*,event_type:str="",actor:str="",target:str="",policy:str="")->tuple[AuditRecord,...]:
        return tuple(x for x in self.audit_records if (not event_type or x.event_type==event_type) and (not actor or x.actor==actor) and (not target or x.target==target) and (not policy or x.policy_reference==policy))[-self.limits.max_search_results:]

    def audit_correction(self,audit_id:str,reason:str)->AuditRecord:return self._audit("audit_correction","governance","operator",audit_id,"corrected",warnings=(_clean(reason,240),))

    def verify_audit_chain(self)->bool:
        records=tuple(self.audit_records)
        return all(record.previous_digest==records[index-1].digest for index,record in enumerate(records) if index>0) and all(record.digest==self._digest(record,record.previous_digest) for record in records)

    def dashboard(self)->dict[str,object]:
        risks=Counter(x.risk_level.value for x in self.incidents);compliance="unknown" if not self.policies else "configured"
        return {"security_health":"ready","zero_trust":self.zero_trust_enabled,"identities":len(self.identities),"active_policies":sum(p.status is PolicyState.ACTIVE for p in self.policies.values()),"audit_records":len(self.audit_records),"events":len(self.security_events),"incidents":len(self.incidents),"trust_entries":len(self.trust),"risk_distribution":dict(risks),"compliance":compliance,"execution_authority":False}

    def verify(self)->dict[str,object]:
        policy=self.validate_policies();return {"valid":policy["valid"] and self.verify_audit_chain(),"zero_trust":self.zero_trust_enabled,"audit_append_only":True,"automatic_permission_escalation":False,"automatic_policy_override":False,"execution_authority":False}

    def _is_privileged(self,operation:str)->bool:return operation.startswith(PRIVILEGED_PREFIXES) or any(f".{x}" in operation for x in PRIVILEGED_PREFIXES)
    def _digest(self,record:AuditRecord,previous:str)->str:
        raw="|".join((record.audit_id,record.timestamp,record.event_type,record.component,record.actor,record.target,record.result,record.severity.value,previous));return sha256(raw.encode()).hexdigest()
    def _audit(self,event_type:str,component:str,actor:str,target:str,result:str,*,severity:SecuritySeverity=SecuritySeverity.INFORMATIONAL,policy_reference:str="",warnings:tuple[str,...]=())->AuditRecord:
        previous=self.audit_records[-1].digest if self.audit_records else "";record=AuditRecord(_clean(event_type,100),_clean(component,100),_clean(actor,120),_clean(target,160),_clean(result,120),severity,policy_reference=_clean(policy_reference,160),warnings=tuple(_clean(x,200) for x in warnings),previous_digest=previous);record=replace(record,digest=self._digest(record,previous));self.audit_records.append(record);self.metrics["audit_records"]+=1;return record


def build_default_governance_runtime()->GovernanceRuntime:
    runtime=GovernanceRuntime()
    runtime.register_role(Role("diagnostic_reader","Diagnostic reader","Read bounded status and audit metadata.",( "diagnostics.read","audit.read","configuration.read")))
    runtime.register_role(Role("executive_coordinator","Executive coordinator","Coordinate requests without bypassing downstream authority.",( "diagnostics.read","workflow.read","provider.read")))
    runtime.register_identity(Identity("local_user",IdentityType.USER,"Local user",TrustLevel.MEDIUM,AuthenticationState.VERIFIED,AuthorizationState.AUTHORIZED,PrivacyClass.PRIVATE,("diagnostic_reader",)))
    runtime.register_identity(Identity("executive",IdentityType.AGENT,"Executive JARVIS",TrustLevel.HIGH,AuthenticationState.VERIFIED,AuthorizationState.AUTHORIZED,PrivacyClass.PROJECT,("executive_coordinator",)))
    runtime.register_identity(Identity("prime",IdentityType.AGENT,"Prime Agent",TrustLevel.MEDIUM,AuthenticationState.VERIFIED,AuthorizationState.RESTRICTED,PrivacyClass.PROJECT,("executive_coordinator",)))
    runtime.register_policy(Policy("security-default-deny","security.default_deny","1.0","global","executive",("*",),("deny:write_memory","deny:secrets_access","deny:credentials_access"),1000,PolicyState.ACTIVE))
    return runtime
