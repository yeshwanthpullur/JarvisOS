"""External coding-tool adapters constrained to preview and approval handoff."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import re
import subprocess

from .environment import ToolEnvironmentRegistry


@dataclass(slots=True)
class ExternalCodingTask:
    task_id: str; request_summary: str; selected_tool: str; mode: str; likely_files: tuple[str, ...]; required_tests: tuple[str, ...]; status: str = "planned"; approval_required: bool = True; write_allowed: bool = False; shell_allowed: bool = False; network_allowed: bool = False; created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ExternalCodingControlPlane:
    def __init__(self, root: Path, tools: ToolEnvironmentRegistry) -> None:
        self.root = root.resolve(); self.tools = tools; self.tasks: dict[str, ExternalCodingTask] = {}; self.audit: list[dict[str, object]] = []

    def plan(self, request: str) -> ExternalCodingTask:
        safe = re.sub(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*\S+", r"\1=[REDACTED]", request)[:600]
        aider = self.tools.inspect("aider"); interpreter = self.tools.inspect("open_interpreter")
        selected = "aider" if aider and aider.install_status == "installed" else "open_interpreter" if interpreter and interpreter.install_status == "installed" else "jarvis_coding_agent"
        task = ExternalCodingTask(f"code-{uuid4().hex[:12]}", safe, selected, "plan_only", (), ("focused tests", "relevant regression", "git diff --check"))
        self.tasks[task.task_id] = task; self.audit.append({"task_id": task.task_id, "operation": "plan", "tool": selected, "status": task.status}); self.audit = self.audit[-100:]
        return task

    def apply(self, task_id: str, *, approval_id: str = "") -> str:
        task = self.tasks.get(task_id)
        if task is None: return "coding_task_not_found"
        if not approval_id: return "approval_required"
        return "external_tool_unavailable" if task.selected_tool == "jarvis_coding_agent" else "broker_handoff_required"

    def repo_metadata(self, operation: str) -> str:
        commands = {"status": ("git", "status", "--short"), "diff": ("git", "diff", "--stat"), "history": ("git", "log", "--oneline", "-8"), "verify": ("git", "rev-parse", "--is-inside-work-tree")}
        command = commands.get(operation)
        if command is None: return "unsupported_git_metadata_operation"
        try:
            result = subprocess.run(command, cwd=self.root, capture_output=True, text=True, timeout=5, check=False)
        except (OSError, subprocess.SubprocessError): return "git_metadata_unavailable"
        output = (result.stdout or result.stderr).replace(str(self.root), "[REPOSITORY]")[:3000].strip()
        return output or "clean_or_empty"

    def status(self) -> dict[str, object]:
        return {"authority": "jarvis_coding_agent", "mode": "plan_only", "aider": self.tools.inspect("aider").health_status.value, "open_interpreter": self.tools.inspect("open_interpreter").health_status.value, "file_write": False, "shell": False, "network": False, "tasks": len(self.tasks)}
