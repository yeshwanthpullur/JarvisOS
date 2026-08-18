"""Local automation classification and previews over existing Phase 4 authority."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
import os
import platform
import shutil


class LocalAction(StrEnum):
    READ_SYSTEM_STATUS="read_system_status"; OPEN_APPLICATION="open_application"; CLOSE_APPLICATION="close_application"; OPEN_FILE="open_file"; READ_FILE="read_file"; WRITE_FILE="write_file"; MOVE_FILE="move_file"; COPY_FILE="copy_file"; DELETE_FILE="delete_file"; CREATE_FOLDER="create_folder"; RUN_COMMAND="run_command"; RUN_SCRIPT="run_script"; INSTALL_SOFTWARE="install_software"; UNINSTALL_SOFTWARE="uninstall_software"; CHANGE_SETTING="change_setting"; NETWORK_CHANGE="network_change"; POWER_ACTION="power_action"; SCHEDULE_TASK="schedule_task"; CANCEL_TASK="cancel_task"; START_SERVICE="start_service"; STOP_SERVICE="stop_service"; UNKNOWN="unknown"


@dataclass(frozen=True, slots=True)
class ActionPreview:
    action: LocalAction; target: str; expected_effect: str; risk: str; approval_required: bool; rollback_available: bool; allowed: bool; reason: str


class LocalAutomationControlPlane:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve(); self.enabled = False; self.desktop_enabled = False; self.write_allowed = False; self.delete_allowed = False; self.command_enabled = False; self.arbitrary_shell = False; self.audit: list[dict[str, object]] = []

    def preview(self, action: LocalAction, target: str = "") -> ActionPreview:
        safe_target = Path(target).name[:160] if target else "none"
        if action is LocalAction.READ_SYSTEM_STATUS:
            return ActionPreview(action, safe_target, "Read bounded local status metadata.", "low", False, False, True, "read_only")
        critical = action in {LocalAction.INSTALL_SOFTWARE, LocalAction.UNINSTALL_SOFTWARE, LocalAction.NETWORK_CHANGE, LocalAction.POWER_ACTION, LocalAction.CHANGE_SETTING, LocalAction.START_SERVICE, LocalAction.STOP_SERVICE}
        writes = action in {LocalAction.WRITE_FILE, LocalAction.MOVE_FILE, LocalAction.COPY_FILE, LocalAction.DELETE_FILE, LocalAction.CREATE_FOLDER}
        allowed = False
        reason = "blocked_critical_action" if critical else "write_disabled" if writes else "execution_disabled"
        return ActionPreview(action, safe_target, "No action performed; route exact scope through Policy, Approval, and Broker.", "critical" if critical else "high", True, action in {LocalAction.WRITE_FILE, LocalAction.MOVE_FILE, LocalAction.COPY_FILE, LocalAction.CREATE_FOLDER}, allowed, reason)

    def system_status(self) -> dict[str, object]:
        usage = shutil.disk_usage(self.root)
        return {"platform": platform.system(), "python": platform.python_version(), "cpu_count": os.cpu_count() or 0, "disk_free_mb": usage.free // (1024 * 1024), "process_list_exposed": False, "gpu": "unknown", "read_only": True}

    def app_list(self) -> tuple[str, ...]:
        return ("notepad", "calculator") if platform.system() == "Windows" else ()

    def status(self) -> dict[str, object]:
        return {"enabled": self.enabled, "desktop": self.desktop_enabled, "filesystem_read": True, "filesystem_write": self.write_allowed, "delete": self.delete_allowed, "commands": self.command_enabled, "arbitrary_shell": self.arbitrary_shell, "authority": "execution_policy_approval_broker"}
