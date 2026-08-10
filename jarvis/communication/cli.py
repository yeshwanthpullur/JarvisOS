from .agent import CommunicationAgent,communication_safety
def render_communication_command(a,c,args):
 t=" ".join(args).strip()
 if c=="communication status":return "Communication status: "+" ".join(f"{k}={v}" for k,v in a.status().items())
 if c=="communication help":return "Communication commands: status, help, providers, plan, safety, draft, notify-plan, show, history. Draft-only; no sending, contacts, tokens, or provider calls."
 if c=="communication providers":return "Communication providers: "+", ".join(f"{p.provider_id}:{p.status}:send=no" for p in a.providers)
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
