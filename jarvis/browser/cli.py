from .agent import BrowserAgent,browser_safety
def render_browser_command(a:BrowserAgent,c:str,args:tuple[str,...])->str:
 t=" ".join(args).strip()
 if c=="browser status":return "Browser status: "+" ".join(f"{k}={str(v).lower() if isinstance(v,bool) else v}" for k,v in a.status().items())
 if c=="browser help":return "Browser commands: status, help, plan, safety, capabilities, sources, summarize, show, history. Read-only; login, forms, purchases, cookies, and sessions are disabled."
 if c=="browser capabilities":return "Browser capabilities: read_only=yes interactive=no screenshots=no forms=no login=no downloads=no cookies=no purchases=no."
 if c=="browser safety":
  r,ok,why=browser_safety(t);return f"Browser safety: risk={r.value} allowed={'yes' if ok else 'no'} reason={why}"
 if c=="browser plan":
  r=a.plan(t);return f"Browser plan: status={r.status.value} intent={r.plan.intent.value} steps="+" | ".join(r.plan.proposed_steps)
 if c=="browser sources":
  r=a.sources(t);return f"Browser sources: status={r.status.value} retrieved=no policy={r.sources[0].reason}"
 if c=="browser summarize":
  r=a.summarize(t);return f"Browser summary: status={r.status.value} output={r.output}"
 if c=="browser show":
  r=a.show(t);return "Browser job unavailable." if r is None else f"Browser job: id={r.request_id} status={r.status.value}."
 if c=="browser history":return "Browser history: "+(", ".join(f"{x.request_id}:{x.status.value}" for x in a.history[-10:]) or "empty")
 return "Browser command unavailable."
