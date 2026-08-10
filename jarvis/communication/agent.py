from dataclasses import dataclass,field
from jarvis.foundation_common import bounded,contains_secret,new_id
from .models import *
def default_communication_providers():
 return tuple(CommunicationProvider(i,n,t,"not_configured",False,False,True,("draft",),("Real sending is disabled." ,)) for i,n,t in (("local_notification","Local notification",CommunicationProviderType.LOCAL_NOTIFICATION),("telegram","Telegram",CommunicationProviderType.TELEGRAM),("discord","Discord",CommunicationProviderType.DISCORD),("email_smtp","Email SMTP",CommunicationProviderType.EMAIL_SMTP),("slack","Slack",CommunicationProviderType.SLACK),("social","Social media",CommunicationProviderType.SOCIAL)))
def classify_communication_intent(t):
 v=t.lower()
 if contains_secret(t) or any(x in v for x in ("harass","phish","dox","threat")):return CommunicationIntent.UNSAFE_OR_ABUSIVE_REQUEST
 if any(x in v for x in ("spam","100 people","bulk send")):return CommunicationIntent.BULK_MESSAGE_REQUEST
 if any(x in v for x in ("send now","send email","post now")):return CommunicationIntent.SEND_MESSAGE_REQUEST
 if "email" in v:return CommunicationIntent.DRAFT_EMAIL
 if "notification" in v:return CommunicationIntent.DRAFT_NOTIFICATION
 return CommunicationIntent.DRAFT_MESSAGE
def communication_safety(t):
 i=classify_communication_intent(t)
 if i in {CommunicationIntent.UNSAFE_OR_ABUSIVE_REQUEST,CommunicationIntent.BULK_MESSAGE_REQUEST}:return CommunicationRiskLevel.CRITICAL,False,"Abuse, spam, secret access, and bulk messaging are blocked."
 if i is CommunicationIntent.SEND_MESSAGE_REQUEST:return CommunicationRiskLevel.HIGH,False,"Real sending is disabled; create a draft only."
 return CommunicationRiskLevel.LOW,True,"Draft-only communication planning is allowed."
@dataclass(slots=True)
class CommunicationAgent:
 enabled:bool=True;max_history_items:int=25;providers:tuple[CommunicationProvider,...]=field(default_factory=default_communication_providers);history:list[CommunicationResult]=field(default_factory=list)
 def _record(self,r):self.history=(self.history+[r])[-self.max_history_items:];return r
 def status(self):return {"status":"ready_draft_only" if self.enabled else "disabled","mode":"draft_only","providers_configured":0,"sending":"disabled","contact_access":"disabled","anti_spam":"enforced"}
 def plan(self,t,draft=False):
  risk,ok,reason=communication_safety(t);intent=classify_communication_intent(t);req=CommunicationRequest(t," ".join(t.lower().split()),intent,risk_level=risk);status=CommunicationStatus.DRAFTED if ok and draft else CommunicationStatus.PLANNED if ok else CommunicationStatus.BLOCKED
  body=bounded(t.replace("draft ","",1),900) if ok and draft else ""
  msg=MessageDraft("email" if intent is CommunicationIntent.DRAFT_EMAIL else "message","unresolved explicit recipient","Draft message" if intent is CommunicationIntent.DRAFT_EMAIL else "",body or "Draft content will be created only from the explicit request.",warnings=("Not sent; recipient remains unresolved.",)) if ok else None
  plan=CommunicationPlan(req.request_id,intent,"Prepare a bounded draft without sending.",None,(),msg,("Validate anti-abuse policy.","Prepare bounded draft metadata.","Require future provider configuration and approval before sending."),risk_level=risk,status=status,warnings=(() if ok else(reason,)))
  return self._record(CommunicationResult(req.request_id,status,req,plan,self.providers,msg,warnings=plan.warnings,error=None if ok else "blocked_by_communication_policy"))
 def show(self,i):return next((x for x in reversed(self.history) if x.request_id==i),None)
