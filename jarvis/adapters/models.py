"""Typed manifest-only MCP and external adapter models."""
from dataclasses import dataclass,field
from enum import StrEnum
from jarvis.foundation_common import new_id,now,validate_items,validate_request_text,validate_text
class AdapterIntent(StrEnum):ADAPTER_STATUS="adapter_status";ADAPTER_PLANNING="adapter_planning";MCP_SERVER_PLAN="mcp_server_plan";PLUGIN_INTEGRATION_PLAN="plugin_integration_plan";PERMISSION_REVIEW="permission_review";CAPABILITY_REVIEW="capability_review";TOOL_EXECUTION_REQUEST="tool_execution_request";CREDENTIAL_REQUIRED_REQUEST="credential_required_request";INSTALL_PLUGIN_REQUEST="install_plugin_request";EXTERNAL_SERVICE_REQUEST="external_service_request";UNSAFE_TOOL_REQUEST="unsafe_tool_request";UNKNOWN="unknown"
class AdapterType(StrEnum):MCP_SERVER="mcp_server";LOCAL_TOOL="local_tool";EXTERNAL_PLUGIN="external_plugin";API_CONNECTOR="api_connector";WEBHOOK_CONNECTOR="webhook_connector";UNKNOWN="unknown"
class AdapterRiskLevel(StrEnum):LOW="low";MEDIUM="medium";HIGH="high";CRITICAL="critical"
class AdapterStatus(StrEnum):PLANNED="planned";MANIFEST_ONLY="manifest_only";DISABLED="disabled";NOT_CONFIGURED="not_configured";BLOCKED="blocked";UNAVAILABLE="unavailable"
@dataclass(frozen=True,slots=True)
class AdapterRequest:
 request:str;normalized_request:str;intent:AdapterIntent=AdapterIntent.UNKNOWN;scope:str="manifest_only";risk_level:AdapterRiskLevel=AdapterRiskLevel.LOW;request_id:str=field(default_factory=new_id);created_at:str=field(default_factory=now)
 def __post_init__(self):validate_request_text(self.request);validate_request_text(self.normalized_request)
@dataclass(frozen=True,slots=True)
class AdapterManifest:
 adapter_id:str;display_name:str;adapter_type:AdapterType;provider:str;status:AdapterStatus=AdapterStatus.NOT_CONFIGURED;configured:bool=False;enabled:bool=False;execution_available:bool=False;requires_credentials:bool=False;required_permissions:tuple[str,...]=();supported_capabilities:tuple[str,...]=();blocked_capabilities:tuple[str,...]=("execute","credentials","network");warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class AdapterPermission:
 permission_id:str;name:str;category:str;risk_level:AdapterRiskLevel;required:bool;granted:bool=False;reason:str="Disabled by default.";warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class AdapterCapabilityStatus:
 mcp_supported_as_manifest:bool=True;mcp_runtime_available:bool=False;external_plugins_supported_as_manifest:bool=True;external_plugin_execution_available:bool=False;network_access_allowed:bool=False;credentials_available:bool=False;background_servers_allowed:bool=False;warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class AdapterPlan:
 request_id:str;intent:AdapterIntent;summary:str;target_adapter:str;proposed_steps:tuple[str,...];required_permissions:tuple[str,...]=();blocked_actions:tuple[str,...]=("execute","install","read_credentials","start_server","network_call");configuration_needed:tuple[str,...]=();risk_level:AdapterRiskLevel=AdapterRiskLevel.LOW;approval_required:bool=True;execution_available:bool=False;status:AdapterStatus=AdapterStatus.PLANNED;warnings:tuple[str,...]=();plan_id:str=field(default_factory=new_id)
@dataclass(frozen=True,slots=True)
class AdapterResult:
 request_id:str;status:AdapterStatus;request:AdapterRequest|None=None;plan:AdapterPlan|None=None;manifests:tuple[AdapterManifest,...]=();capability_status:AdapterCapabilityStatus|None=None;output:str="";warnings:tuple[str,...]=();error:str|None=None
