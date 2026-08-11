"""MCP transport boundaries. No installation or arbitrary shell evaluation."""
from __future__ import annotations
import os,subprocess
from typing import Protocol,Any
from urllib.parse import urlsplit

class MCPTransport(Protocol):
 def connect(self):...
 def initialize(self):...
 def list_tools(self):...
 def list_resources(self):...
 def read_resource(self,uri):...
 def list_prompts(self):...
 def call_tool(self,name,arguments):...
 def close(self):...
 def health(self):...

class LocalStdioTransport:
 def __init__(self,executable:str,args:tuple[str,...]=(),*,allowed_executables:tuple[str,...]=(),timeout:int=10,credential_env:dict[str,str]|None=None):self.executable=executable;self.args=args;self.allowed=allowed_executables;self.timeout=timeout;self.credential_env=credential_env or {};self.process=None
 def connect(self):
  if self.executable not in self.allowed:raise PermissionError("mcp_executable_not_allowed")
  env={"PATH":os.environ.get("PATH","")} | dict(self.credential_env);self.process=subprocess.Popen([self.executable,*self.args],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,shell=False,env=env);return True
 def initialize(self):raise RuntimeError("mcp_protocol_adapter_required")
 def list_tools(self):return ()
 def list_resources(self):return ()
 def read_resource(self,uri):raise RuntimeError("mcp_protocol_adapter_required")
 def list_prompts(self):return ()
 def call_tool(self,name,arguments):raise RuntimeError("mcp_protocol_adapter_required")
 def health(self):return bool(self.process and self.process.poll() is None)
 def close(self):
  if self.process and self.process.poll() is None:
   self.process.terminate()
   try:self.process.wait(timeout=2)
   except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=2)

class HTTPMCPTransport:
 def __init__(self,endpoint:str,*,remote:bool=False,allowed_hosts:tuple[str,...]=()):
  parsed=urlsplit(endpoint);host=(parsed.hostname or "").lower()
  if parsed.username or parsed.password:raise ValueError("credentials_in_url")
  if remote and (parsed.scheme!="https" or host not in allowed_hosts):raise ValueError("remote_mcp_endpoint_blocked")
  if not remote and (parsed.scheme not in {"http","https"} or host not in {"localhost","127.0.0.1","::1"}):raise ValueError("local_mcp_endpoint_invalid")
  self.endpoint=endpoint;self.remote=remote
 def connect(self):return True
 def initialize(self):raise RuntimeError("mcp_http_protocol_adapter_required")
 def list_tools(self):return ()
 def list_resources(self):return ()
 def read_resource(self,uri):raise RuntimeError("mcp_http_protocol_adapter_required")
 def list_prompts(self):return ()
 def call_tool(self,name,arguments):raise RuntimeError("mcp_http_protocol_adapter_required")
 def close(self):return None
 def health(self):return False
