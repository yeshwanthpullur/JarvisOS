"""Bounded CLI rendering for external integration metadata."""
from __future__ import annotations
from .control_plane import ExternalIntegrationControlPlane
from .security import credential_presence,validate_endpoint
def render_external_command(command,args=(),plane=None):
 p=plane or ExternalIntegrationControlPlane(); op=command.lower(); arg=args[0] if args else ""
 if op=="integration status":
  s=p.registry.summary();return f"External integrations: registered={s['total']} enabled={s['enabled']} configured={s['configured']} ready={s['ready']} execution=disabled cloud=disabled."
 if op=="integration policy":return "External integration policy: local-first=yes execution=disabled approval-authoritative=Phase4 paid=disabled secret-egress=blocked retries=bounded."
 if op=="provider list":return "External provider list: "+", ".join(f"{x.provider_id}:{x.state.value}" for x in p.registry.list())
 if op=="provider show":
  x=p.registry.get(arg)
  return "External provider not found." if not x else f"Provider {x.provider_id}: category={x.category.value} state={x.state.value} enabled={str(x.enabled).lower()} configured={str(x.configured).lower()} execution={str(x.policy.execution_allowed).lower()} reason={x.reason}"
 if op=="provider capabilities":return "External capabilities: "+", ".join(sorted({c.name for x in p.registry.list() for c in x.capabilities}))
 if op=="provider health":
  h=p.health(arg);return f"Provider health: id={arg or 'required'} state={h.state.value} cached={str(h.cached).lower()} reason={h.reason}"
 if op=="provider policy":return "Provider policy: no automatic enablement; credentials are references only; paid/cloud execution disabled; approval system authoritative."
 if op=="provider validate":
  x=p.registry.get(arg)
  if not x:return "Provider validation: provider not found."
  valid,reason=validate_endpoint(x.endpoint,local_provider=x.local);return f"Provider validation: id={x.provider_id} registry=valid endpoint={reason} executable=no result={'valid' if valid else 'blocked'}."
 if op=="provider history":return "Provider history: "+("; ".join(f"{x['provider_id']}:{x['status']}:{x['reason']}" for x in list(p.history)[-10:]) or "none")
 if op=="credential status":
  x=p.registry.get(arg)
  if not x:return "Credential status: provider not found."
  values=credential_presence(x);return f"Credential status: provider={x.provider_id} "+(", ".join(f"{k}=missing" for k in values) or "not_required")
 if op=="credential required":return "Required credential references: "+", ".join(f"{x.provider_id}=[{','.join(x.credential_refs)}]" for x in p.registry.list() if x.credential_refs)
 return "External integration command unavailable."
