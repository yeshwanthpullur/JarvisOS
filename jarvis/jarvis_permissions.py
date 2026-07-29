"""Executive permission metadata."""

from __future__ import annotations

from enum import StrEnum


class JarvisPermission(StrEnum):
    """Declarative permissions available to the Executive Core."""

    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    TASKS = "tasks"
    PLUGINS = "plugins"
    PROVIDERS = "providers"
    AGENTS = "agents"
    AGENT_CREATOR = "agent_creator"
    CONFIGURATION = "configuration"
    HEALTH = "health"
    METRICS = "metrics"
    TOOL_DISCOVER = "tool.discover"
    TOOL_INSPECT = "tool.inspect"
    TOOL_RECOMMEND = "tool.recommend"
    TOOL_PREPARE = "tool.prepare"
    TOOL_EXECUTE = "tool.execute"
    TOOL_CANCEL = "tool.cancel"
    TOOL_READ_DATA = "tool.read_data"
    TOOL_WRITE_DATA = "tool.write_data"
    TOOL_NETWORK_ACCESS = "tool.network_access"
    TOOL_FILE_READ = "tool.file_read"
    TOOL_FILE_WRITE = "tool.file_write"
    TOOL_PROCESS_EXECUTE = "tool.process_execute"
    TOOL_BROWSER_CONTROL = "tool.browser_control"
    TOOL_COMMUNICATION_SEND = "tool.communication_send"
    TOOL_CREDENTIAL_USE = "tool.credential_use"
    TOOL_ADMINISTRATIVE_ACTION = "tool.administrative_action"
    TOOL_AUDIT_READ = "tool.audit_read"
