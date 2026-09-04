"""Safe adapter contracts for optional external coding workers."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import os
import shutil
import subprocess
from typing import Callable, Protocol

from .models import (
    WorkerCapabilities,
    WorkerError,
    WorkerRecord,
    WorkerResult,
    WorkerStatus,
    WorkerTask,
    WorkerTaskStatus,
    WorkspaceMode,
    bounded,
    now,
)


Runner = Callable[[tuple[str, ...], int], tuple[int, str, str]]


def safe_runner(command: tuple[str, ...], timeout_seconds: int) -> tuple[int, str, str]:
    """Run a bounded metadata command without a shell."""
    def clean_stream(value: str, limit: int) -> str:
        lines = tuple(bounded(line, 500) for line in value.splitlines()[:128])
        text = "\n".join(line for line in lines if line)
        return text if len(text) <= limit else text[: limit - 3] + "..."

    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=max(1, min(timeout_seconds, 30)),
            shell=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return process.returncode, clean_stream(process.stdout, 16_000), clean_stream(process.stderr, 2000)
    except (OSError, subprocess.SubprocessError) as exc:
        return 127, "", f"{type(exc).__name__}: metadata command unavailable"


class WorkerAdapter(Protocol):
    worker_id: str

    def detect(self) -> WorkerRecord: ...
    def health(self) -> WorkerRecord: ...
    def capabilities(self) -> WorkerCapabilities: ...
    def start_task(self, task: WorkerTask) -> WorkerResult: ...
    def status(self, task_id: str) -> WorkerResult: ...
    def stream_events(self, task_id: str) -> tuple[str, ...]: ...
    def poll(self, task_id: str) -> WorkerResult: ...
    def send_context(self, task_id: str, refs: tuple[str, ...]) -> WorkerResult: ...
    def request_approval(self, task_id: str, action: str) -> WorkerResult: ...
    def cancel(self, task_id: str) -> WorkerResult: ...
    def resume(self, task_id: str) -> WorkerResult: ...
    def collect_artifacts(self, task_id: str) -> tuple[object, ...]: ...
    def collect_result(self, task_id: str) -> WorkerResult: ...
    def report_status(self, task_id: str) -> WorkerResult: ...
    def finish(self, task_id: str) -> WorkerResult: ...


class MetadataWorkerAdapter:
    """Metadata and plan-only adapter; it never grants execution authority."""

    def __init__(
        self,
        worker_id: str,
        display_name: str,
        executable_candidates: tuple[str, ...],
        *,
        adapter_type: str = "subprocess_metadata",
        capabilities: WorkerCapabilities | None = None,
        workspace_modes: tuple[WorkspaceMode, ...] = (WorkspaceMode.READ_ONLY, WorkspaceMode.WORKTREE),
        runner: Runner = safe_runner,
        enabled: bool = False,
        version_args: tuple[str, ...] = ("--version",),
        reason: str = "Optional worker; disabled until explicitly governed.",
    ) -> None:
        self.worker_id = worker_id
        self.display_name = display_name
        self.executable_candidates = executable_candidates
        self.adapter_type = adapter_type
        self._capabilities = capabilities or WorkerCapabilities()
        self.workspace_modes = workspace_modes
        self.runner = runner
        self.enabled = enabled
        self.version_args = version_args
        self.reason = reason
        self._tasks: dict[str, WorkerResult] = {}
        self._events: dict[str, tuple[str, ...]] = {}
        self._executable = ""

    def _find_executable(self) -> tuple[str, str]:
        for candidate in self.executable_candidates:
            path = shutil.which(candidate)
            if path:
                return path, f"executable:{candidate}"
        return "", "not_detected"

    def detect(self) -> WorkerRecord:
        executable, source = self._find_executable()
        self._executable = executable
        detected = bool(executable)
        status = WorkerStatus.DEGRADED if detected else WorkerStatus.UNAVAILABLE
        reason = self.reason if detected else "Executable was not detected; no installation was attempted."
        return WorkerRecord(
            self.worker_id,
            self.display_name,
            self.adapter_type,
            self.executable_candidates,
            status=status,
            discovery_source=source,
            capabilities=self._capabilities,
            workspace_modes=self.workspace_modes if detected else (WorkspaceMode.UNAVAILABLE,),
            execution_enabled=False,
            approval_required=True,
            health_reason=reason,
            executable=Path(executable).name if executable else "",
            detected=detected,
            configured=False,
            authenticated=False,
            healthy=False,
            availability="detected_disabled" if detected else "unavailable",
        )

    def health(self) -> WorkerRecord:
        record = self.detect()
        if not self._executable:
            return record
        code, output, error = self.runner((self._executable, *self.version_args), 10)
        version = bounded((output or error).splitlines()[0] if (output or error) else "unknown", 120)
        return replace(
            record,
            status=WorkerStatus.DEGRADED if code == 0 else WorkerStatus.ERROR,
            detected_version=version if code == 0 else "",
            healthy=code == 0,
            availability="healthy_disabled" if code == 0 else "degraded",
            last_health_check=now(),
            health_reason=(
                "Detected and responsive; execution remains disabled pending Approval and Broker routing."
                if code == 0
                else "Detected but metadata health command failed safely."
            ),
        )

    def capabilities(self) -> WorkerCapabilities:
        return self._capabilities

    def _result(self, task: WorkerTask, status: WorkerTaskStatus, summary: str, error: WorkerError | None = None) -> WorkerResult:
        result = WorkerResult(task.task_id, self.worker_id, status, summary, error=error)
        self._tasks[task.task_id] = result
        self._events[task.task_id] = (f"{status.value}:{bounded(summary, 200)}",)
        return result

    def start_task(self, task: WorkerTask) -> WorkerResult:
        if task.worker_id != self.worker_id:
            return self._result(task, WorkerTaskStatus.BLOCKED, "Worker/task mismatch.", WorkerError("worker_mismatch", "Selected worker does not own this task."))
        if task.execution_mode not in {"plan_only", "dry_run"}:
            return self._result(task, WorkerTaskStatus.BLOCKED, "Execution requires the existing Approval, Policy, and Broker authorities.", WorkerError("execution_not_authorized", "External worker execution is disabled by default."))
        record = self.detect()
        if record.status is WorkerStatus.UNAVAILABLE:
            return self._result(task, WorkerTaskStatus.UNAVAILABLE, record.health_reason, WorkerError("worker_unavailable", record.health_reason))
        return self._result(task, WorkerTaskStatus.PLANNED, "Bounded worker plan created; no external process was started and no repository change occurred.")

    def status(self, task_id: str) -> WorkerResult:
        return self._tasks.get(task_id) or WorkerResult(task_id, self.worker_id, WorkerTaskStatus.UNAVAILABLE, "Task metadata is unavailable.")

    def stream_events(self, task_id: str) -> tuple[str, ...]:
        return self._events.get(task_id, ())[:32]

    def poll(self, task_id: str) -> WorkerResult:
        return self.status(task_id)

    def send_context(self, task_id: str, refs: tuple[str, ...]) -> WorkerResult:
        current = self.status(task_id)
        if current.status is WorkerTaskStatus.UNAVAILABLE:
            return current
        if len(refs) > 32 or any(len(ref) > 300 for ref in refs):
            return WorkerResult(task_id, self.worker_id, WorkerTaskStatus.BLOCKED, "Context reference limits exceeded.")
        return WorkerResult(task_id, self.worker_id, current.status, f"Accepted {len(refs)} opaque context references; no content was fetched.")

    def request_approval(self, task_id: str, action: str) -> WorkerResult:
        return WorkerResult(task_id, self.worker_id, WorkerTaskStatus.WAITING, f"Approval must be requested through JARVIS for action={bounded(action, 80)}; no approval was granted here.")

    def cancel(self, task_id: str) -> WorkerResult:
        current = self.status(task_id)
        if current.status in {WorkerTaskStatus.COMPLETED, WorkerTaskStatus.CANCELLED, WorkerTaskStatus.UNAVAILABLE}:
            return current
        result = WorkerResult(task_id, self.worker_id, WorkerTaskStatus.CANCELLED, "Task metadata cancelled; no process termination was needed.")
        self._tasks[task_id] = result
        return result

    def resume(self, task_id: str) -> WorkerResult:
        current = self.status(task_id)
        if current.status is not WorkerTaskStatus.CANCELLED:
            return WorkerResult(task_id, self.worker_id, WorkerTaskStatus.BLOCKED, "Only a retained cancelled plan can be resumed.")
        result = WorkerResult(task_id, self.worker_id, WorkerTaskStatus.PLANNED, "Plan resumed without starting an external process.")
        self._tasks[task_id] = result
        return result

    def collect_artifacts(self, task_id: str) -> tuple[object, ...]:
        return self.status(task_id).artifacts

    def collect_result(self, task_id: str) -> WorkerResult:
        return self.status(task_id)

    def report_status(self, task_id: str) -> WorkerResult:
        return self.status(task_id)

    def finish(self, task_id: str) -> WorkerResult:
        current = self.status(task_id)
        if current.status not in {WorkerTaskStatus.PLANNED, WorkerTaskStatus.WAITING}:
            return current
        result = WorkerResult(task_id, self.worker_id, WorkerTaskStatus.COMPLETED, "Plan-only task closed; no external action was performed.")
        self._tasks[task_id] = result
        return result


class HermesAdapter(MetadataWorkerAdapter):
    def __init__(self, runner: Runner = safe_runner) -> None:
        super().__init__(
            "hermes",
            "Hermes Agent",
            ("hermes.exe", "hermes"),
            capabilities=WorkerCapabilities(
                planning=True,
                repository_read=True,
                repository_write=True,
                streaming=True,
                cancellation=True,
                resume=True,
                artifact_collection=True,
                independent_review=True,
                sessions=True,
                tool_use=True,
                research=True,
                local_models=True,
                cloud_models=True,
                supported_task_types=("general_work", "research", "planning", "review", "scheduled_job", "goal_job"),
            ),
            runner=runner,
            reason="Detected external agent; non-authoritative and execution-disabled until explicitly approved and brokered.",
        )


class CodexAdapter(MetadataWorkerAdapter):
    """Codex metadata adapter with a non-secret login-state probe."""

    def __init__(self, runner: Runner = safe_runner) -> None:
        super().__init__(
            "codex",
            "Codex CLI",
            ("codex.cmd", "codex.exe", "codex"),
            capabilities=WorkerCapabilities(
                planning=True,
                repository_read=True,
                repository_write=True,
                streaming=True,
                cancellation=True,
                resume=True,
                artifact_collection=True,
                independent_review=True,
                sessions=True,
                tool_use=True,
                local_models=True,
                cloud_models=True,
                supported_task_types=("coding", "review", "planning", "testing"),
            ),
            runner=runner,
            reason="Detected coding worker; repository mutations remain subject to JARVIS approval and review.",
        )

    def health(self) -> WorkerRecord:
        record = super().health()
        if not record.healthy or not self._executable:
            return record
        code, output, error = self.runner((self._executable, "login", "status"), 10)
        authenticated = code == 0 and "logged in" in f"{output}\n{error}".lower()
        return replace(
            record,
            configured=authenticated,
            authenticated=authenticated,
            health_reason=(
                "Detected, responsive, and login state verified; execution remains Approval/Broker controlled."
                if authenticated
                else "Detected and responsive; login state was not verified and execution remains disabled."
            ),
        )


class OpenCodeAdapter(MetadataWorkerAdapter):
    def __init__(self, runner: Runner = safe_runner) -> None:
        super().__init__(
            "opencode",
            "OpenCode",
            ("opencode.cmd", "opencode.exe", "opencode"),
            capabilities=WorkerCapabilities(
                planning=True,
                repository_read=True,
                repository_write=True,
                streaming=True,
                cancellation=True,
                resume=True,
                artifact_collection=True,
                model_discovery=True,
                independent_review=True,
                tool_use=True,
                cloud_models=True,
                supported_task_types=("coding", "review", "model_catalog", "planning"),
            ),
            runner=runner,
            reason="Detected coding agent; model discovery is metadata-only and execution remains disabled.",
        )

    def discover_models(self) -> tuple[str, ...]:
        record = self.detect()
        if record.status is WorkerStatus.UNAVAILABLE or not self._executable:
            return ()
        code, output, _error = self.runner((self._executable, "models"), 30)
        if code != 0:
            return ()
        return tuple(
            line.strip()
            for line in output.splitlines()
            if line.strip() and "/" in line and len(line.strip()) <= 180
        )[:64]


class MunderAdapter(MetadataWorkerAdapter):
    """Optional Munder contract with bounded workspace expectations."""

    def __init__(self, runner: Runner = safe_runner) -> None:
        super().__init__(
            "munder",
            "Munder",
            ("munder.exe", "munder.cmd", "munder"),
            adapter_type="optional_workspace_adapter",
            capabilities=WorkerCapabilities(
                planning=True,
                repository_read=True,
                artifact_collection=True,
                sessions=True,
                supported_task_types=("control_room", "planning", "visualization"),
            ),
            workspace_modes=(WorkspaceMode.READ_ONLY, WorkspaceMode.ISOLATED_EXTERNAL),
            runner=runner,
            reason="Optional adapter; only explicit bounded workspaces are eligible and bypass flags are prohibited.",
        )

    @staticmethod
    def validate_workspace(workspace: Path, allowed_root: Path) -> bool:
        try:
            workspace.resolve().relative_to(allowed_root.resolve())
            return workspace.is_dir()
        except (OSError, ValueError):
            return False


def build_default_adapters(runner: Runner = safe_runner) -> tuple[MetadataWorkerAdapter, ...]:
    coding = WorkerCapabilities(
        planning=True,
        repository_read=True,
        repository_write=True,
        streaming=True,
        cancellation=True,
        resume=True,
        artifact_collection=True,
        independent_review=True,
        sessions=True,
        tool_use=True,
        cloud_models=True,
        supported_task_types=("coding", "review", "planning", "testing"),
    )
    return (
        CodexAdapter(runner),
        HermesAdapter(runner),
        OpenCodeAdapter(runner),
        MetadataWorkerAdapter("aider", "Aider", ("aider.exe", "aider.cmd", "aider"), capabilities=coding, runner=runner, reason="Detected coding worker; auto-commit and repository writes remain disabled."),
        MunderAdapter(runner),
        MetadataWorkerAdapter("claude", "Claude Code", ("claude.exe", "claude.cmd", "claude"), capabilities=coding, runner=runner),
        MetadataWorkerAdapter("gemini", "Gemini CLI", ("gemini.cmd", "gemini.exe", "gemini"), capabilities=coding, runner=runner),
        MetadataWorkerAdapter("antigravity", "Antigravity", ("antigravity.exe", "antigravity.cmd", "antigravity"), capabilities=coding, runner=runner),
        MetadataWorkerAdapter("qwen", "Qwen Code", ("qwen.cmd", "qwen.exe", "qwen"), capabilities=coding, runner=runner),
        MetadataWorkerAdapter("copilot", "GitHub Copilot CLI", ("copilot.cmd", "copilot.exe", "copilot"), capabilities=coding, runner=runner),
        MetadataWorkerAdapter("grok", "Grok CLI", ("grok.cmd", "grok.exe", "grok"), capabilities=coding, runner=runner),
        MetadataWorkerAdapter("kimi", "Kimi CLI", ("kimi.cmd", "kimi.exe", "kimi"), capabilities=coding, runner=runner),
    )
