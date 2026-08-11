"""Bounded Telegram command rendering."""
from __future__ import annotations
from .runtime import TelegramRuntime

HELP="telegram status|capabilities|identity|auth-status|pair|pair-status|unpair|chats|validate-chat|polling-status|start|stop|send-plan|send-dry-run|send|rate-status|history|health"
def render_telegram_command(command,args,runtime:TelegramRuntime):
    op=command.removeprefix("telegram ");status=runtime.status()
    if op=="help":return HELP
    if op in {"status","health"}:return "Telegram: "+" ".join(f"{k}={str(v).lower() if isinstance(v,bool) else v}" for k,v in status.items())
    if op=="capabilities":return "Telegram capabilities: text_receive=controlled text_reply=authorized independent_send=approval_required attachments=disabled voice=disabled groups=disabled webhook=disabled scheduled=disabled"
    if op in {"identity","auth-status"}:return f"Telegram identity: verified={str(runtime.identity.verified).lower()} username={runtime.identity.username or 'unavailable'} credential_present={str(runtime.credential_present()).lower()} token_exposed=no"
    if op=="pair":return f"Telegram pairing code: {runtime.create_pairing()} expires_in=300s single_use=yes. Send /pair <code> from the intended private chat."
    if op=="pair-status":return f"Telegram pairing: status={runtime.pairing_status()}"
    if op=="unpair":return "Telegram unpair: explicit chat reference required through the authorized inbound interface."
    if op=="chats":return f"Telegram authorized chats: count={len(runtime.authorizations)} refs="+(",".join(runtime.authorizations) or "none")
    if op=="validate-chat":return f"Telegram chat validation: valid={'yes' if args and args[0].strip() else 'no'} authorization_required=yes"
    if op=="polling-status":return f"Telegram polling: active={str(runtime.polling).lower()} last_update_id={runtime.last_update_id} daemon=no webhook=no"
    if op=="start":r=runtime.start();return f"Telegram polling start: status={r.status} error={r.error or 'none'} daemon=no"
    if op=="stop":r=runtime.stop();return f"Telegram polling stop: status={r.status}"
    if op in {"send-plan","send-dry-run"}:
        text=" ".join(args);p=runtime.plan_send("planned-destination",text);return f"Telegram {op}: chunks={p.chunks} approval_required={str(p.approval_required).lower()} policy_allowed={str(p.policy_allowed).lower()} executed=no"
    if op=="send":return "Telegram send: approval_required; use the authoritative scoped Approval System and Broker. No message was sent."
    if op=="rate-status":return f"Telegram rate: sent_window={len(runtime.send_times)} limit={runtime.policy.max_sends_per_window} window_seconds={runtime.policy.rate_limit_window}"
    if op=="history":return "Telegram history: "+("; ".join(f"{x['action']}:{x['status']}:chunks={x['chunks']}" for x in runtime.history) or "none")
    return HELP

