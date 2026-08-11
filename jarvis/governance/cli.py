"""Bounded CLI rendering for enterprise-governance metadata."""
from __future__ import annotations

from jarvis.foundation_common import bounded
from .runtime import GovernanceRuntime


def _list(values,formatter,empty="none")->str:return "; ".join(formatter(x) for x in tuple(values)[-25:]) or empty


def render_security_command(runtime:GovernanceRuntime,command:str,args:tuple[str,...])->str:
    op=command.removeprefix("security ")
    if op=="status":return "Security status: enabled=yes zero_trust=enabled governance=enabled audit=enabled compliance=enabled automatic_permission_escalation=disabled automatic_policy_override=disabled authority=coordination_only"
    if op=="health":return "Security health: "+" ".join(f"{k}={v}" for k,v in runtime.dashboard().items())[:4500]
    if op=="identities":return "Security identities: "+_list(runtime.identities.values(),lambda x:f"{x.identity_id}:{x.identity_type.value}:{x.authentication_state.value}:{x.trust_level.value}")
    if op=="permissions":return "Security permissions: "+_list(runtime.roles.values(),lambda x:f"{x.role_id}={','.join(x.assigned_permissions) or 'none'} restrictions={','.join(x.restrictions) or 'none'}")
    if op=="policies":return "Security policies: "+_list(runtime.policies.values(),lambda x:f"{x.policy_id}:v{x.version}:{x.status.value}:priority{x.priority}")
    if op=="trust":return "Security trust: "+_list(runtime.trust.values(),lambda x:f"{x.entity_id}:{x.trust_level.value}:{x.current_score:.2f}")
    if op=="incidents":return "Security incidents: "+_list(runtime.incidents,lambda x:f"{x.incident_id}:{x.severity.value}:{x.status.value}")
    if op=="audit":return "Security audit: "+_list(runtime.audit_records,lambda x:f"{x.audit_id}:{x.event_type}:{x.result}")
    if op=="compliance":return "Security compliance: configured_policies="+str(len(runtime.policies))+" advisory=yes execution_authority=no"
    if op=="risks":return "Security risks: minimal/low/medium/high/critical; risk is advisory and grants no permission."
    if op=="governance":return "Security governance: registry=enabled precedence=security>execution>approval>workflow>runtime>provider conflicts=fail_closed"
    if op=="events":return "Security events: "+_list(runtime.security_events,lambda x:f"{x.event_id}:{x.severity.value}:{x.event_type}:{x.component}")
    if op=="metrics":return "Security metrics: "+(", ".join(f"{k}={v}" for k,v in sorted(runtime.metrics.items())) or "none")
    if op=="dashboard":return "Security dashboard: "+" ".join(f"{k}={v}" for k,v in runtime.dashboard().items())[:4500]
    if op=="validate":
        operation=args[0] if args else "diagnostics.read";result=runtime.zero_trust_validate("local_user",operation);return "Security validation: "+" ".join(f"{k}={v}" for k,v in result.items())[:4500]
    if op=="verify":return "Security verify: "+" ".join(f"{k}={v}" for k,v in runtime.verify().items())
    if op=="policy-show":
        item=runtime.policies.get(args[0] if args else "");return "Security policy unavailable." if not item else bounded(f"Security policy: id={item.policy_id} name={item.policy_name} version={item.version} scope={item.scope} owner={item.owner} priority={item.priority} status={item.status.value} conditions={item.conditions} actions={item.actions}",4500)
    if op=="incident-show":
        item=next((x for x in runtime.incidents if x.incident_id==(args[0] if args else "")),None);return "Security incident unavailable." if not item else bounded(f"Security incident: id={item.incident_id} severity={item.severity.value} state={item.status.value} components={item.affected_components} workflows={item.affected_workflows} recommendations={item.recommended_actions}",4500)
    if op=="audit-show":
        item=next((x for x in runtime.audit_records if x.audit_id==(args[0] if args else "")),None);return "Security audit record unavailable." if not item else bounded(f"Security audit record: id={item.audit_id} time={item.timestamp} event={item.event_type} component={item.component} actor={item.actor} target={item.target} result={item.result} severity={item.severity.value} policy={item.policy_reference or 'none'}",4500)
    if op=="trust-show":
        item=runtime.trust.get(args[0] if args else "");return "Security trust record unavailable." if not item else bounded(f"Security trust: entity={item.entity_id} type={item.entity_type} score={item.current_score:.2f} level={item.trust_level.value} factors={item.supporting_factors} warnings={item.warnings}",4500)
    return "Security commands: status, health, identities, permissions, policies, trust, incidents, audit, compliance, risks, governance, events, metrics, dashboard, validate, verify, policy-show, incident-show, audit-show, trust-show."
