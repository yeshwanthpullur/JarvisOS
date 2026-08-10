"""Credential, egress, and endpoint policy without secret access."""
from __future__ import annotations
import re
from urllib.parse import urlsplit
from .models import DataClassification, ExternalActionRequest, ExternalProvider

_SECRET_PATTERNS=(
 re.compile(r"(?i)authorization\s*[:=]\s*bearer\s+[A-Za-z0-9._~+/-]+"),
 re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/-]+"),
 re.compile(r"(?i)(api[_-]?key|token|password|secret|authorization|cookie|session[_-]?id)\s*[:=]\s*\S+"),
 re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)
def redact(value:str,max_chars:int=240)->str:
 text=value[:max_chars]
 for pattern in _SECRET_PATTERNS:text=pattern.sub("[REDACTED]",text)
 return text
def credential_presence(provider:ExternalProvider,available_refs:set[str]|None=None)->dict[str,bool]:
 available_refs=available_refs or set();return {ref:ref in available_refs for ref in provider.credential_refs}
def validate_endpoint(endpoint:str|None,*,local_provider:bool=False)->tuple[bool,str]:
 if not endpoint:return True,"no_endpoint"
 parsed=urlsplit(endpoint)
 if parsed.username or parsed.password or "@" in parsed.netloc:return False,"credentials_in_url"
 if parsed.scheme not in {"http","https"}:return False,"unsupported_scheme"
 host=(parsed.hostname or "").lower()
 if local_provider and host not in {"127.0.0.1","localhost","::1"}:return False,"local_provider_endpoint_must_be_loopback"
 if not local_provider and parsed.scheme!="https":return False,"remote_endpoint_requires_https"
 return True,"valid"
def classify_data(text:str)->DataClassification:
 lowered=text.lower()
 if any(x in lowered for x in ("api key","password","bearer ","private key","access token")):return DataClassification.CREDENTIAL
 if any(x in lowered for x in ("medical record","bank account","private person","home address")):return DataClassification.RESTRICTED
 if any(x in lowered for x in ("secret","confidential")):return DataClassification.SECRET
 if any(x in lowered for x in ("email address","phone number","personal")):return DataClassification.PERSONAL
 return DataClassification.PROJECT_INTERNAL
def validate_action(request:ExternalActionRequest,provider:ExternalProvider)->tuple[bool,str]:
 if not provider.enabled:return False,"provider_disabled"
 if not provider.configured:return False,"provider_not_configured"
 if not provider.policy.execution_allowed:return False,"execution_disabled"
 if request.data_classification not in provider.policy.allowed_data_classes:return False,"data_egress_blocked"
 capability=next((c for c in provider.capabilities if c.name==request.capability),None)
 if capability is None:return False,"capability_not_supported"
 if not set(capability.permissions).issubset(request.permissions):return False,"permission_missing"
 if (capability.requires_approval or provider.policy.approval_required) and not request.approval_id:return False,"approval_required"
 return True,"allowed"
