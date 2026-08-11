from .agent import CommunicationAgent,communication_safety
def render_communication_command(a,c,args):
 t=" ".join(args).strip()
 if c=="communication status":return "Communication status: "+" ".join(f"{k}={v}" for k,v in a.status().items())
 if c=="communication help":return "Communication commands: status, help, providers, plan, safety, draft, notify-plan, show, history. Draft-only; no sending, contacts, tokens, or provider calls."
 if c=="communication providers":return "Communication providers: "+", ".join(f"{p.provider_id}:{p.status}:send=no" for p in a.providers)
 if c=="communication provider-status":return f"External communication providers: registered={len(a.external.profiles)} ready={sum(p.ready for p in a.external.profiles)} sending=disabled bulk=disabled scheduled=disabled."
 if c=="communication provider-show":
  p=a.external.profile(args[0] if args else "");return "Communication provider unavailable." if not p else f"Communication provider {p.provider_id}: state={p.state.value} configured={str(p.configured).lower()} authenticated={str(p.authenticated).lower()} ready={str(p.ready).lower()} send=no."
 if c=="communication provider-health":
  p=a.external.profile(args[0] if args else "");return "Communication provider unavailable." if not p else f"Communication provider health: id={p.provider_id} state={p.state.value} health={p.health_status} side_effects=no."
 if c=="communication destination-validate":
  if len(args)<2:return "Destination validation: blocked reason=provider_and_destination_required."
  d=a.external.validate_destination(args[0],args[1]);return f"Destination validation: provider={d.provider_id} valid={str(d.verified).lower()} destination={d.safe_identifier or 'missing'} writable={str(d.writable).lower()}."
 if c in {"communication send-plan","communication send-safety","communication send-dry-run"}:
  provider=next((x for x in ("telegram","discord","email_smtp","email_api","slack","matrix") if x in t.lower()),"telegram");plan,v=a.external.plan(t,provider,"");return f"External message {c.split()[-1]}: provider={provider} ready={str(v.provider_ready).lower()} destination_valid={str(v.destination_valid).lower()} content_safe={str(v.content_safe).lower()} approval={str(v.approval_valid).lower()} delivered=false reason={v.blocked_reason}."
 if c=="communication attachment-check":
  x=a.external.check_attachment(t);return f"Attachment check: file={x.display_name} allowed={str(x.allowed).lower()} reason={x.blocked_reason}."
 if c=="communication rate-status":
  r=a.external.rate_status(args[0] if args else "unknown");return f"Communication rate: provider={r['provider']} count={r['count']} limit={r['limit']} window={r['window_seconds']} rate_limited={str(r['rate_limited']).lower()}."
 if c=="communication safety":
  r,ok,why=communication_safety(t);return f"Communication safety: risk={r.value} allowed={'yes' if ok else 'no'} reason={why}"
 if c in {"communication plan","communication notify-plan"}:
  r=a.plan(t);return f"Communication plan: status={r.status.value} intent={r.plan.intent.value} sending=no steps="+" | ".join(r.plan.proposed_steps)
 if c=="communication draft":
  r=a.plan(t,True);return f"Communication draft: status={r.status.value} sent=no preview={r.draft.body_preview if r.draft else 'blocked'} error={r.error or 'none'}."
 if c=="communication show":
  r=a.show(t);return "Communication job unavailable." if r is None else f"Communication job: id={r.request_id} status={r.status.value} sent=no."
 if c=="communication history":return "Communication history: "+(", ".join(f"{x.request_id}:{x.status.value}" for x in a.history[-10:]) or "empty")
 return "Communication command unavailable."
