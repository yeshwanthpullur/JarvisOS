"""Bounded public GET reader with SSRF and redirect protection."""
from dataclasses import dataclass,field
from html.parser import HTMLParser
import ipaddress,socket,time,urllib.parse,urllib.request
from jarvis.foundation_common import bounded,new_id
from jarvis.execution.broker import ExecutionBroker,ToolExecutionRequest
from jarvis.execution.models import ExecutionMode,ExecutionPermission,ExecutionRisk
@dataclass(frozen=True,slots=True)
class BrowserReadPolicy:
 allow_http:bool=False;allow_https:bool=True;allow_private_network:bool=False;allow_loopback:bool=False;allow_link_local:bool=False;allow_metadata_endpoints:bool=False;allow_redirects:bool=True;max_redirects:int=3;max_response_bytes:int=262144;max_text_chars:int=4000;default_timeout_seconds:int=8;allow_binary_downloads:bool=False;allow_authenticated_requests:bool=False;allow_cookies:bool=False;allow_javascript_execution:bool=False;allow_forms:bool=False;allow_mutating_methods:bool=False;require_approval:bool=True
@dataclass(frozen=True,slots=True)
class URLValidation:
 scheme_allowed:bool;host_allowed:bool;port_allowed:bool;public_target:bool;private_network_detected:bool;loopback_detected:bool;metadata_endpoint_detected:bool;redirect_allowed:bool;blocked_reason:str="";validation_id:str=field(default_factory=new_id)
@dataclass(frozen=True,slots=True)
class BrowserReadResult:
 request_id:str;status:str;source_ref:str="";title:str="";content_type:str="";content_length:int=0;text_preview:str="";truncated:bool=False;redirects_followed:int=0;duration_ms:int=0;warnings:tuple[str,...]=();error:str|None=None
class _Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.skip=0;self.title="";self.in_title=False
 def handle_starttag(self,t,a):
  if t in {"script","style"}:self.skip+=1
  if t=="title":self.in_title=True
 def handle_endtag(self,t):
  if t in {"script","style"} and self.skip:self.skip-=1
  if t=="title":self.in_title=False
 def handle_data(self,d):
  if not self.skip:
   self.parts.append(d)
   if self.in_title:self.title+=d
class BrowserReader:
 def __init__(self,broker:ExecutionBroker,resolver=None,opener=None):self.broker=broker;self.policy=BrowserReadPolicy();self.resolver=resolver or socket.getaddrinfo;self.opener=opener or urllib.request.build_opener();self.history=[]
 def validate_url(self,url):
  try:
   u=urllib.parse.urlsplit(url);scheme=u.scheme.lower();scheme_ok=scheme=="https" or scheme=="http" and self.policy.allow_http;port=u.port;port_ok=port in {None,80,443};host=(u.hostname or "").lower();metadata=host in {"169.254.169.254","metadata.google.internal"};ips=[]
   for x in self.resolver(host,port or (443 if scheme=="https" else 80),type=socket.SOCK_STREAM):ips.append(ipaddress.ip_address(x[4][0]))
   private=any(i.is_private or i.is_link_local or i.is_multicast or i.is_unspecified or i.is_reserved for i in ips);loop=any(i.is_loopback for i in ips);ok=scheme_ok and bool(host) and port_ok and not private and not loop and not metadata
   reason="unsafe_scheme" if not scheme_ok else "unsafe_port" if not port_ok else "private_or_internal_target" if private or loop or metadata else ""
   return URLValidation(scheme_ok,bool(host),port_ok,ok,private,loop,metadata,self.policy.allow_redirects,reason)
  except Exception:return URLValidation(False,False,False,False,False,False,False,False,"invalid_url")
 def dry_run(self,url):
  v=self.validate_url(url);return BrowserReadResult(new_id(),"dry_run_completed" if v.public_target else "blocked",source_ref=urllib.parse.urlsplit(url).hostname or "",warnings=("No network request occurred.",),error=v.blocked_reason or None)
 def read(self,url,approval_id):
  v=self.validate_url(url);host=urllib.parse.urlsplit(url).hostname or "";req=ToolExecutionRequest("browser_read","browser_reader","browser",f"read public host {host}",ExecutionMode.APPROVED_EXECUTION,ExecutionRisk.MEDIUM,(ExecutionPermission.BROWSER_READ,ExecutionPermission.NETWORK_ACCESS),(host,),approval_id,False)
  if not v.public_target:return BrowserReadResult(req.request_id,"blocked",source_ref=host,error=v.blocked_reason)
  if self.broker.route(req).status!="approved_for_executor":return BrowserReadResult(req.request_id,"approval_required",source_ref=host,error="invalid_approval")
  start=time.monotonic()
  try:
   request=urllib.request.Request(url,headers={"User-Agent":"JARVIS-Local-Read/1.0"},method="GET");response=self.opener.open(request,timeout=self.policy.default_timeout_seconds);final=response.geturl();fv=self.validate_url(final)
   if not fv.public_target:return BrowserReadResult(req.request_id,"blocked",source_ref=host,error="unsafe_redirect_target")
   ctype=response.headers.get_content_type();allowed=ctype.startswith("text/") or ctype in {"application/json","application/xml"}
   if not allowed:return BrowserReadResult(req.request_id,"blocked",source_ref=host,content_type=ctype,error="binary_content_blocked")
   raw=response.read(self.policy.max_response_bytes+1);trunc=len(raw)>self.policy.max_response_bytes;raw=raw[:self.policy.max_response_bytes];text=raw.decode(response.headers.get_content_charset() or "utf-8",errors="replace");title=""
   if ctype=="text/html":p=_Text();p.feed(text);title=bounded(p.title,200);text=" ".join(" ".join(p.parts).split())
   result=BrowserReadResult(req.request_id,"completed",host,title,ctype,len(raw),bounded(text,self.policy.max_text_chars),trunc or len(text)>self.policy.max_text_chars,0,int((time.monotonic()-start)*1000));self.history=(self.history+[result])[-25:];return result
  except Exception as e:return BrowserReadResult(req.request_id,"failed",source_ref=host,duration_ms=int((time.monotonic()-start)*1000),error=bounded(type(e).__name__,80))
