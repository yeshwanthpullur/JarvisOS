"""Read-only, side-effect-free Browser Agent planner."""
from dataclasses import dataclass,field
from jarvis.foundation_common import bounded,contains_secret,new_id
from .models import *
def classify_browser_intent(text:str)->BrowserIntent:
 v=text.lower()
 if contains_secret(text) or any(x in v for x in ("captcha","steal cookie","session token","private data")): return BrowserIntent.UNSAFE_OR_PRIVATE_REQUEST
 if any(x in v for x in ("buy ","purchase","checkout")): return BrowserIntent.SHOPPING_OR_PURCHASE_REQUEST
 if "login" in v or "sign in" in v:return BrowserIntent.LOGIN_TASK_REQUEST
 if "form" in v or "submit" in v:return BrowserIntent.FORM_TASK_REQUEST
 if "summar" in v:return BrowserIntent.SUMMARIZE_WEBPAGE
 if "compare" in v:return BrowserIntent.COMPARE_PAGES
 if "research" in v:return BrowserIntent.RESEARCH_WEB
 return BrowserIntent.BROWSER_TASK_PLAN
def browser_safety(text:str)->tuple[BrowserRiskLevel,bool,str]:
 i=classify_browser_intent(text)
 if i is BrowserIntent.UNSAFE_OR_PRIVATE_REQUEST:return BrowserRiskLevel.CRITICAL,False,"CAPTCHA bypass, secrets, cookies, sessions, and private targeting are blocked."
 if i in {BrowserIntent.SHOPPING_OR_PURCHASE_REQUEST,BrowserIntent.LOGIN_TASK_REQUEST,BrowserIntent.FORM_TASK_REQUEST,BrowserIntent.ACCOUNT_OR_MESSAGE_REQUEST}:return BrowserRiskLevel.HIGH,False,"Interactive browser side effects are disabled."
 return BrowserRiskLevel.LOW,True,"Read-only public-page planning is allowed."
@dataclass(slots=True)
class BrowserAgent:
 enabled:bool=True; read_only_available:bool=True; max_history_items:int=25; history:list[BrowserResult]=field(default_factory=list)
 def _record(self,r):self.history=(self.history+[r])[-self.max_history_items:];return r
 def capabilities(self):return BrowserCapabilityStatus(self.read_only_available)
 def status(self):return {"status":"ready_read_only" if self.enabled else "disabled","mode":"plan_only","web_read_only":self.read_only_available,"interactive":"disabled","login":"disabled","forms":"disabled","purchases":"disabled","cookies":"disabled"}
 def plan(self,text:str):
  risk,allowed,reason=browser_safety(text);intent=classify_browser_intent(text);req=BrowserRequest(text," ".join(text.lower().split()),intent,risk_level=risk);status=BrowserStatus.PLANNED if allowed else BrowserStatus.BLOCKED
  plan=BrowserPlan(req.request_id,intent,"Plan bounded read-only browser work.",( "Validate a public source reference.","Use read-only retrieval only when explicitly invoked.","Return bounded evidence without forms, login, downloads, purchases, cookies, or sessions."),risk_level=risk,approval_required=risk is BrowserRiskLevel.HIGH,status=status,warnings=(() if allowed else (reason,)))
  return self._record(BrowserResult(req.request_id,status,req,plan,self.capabilities(),warnings=plan.warnings,error=None if allowed else "blocked_by_browser_policy"))
 def sources(self,text:str):
  result=self.plan(text);src=BrowserSource(new_id(),"public_web","user_supplied_or_future_url","Read-only source plan",result.status is not BrowserStatus.BLOCKED,"No source was retrieved; this is policy metadata.")
  return self._record(BrowserResult(new_id(),result.status,result.request,result.plan,result.capability_status,(src,),warnings=("No source retrieval was performed.",)))
 def summarize(self,ref:str):
  return self._record(BrowserResult(new_id(),BrowserStatus.PLANNED,capability_status=self.capabilities(),output="No page was retrieved. Provide evidence through the existing read-only web path; no citation is fabricated.",warnings=("Plan-only browser summary.",)))
 def show(self,i):return next((x for x in reversed(self.history) if x.request_id==i),None)
