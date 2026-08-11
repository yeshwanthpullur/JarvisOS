"""Bounded MCP registry, discovery, resource, and result models."""
from dataclasses import dataclass,field
from enum import StrEnum
from typing import Any
from jarvis.foundation_common import new_id

class MCPTransportType(StrEnum):LOCAL_STDIO="local_stdio";LOCAL_HTTP="local_http";REMOTE_HTTP="remote_http"
class MCPServerState(StrEnum):REGISTERED="registered";DISABLED="disabled";UNCONFIGURED="unconfigured";CONFIGURED="configured";CREDENTIAL_MISSING="credential_missing";TRUST_UNVERIFIED="trust_unverified";TRUSTED_FOR_DISCOVERY="trusted_for_discovery";TRUSTED_FOR_READ="trusted_for_read";TRUSTED_FOR_SPECIFIC_EXECUTION="trusted_for_specific_execution";STARTING="starting";RUNNING="running";REACHABLE="reachable";PROTOCOL_READY="protocol_ready";DEGRADED="degraded";RATE_LIMITED="rate_limited";STOPPED="stopped";BLOCKED="blocked";ERROR="error"
class MCPTrustState(StrEnum):UNKNOWN="unknown";BLOCKED="blocked";REVIEWED="reviewed";TRUSTED_FOR_DISCOVERY="trusted_for_discovery";TRUSTED_FOR_RESOURCES="trusted_for_resources";TRUSTED_FOR_SPECIFIC_TOOLS="trusted_for_specific_tools"
class MCPToolCategory(StrEnum):READ="read";SEARCH="search";RETRIEVE="retrieve";CREATE="create";MODIFY="modify";DELETE="delete";EXECUTE="execute";SEND="send";PUBLISH="publish";UPLOAD="upload";DOWNLOAD="download";UNKNOWN="unknown"
@dataclass(frozen=True,slots=True)
class MCPServerManifest:
 server_id:str;display_name:str;transport:MCPTransportType;source_type:str="local_config";executable_ref:str="";args:tuple[str,...]=();endpoint:str="";required_credentials:tuple[str,...]=();allowed_tools:tuple[str,...]=();denied_tools:tuple[str,...]=();trust_state:MCPTrustState=MCPTrustState.UNKNOWN;enabled:bool=False;notes:str=""
@dataclass(slots=True)
class MCPServer:
 manifest:MCPServerManifest;state:MCPServerState=MCPServerState.REGISTERED;reachable:bool=False;protocol_ready:bool=False;tool_count:int=0;resource_count:int=0;prompt_count:int=0;health_status:str="not_checked";last_checked_at:str="never";limitations:tuple[str,...]=();warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class MCPTool:
 server_id:str;tool_name:str;display_name:str;description_summary:str;input_schema_summary:str="{}";category:MCPToolCategory=MCPToolCategory.UNKNOWN;read_only:bool=False;side_effecting:bool=True;permission:str="mcp_execute";risk_level:str="high";approval_required:bool=True;trusted:bool=False;enabled:bool=False;execution_available:bool=False;limitations:tuple[str,...]=();warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class MCPResource:
 server_id:str;resource_uri_ref:str;display_name:str;mime_type:str="text/plain";estimated_size:int=0;classification:str="external_untrusted";readable:bool=False;trusted:bool=False;limitations:tuple[str,...]=();warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class MCPToolResult:
 server_id:str;tool_name:str;status:str;result_type:str="metadata";bounded_summary:str="";artifact_refs:tuple[str,...]=();duration_ms:int=0;data_classification:str="external_untrusted";warnings:tuple[str,...]=();error:str|None=None;request_id:str=field(default_factory=new_id)
@dataclass(frozen=True,slots=True)
class MCPPolicy:
 enabled:bool=True;allow_local_stdio:bool=True;allow_local_http:bool=True;allow_remote_http:bool=False;allow_tool_execution:bool=False;allow_resource_read:bool=True;allow_prompts:bool=False;allow_installation:bool=False;allow_scheduled_execution:bool=False;require_approval_for_side_effects:bool=True;max_servers:int=16;max_tools_per_server:int=50;max_resources_per_server:int=50;max_result_chars:int=8000;max_concurrent_calls:int=2;startup_timeout_seconds:int=10;call_timeout_seconds:int=30;max_retries:int=1;health_cache_seconds:int=60;save_history:bool=True;max_history_items:int=100;redact_sensitive_values:bool=True
