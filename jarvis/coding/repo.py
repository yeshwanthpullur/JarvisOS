"""Read-only, bounded Git repository inspection."""

from __future__ import annotations

from pathlib import Path, PurePath, PureWindowsPath
import subprocess

from .models import RepoInspection
from .safety import redact_secret_shaped


_SENSITIVE_NAMES = {".env", ".env.local", "credentials.json", "secrets.json"}


def safe_repo_name(value: str) -> str:
    cleaned = redact_secret_shaped(value.strip().replace("\\", "/"))
    if PurePath(cleaned).is_absolute() or PureWindowsPath(cleaned).is_absolute():
        return "[private-path]"
    if any(part.lower() in _SENSITIVE_NAMES for part in cleaned.split("/")):
        return "[sensitive-file]"
    return cleaned[:240]


class RepoInspector:
    def __init__(self, repo_root: Path, max_files: int = 20) -> None:
        self.repo_root = Path(repo_root)
        self.max_files = max(1, min(int(max_files), 50))

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ("git", *args),
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode:
            raise RuntimeError("git_read_failed")
        return result.stdout.rstrip("\r\n")

    def inspect(self) -> RepoInspection:
        try:
            branch = self._git("branch", "--show-current").strip() or "detached"
            head = self._git("rev-parse", "HEAD").strip()
            status_lines = self._git("status", "--short").splitlines()
            recent = self._git("log", "--oneline", "-5").splitlines()
        except (OSError, subprocess.SubprocessError, RuntimeError):
            return RepoInspection("unavailable", "unavailable", False, warnings=("Git repository inspection is unavailable.",))

        staged: list[str] = []
        changed: list[str] = []
        untracked: list[str] = []
        for line in status_lines:
            if len(line) < 4:
                continue
            code, raw_name = line[:2], line[3:]
            name = safe_repo_name(raw_name.split(" -> ")[-1])
            if code == "??":
                untracked.append(name)
            else:
                if code[0] != " ":
                    staged.append(name)
                if code[1] != " ":
                    changed.append(name)
        warnings = ("File lists were truncated.",) if max(len(staged), len(changed), len(untracked)) > self.max_files else ()
        return RepoInspection(
            branch=branch[:80],
            head=head[:64],
            tracked_clean=not staged and not changed,
            untracked_summary=tuple(untracked[: self.max_files]),
            staged_files=tuple(staged[: self.max_files]),
            changed_files=tuple(changed[: self.max_files]),
            recent_commits=tuple(item[:240] for item in recent[:5]),
            warnings=warnings,
        )
