"""Secure text-only Telegram runtime governed by Phase 4 approval and broker authority."""
from __future__ import annotations
import hashlib, hmac, os, secrets, time
from collections import deque
from dataclasses import dataclass
from jarvis.execution.broker import ExecutionBroker, ToolExecutionRequest
from jarvis.execution.models import ExecutionMode,ExecutionPermission,ExecutionRisk
from jarvis.foundation_common import bounded
from .client import TelegramClient
from .models import *

@dataclass(frozen=True,slots=True)
class TelegramPolicy:
    enabled:bool=False; polling_enabled:bool=False; webhook_enabled:bool=False; require_authorized_chat:bool=True; allow_inbound_text:bool=True; allow_outbound_text:bool=True; allow_commands:bool=True; allow_media:bool=False; allow_documents:bool=False; allow_voice:bool=False; allow_group_chats:bool=False; allow_channel_posts:bool=False; allow_scheduled_send:bool=False; require_approval_for_send:bool=True; max_message_chars:int=3900; max_updates_per_poll:int=20; poll_timeout_seconds:int=10; max_retries:int=2; rate_limit_window:int=60; max_sends_per_window:int=5; save_history:bool=True; redact_sensitive_values:bool=True

class TelegramRuntime:
    def __init__(self,*,policy=None,token_getter=None,client_factory=None,broker=None,clock=None):
        self.policy=policy or TelegramPolicy();self._token_getter=token_getter or (lambda:os.environ.get("TELEGRAM_BOT_TOKEN",""));self._client_factory=client_factory or TelegramClient;self.broker=broker or ExecutionBroker();self._clock=clock or time.time
        self.identity=TelegramBotIdentity();self.authorizations={};self.pairing=None;self.polling=False;self.last_update_id=0;self.seen_updates=deque(maxlen=500);self.sent_fingerprints=deque(maxlen=100);self.send_times=deque(maxlen=100);self.history=deque(maxlen=50);self.metrics={k:0 for k in ("polls","updates","authorized","unauthorized","sent","send_failures","rate_limits","duplicates","approvals")}
    def _token(self): return self._token_getter().strip()
    def credential_present(self): return bool(self._token())
    def status(self):
        state=TelegramState.DISABLED if not self.policy.enabled else TelegramState.CREDENTIAL_MISSING if not self.credential_present() else TelegramState.READY if self.identity.verified else TelegramState.AUTH_UNVERIFIED
        return {"implemented":True,"state":state.value,"enabled":self.policy.enabled,"credential_present":self.credential_present(),"authenticated":self.identity.verified,"reachable":self.identity.verified,"ready":state is TelegramState.READY,"polling":self.polling,"authorized_chats":len(self.authorizations),"webhook":False,"attachments":False,"voice":False,"groups":False,"scheduled_send":False}
    def verify_identity(self):
        if not self.credential_present(): return TelegramResult(TelegramState.CREDENTIAL_MISSING.value,error=TelegramError.CREDENTIAL_MISSING.value)
        try:
            raw=self._client_factory(self._token(),timeout=10).identity() or {};self.identity=TelegramBotIdentity(str(raw.get("id","")),bounded(str(raw.get("username","")),80),bounded(str(raw.get("first_name","")),80),True)
            return TelegramResult("authenticated",True,external_ref=self.identity.username)
        except Exception:
            self.identity=TelegramBotIdentity(warnings=(TelegramError.AUTHENTICATION_FAILED.value,));return TelegramResult("failed",error=TelegramError.AUTHENTICATION_FAILED.value)
    def create_pairing(self,ttl_seconds=300):
        code=f"{secrets.randbelow(1000000):06d}";digest=hashlib.sha256(code.encode()).hexdigest();self.pairing=TelegramPairingRequest(digest,self._clock()+max(60,min(ttl_seconds,900)));return code
    def pairing_status(self):
        if not self.pairing:return "unavailable"
        if self.pairing.used:return "used"
        return "expired" if self._clock()>self.pairing.expires_at_epoch else "pending"
    def pair(self,code,chat_id,user_id,chat_type="private"):
        p=self.pairing;digest=hashlib.sha256(code.encode()).hexdigest()
        if not p or p.used or self._clock()>p.expires_at_epoch or chat_type!="private" or not hmac.compare_digest(digest,p.code_fingerprint):return TelegramResult("blocked",error=TelegramError.AUTHORIZATION_FAILED.value)
        p.used=True;ref=self._ref(chat_id);self.authorizations[ref]=TelegramChatAuthorization(ref,self._ref(user_id));return TelegramResult("authorized",True,external_ref=ref)
    def unpair(self,chat_id): return self.authorizations.pop(self._ref(chat_id),None) is not None
    def _ref(self,value): return hashlib.sha256(str(value).encode()).hexdigest()[:16]
    def authorized(self,chat_id,user_id,chat_type="private"):
        item=self.authorizations.get(self._ref(chat_id));return bool(item and item.user_id_ref==self._ref(user_id) and chat_type=="private")
    def normalize_update(self,update):
        try:
            uid=int(update["update_id"]);msg=update["message"];chat=msg["chat"];sender=msg["from"];text=msg.get("text")
            if uid<=self.last_update_id or uid in self.seen_updates:self.metrics["duplicates"]+=1;return None,TelegramError.POLICY_BLOCKED.value
            if not isinstance(text,str):return None,TelegramError.UNSUPPORTED_UPDATE.value
            text=text.strip()
            if not text or len(text)>self.policy.max_message_chars:return None,TelegramError.MESSAGE_TOO_LARGE.value
            ctype=str(chat.get("type",""));auth=self.authorized(chat.get("id"),sender.get("id"),ctype)
            command=text.split(maxsplit=1)[0].lower() if text.startswith("/") else ""
            return TelegramInboundMessage(uid,int(msg.get("message_id",0)),self._ref(chat.get("id")),self._ref(sender.get("id")),ctype,int(msg.get("date",0)),text,command,authorized=auth),""
        except (KeyError,TypeError,ValueError):return None,TelegramError.UNSUPPORTED_UPDATE.value
    def accept_update(self,update):
        message,error=self.normalize_update(update);self.metrics["updates"]+=1
        if message is None:return TelegramResult("ignored",error=error)
        self.seen_updates.append(message.update_id);self.last_update_id=max(self.last_update_id,message.update_id)
        if not message.authorized and message.command!="/pair":self.metrics["unauthorized"]+=1;return TelegramResult("blocked",error=TelegramError.AUTHORIZATION_FAILED.value)
        self.metrics["authorized"]+=int(message.authorized);return TelegramResult("accepted",True,external_ref=message.chat_ref)
    def start(self):
        if not self.policy.enabled:return TelegramResult("blocked",error="provider_disabled")
        verified=self.verify_identity()
        if not verified.executed:return verified
        if not self.authorizations:return TelegramResult("blocked",error="authorized_chat_required")
        self.polling=True;return TelegramResult("started",True)
    def stop(self):self.polling=False;return TelegramResult("stopped",True)
    def poll_once(self):
        if not self.polling:return ()
        self.metrics["polls"]+=1
        try:updates=self._client_factory(self._token(),timeout=self.policy.poll_timeout_seconds+2).updates(self.last_update_id+1,self.policy.max_updates_per_poll,self.policy.poll_timeout_seconds) or []
        except Exception:return (TelegramResult("failed",error=TelegramError.NETWORK_UNREACHABLE.value),)
        return tuple(self.accept_update(x) for x in updates[:self.policy.max_updates_per_poll])
    def chunks(self,text):
        text=text.strip();limit=self.policy.max_message_chars
        if not text:return ()
        return tuple(text[i:i+limit] for i in range(0,len(text),limit))
    def plan_send(self,destination,message,*,direct_reply=False):
        safe=bool(destination and message.strip() and len(message)<=self.policy.max_message_chars*8);return TelegramSendPlan(self._ref(destination) if destination else "missing",bounded(message,400),len(self.chunks(message)),direct_reply,not direct_reply,safe,warnings=(() if safe else (TelegramError.MESSAGE_TOO_LARGE.value,)))
    def send(self,destination,message,approval_id="",*,direct_reply=False):
        plan=self.plan_send(destination,message,direct_reply=direct_reply)
        if not self.policy.enabled or not self.identity.verified:return TelegramResult("unavailable",error="provider_not_ready")
        if not plan.policy_allowed:return TelegramResult("blocked",error=TelegramError.MESSAGE_TOO_LARGE.value)
        fp=hashlib.sha256(f"{plan.destination_ref}:{message}".encode()).hexdigest()
        if fp in self.sent_fingerprints:return TelegramResult("blocked",error="duplicate_send")
        now_epoch=self._clock();self.send_times=deque((x for x in self.send_times if now_epoch-x<self.policy.rate_limit_window),maxlen=100)
        if len(self.send_times)>=self.policy.max_sends_per_window:self.metrics["rate_limits"]+=1;return TelegramResult("blocked",error=TelegramError.RATE_LIMITED.value)
        if not direct_reply:
            req=ToolExecutionRequest("telegram_send","telegram_send_tool","communication","Send bounded Telegram text",ExecutionMode.APPROVED_EXECUTION,ExecutionRisk.HIGH,(ExecutionPermission.SEND_MESSAGE,ExecutionPermission.NETWORK_ACCESS),(plan.destination_ref,),approval_id,False)
            routed=self.broker.route(req)
            if routed.status!="approved_for_executor":return TelegramResult("approval_required",error=TelegramError.APPROVAL_REQUIRED.value)
        try:
            refs=[]
            for chunk in self.chunks(message):refs.append(str((self._client_factory(self._token(),timeout=10).send_text(destination,chunk) or {}).get("message_id","")))
            self.sent_fingerprints.append(fp);self.send_times.append(now_epoch);self.metrics["sent"]+=len(refs);self.history.append({"action":"send","status":"completed","chunks":len(refs),"destination_ref":plan.destination_ref});return TelegramResult("completed",True,external_ref=",".join(refs))
        except Exception:self.metrics["send_failures"]+=1;return TelegramResult("failed",error=TelegramError.PROVIDER_ERROR.value)

