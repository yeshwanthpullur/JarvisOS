"""Metadata-only current diff review."""

from __future__ import annotations

from pathlib import Path
import subprocess

from .models import DiffReview
from .repo import safe_repo_name


class DiffReviewer:
    def __init__(self, repo_root: Path, max_files: int = 20, max_diff_chars: int = 4000) -> None:
        self.repo_root = Path(repo_root)
        self.max_files = max(1, min(int(max_files), 50))
        self.max_diff_chars = max(200, min(int(max_diff_chars), 20_000))

    def _git(self, *args: str) -> str:
        result = subprocess.run(("git", *args), cwd=self.repo_root, capture_output=True, text=True, timeout=10, check=False)
        if result.returncode:
            raise RuntimeError("git_diff_read_failed")
        return result.stdout

    def review(self) -> DiffReview:
        try:
            rows = self._git("diff", "--numstat", "HEAD").splitlines()
        except (OSError, subprocess.SubprocessError, RuntimeError):
            return DiffReview((), 0, 0, "Diff metadata is unavailable.", warnings=("Git diff inspection failed safely.",))
        files: list[str] = []
        insertions = deletions = 0
        binary = False
        for row in rows:
            parts = row.split("\t", 2)
            if len(parts) != 3:
                continue
            added, removed, name = parts
            files.append(safe_repo_name(name))
            if added.isdigit():
                insertions += int(added)
            else:
                binary = True
            if removed.isdigit():
                deletions += int(removed)
            else:
                binary = True
        risks: list[str] = []
        names = " ".join(files).lower()
        if any(token in names for token in ("security", "permission", "config", "api/", "vercel")):
            risks.append("Security, configuration, or deployment boundaries changed; run focused policy tests.")
        if any(token in names for token in ("requirements", "pyproject", "package")):
            risks.append("Dependency metadata changed; review supply-chain and compatibility impact.")
        warnings: list[str] = []
        estimated_chars = (insertions + deletions) * 80
        if len(files) > self.max_files or estimated_chars > self.max_diff_chars:
            warnings.append("Diff exceeds the bounded review window; narrow the review scope for content inspection.")
        if binary:
            warnings.append("Binary diff metadata was detected; binary contents were not inspected.")
        tests = ("Run focused tests for changed subsystems.", "Run the full regression suite before commit.") if files else ("No tracked diff requires tests.",)
        summary = f"Tracked diff changes {len(files)} file(s): +{insertions}/-{deletions}. No source contents were copied."
        return DiffReview(tuple(files[: self.max_files]), insertions, deletions, summary, tuple(risks), tests, tuple(warnings))
