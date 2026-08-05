"""Runtime storage helpers for video editing plans."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class VideoEditingStorage:
    """Manage bounded runtime paths and metadata history."""

    def __init__(self, root: Path, save_metadata: bool = True, allow_overwrite: bool = False) -> None:
        self.root = root
        self.plans_dir = self.root / "plans"
        self.jobs_dir = self.root / "jobs"
        self.history_path = self.root / "history.json"
        self.save_metadata = save_metadata
        self.allow_overwrite = allow_overwrite

    def ensure(self) -> None:
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

    def plan_path(self, plan_id: str) -> Path:
        self.ensure()
        candidate = self.plans_dir / f"{plan_id}.json"
        if candidate.exists() and not self.allow_overwrite:
            raise FileExistsError("plan_exists")
        return candidate

    def metadata_path(self, plan_id: str) -> Path:
        self.ensure()
        return self.jobs_dir / f"{plan_id}.json"

    def public_path(self, path: Path | None) -> str | None:
        if path is None:
            return None
        try:
            relative = path.relative_to(self.root.parent)
            return relative.as_posix()
        except ValueError:
            return path.name

    def record(self, item: dict[str, Any]) -> str | None:
        if not self.save_metadata:
            return None
        self.ensure()
        metadata_path = self.metadata_path(str(item["plan_id"]))
        self._write_json(metadata_path, item)
        history = self._load_history()
        history = [entry for entry in history if entry.get("plan_id") != item["plan_id"]]
        history.append(item)
        history = history[-20:]
        self._write_json(self.history_path, {"schema_version": 1, "plans": history})
        return self.public_path(metadata_path)

    def load_history(self, limit: int = 10) -> tuple[dict[str, Any], ...]:
        return tuple(self._load_history()[-max(1, limit):][::-1])

    def load_plan(self, plan_id: str) -> dict[str, Any] | None:
        path = self.metadata_path(plan_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return None

    def _load_history(self) -> list[dict[str, Any]]:
        if not self.history_path.exists():
            return []
        try:
            payload = json.loads(self.history_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return []
        plans = payload.get("plans", [])
        return plans if isinstance(plans, list) else []

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
