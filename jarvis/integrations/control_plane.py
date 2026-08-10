"""Safe routing, cached health metadata, and bounded audit history."""
from __future__ import annotations
from collections import deque
from .models import *
from .registry import ExternalProviderRegistry,build_external_provider_registry
from .security import validate_action,validate_endpoint
class ExternalIntegrationControlPlane:
 def __init__(self,registry:ExternalProviderRegistry|None=None,max_history=50):self.registry=registry or build_external_provider_registry();self.history=deque(maxlen=max_history)
 def route(self,capability,data_classification=DataClassification.PROJECT_INTERNAL,local_preferred=True):
  candidates=self.registry.find(capability);ordered=sorted(candidates,key=lambda p:(not(local_preferred and p.local),p.cost_class in {CostClass.PAID,CostClass.METERED},p.provider_id))
  selectable=[p for p in ordered if p.enabled and p.configured and p.state==ProviderState.READY and p.policy.execution_allowed]
  selected=selectable[0] if selectable else None
  return ProviderRoute(capability,selected.provider_id if selected else None,"ready" if selected else "unavailable","Provider selected by bounded policy." if selected else "No enabled, configured, ready provider permits execution.",bool(selected and selected.policy.approval_required),data_classification,tuple(p.provider_id for p in ordered[:8]))
 def validate_request(self,request):
  p=self.registry.get(request.provider_id)
  if p is None:return ExternalActionResult(request.request_id,request.provider_id,"blocked",reason="provider_not_registered")
  endpoint_ok,endpoint_reason=validate_endpoint(p.endpoint,local_provider=p.local)
  allowed,reason=validate_action(request,p) if endpoint_ok else (False,endpoint_reason)
  result=ExternalActionResult(request.request_id,p.provider_id,"validated" if allowed else "blocked",False,reason)
  self.history.append({"request_id":request.request_id,"provider_id":p.provider_id,"capability":request.capability,"status":result.status,"reason":reason})
  return result
 def health(self,pid):
  p=self.registry.get(pid);return p.health if p else ProviderHealth(ProviderState.ERROR,reason="provider_not_registered")
