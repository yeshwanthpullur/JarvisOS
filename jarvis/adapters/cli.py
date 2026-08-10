from .agent import AdapterAgent,adapter_safety
def render_adapter_command(a,c,args):
 t=" ".join(args).strip()
 if c=="adapter status":return "Adapter status: "+" ".join(f"{k}={v}" for k,v in a.status().items())
 if c=="adapter help":return "Adapter commands: status, help, list, show, plan, safety, permissions, capabilities, show-job, history. Manifest-only; no MCP/plugin runtime, installation, credentials, network, or execution."
 if c=="adapter list":return "Adapters: "+", ".join(f"{m.adapter_id}:{m.status.value}:execute=no" for m in a.manifests)
 if c=="adapter show":
  m=a.show(t);return "Adapter unavailable." if m is None else f"Adapter: id={m.adapter_id} type={m.adapter_type.value} status={m.status.value} enabled=no execution=no credentials={'required' if m.requires_credentials else 'not_required'}."
 if c=="adapter plan":
  r=a.plan(t);return f"Adapter plan: status={r.status.value} intent={r.plan.intent.value} target={r.plan.target_adapter} execution=no steps="+" | ".join(r.plan.proposed_steps)
 if c=="adapter safety":
  r,ok,why=adapter_safety(t);return f"Adapter safety: risk={r.value} allowed={'yes' if ok else 'no'} reason={why}"
 if c=="adapter permissions":return "Adapter permissions: "+(", ".join(f"{p.name}:granted=no:risk={p.risk_level.value}" for p in a.permissions(t)) or "none")
 if c=="adapter capabilities":return "Adapter capabilities: manifests=yes MCP_runtime=no plugin_execution=no network=no credentials=no background_servers=no."
 if c=="adapter show-job":
  r=a.show_job(t);return "Adapter job unavailable." if r is None else f"Adapter job: id={r.request_id} status={r.status.value} execution=no."
 if c=="adapter history":return "Adapter history: "+(", ".join(f"{x.request_id}:{x.status.value}" for x in a.history[-10:]) or "empty")
 return "Adapter command unavailable."
