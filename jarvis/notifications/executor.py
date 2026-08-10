from collections import deque
from time import time
from jarvis.foundation_common import contains_secret,new_id
from jarvis.execution.broker import ExecutionBroker,ToolExecutionRequest
from jarvis.execution.models import ExecutionMode,ExecutionPermission,ExecutionRisk
from .models import *
class ConsoleNotificationProvider:
 provider=NotificationProvider("console_notification","JARVIS Console Notification","local_console","ready",True,supported_features=("visible_local_text",),unsupported_features=("os_toast","actions","external_delivery"),warnings=("Console fallback is not reported as an OS toast.",))
 def display(self,title,body):print(f"JARVIS notification: {title}: {body}");return True
class NotificationExecutor:
 def __init__(self,broker:ExecutionBroker,provider=None):self.broker=broker;self.provider=provider or ConsoleNotificationProvider();self.policy=NotificationPolicy();self.events=deque();self.history=[]
 def validate(self,title,body,approval_valid=False):
  now=time()
  while self.events and self.events[0]<now-self.policy.rate_limit_window_seconds:self.events.popleft()
  secret=contains_secret(title) or contains_secret(body);lens=len(title)<=self.policy.max_title_chars and len(body)<=self.policy.max_body_chars;rate=len(self.events)<self.policy.max_notifications_per_window;ok=self.provider.provider.available and lens and rate and not secret
  reason="secret_content_blocked" if secret else "content_too_long" if not lens else "rate_limited" if not rate else "provider_unavailable" if not self.provider.provider.available else ""
  return NotificationValidation(self.provider.provider.available,approval_valid,ok,rate,len(title)<=self.policy.max_title_chars,len(body)<=self.policy.max_body_chars,secret,reason)
 def dry_run(self,title,body):
  v=self.validate(title,body);return NotificationResult(new_id(),"dry_run_completed" if v.content_safe else "blocked",self.provider.provider.provider_id,False,error=v.blocked_reason or None)
 def send(self,title,body,approval_id):
  v=self.validate(title,body);fingerprint=f"{title[:30]}:{len(body)}";req=ToolExecutionRequest("notification_send","notification_executor","notifications",fingerprint,ExecutionMode.APPROVED_EXECUTION,ExecutionRisk.MEDIUM,(ExecutionPermission.SEND_NOTIFICATION,),("local_device",fingerprint),approval_id,False)
  if not v.content_safe:return NotificationResult(req.request_id,"blocked",self.provider.provider.provider_id,False,error=v.blocked_reason)
  if self.broker.route(req).status!="approved_for_executor":return NotificationResult(req.request_id,"approval_required",self.provider.provider.provider_id,False,error="invalid_approval")
  try:
   shown=bool(self.provider.display(title,body));self.events.append(time());r=NotificationResult(req.request_id,"completed" if shown else "failed",self.provider.provider.provider_id,shown);self.history=(self.history+[r])[-50:];return r
  except Exception:return NotificationResult(req.request_id,"failed",self.provider.provider.provider_id,False,error="provider_failure")
