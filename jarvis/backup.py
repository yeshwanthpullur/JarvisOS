"""Small, integrity-checked local backup foundation.

Only explicitly supplied files are copied.  The manager rejects secret-shaped
filenames and never discovers or backs up a whole workspace automatically.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path


_BLOCKED_NAMES = {".env", ".env.local", ".env.production", "credentials.json", "token.json"}


@dataclass(frozen=True, slots=True)
class BackupRecord:
    backup_id: str
    source_name: str
    backup_name: str
    size_bytes: int
    sha256: str
    verified: bool


class BackupManager:
    """Create and restore bounded local state backups with explicit paths."""

    def __init__(self, root: Path, *, max_bytes: int = 2_000_000) -> None:
        self.root = Path(root)
        self.max_bytes = max(1, min(int(max_bytes), 20_000_000))

    def _validate_source(self, source: Path) -> Path:
        source = Path(source)
        if source.name.lower() in _BLOCKED_NAMES or "secret" in source.name.lower():
            raise ValueError("secret_backup_blocked")
        if not source.is_file():
            raise ValueError("backup_source_unavailable")
        if source.stat().st_size > self.max_bytes:
            raise ValueError("backup_source_too_large")
        return source

    @staticmethod
    def _digest(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65_536), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def create(self, source: Path, *, backup_id: str = "local-state") -> BackupRecord:
        source = self._validate_source(source)
        safe_id = "".join(char for char in backup_id if char.isalnum() or char in "-_")[:80] or "local-state"
        self.root.mkdir(parents=True, exist_ok=True)
        destination = self.root / f"{safe_id}.backup"
        shutil.copyfile(source, destination)
        digest = self._digest(destination)
        manifest = self.root / f"{safe_id}.json"
        manifest.write_text(json.dumps({"backup_id": safe_id, "source_name": source.name, "backup_name": destination.name, "size_bytes": destination.stat().st_size, "sha256": digest}, sort_keys=True), encoding="utf-8")
        return BackupRecord(safe_id, source.name, destination.name, destination.stat().st_size, digest, self._digest(destination) == digest)

    def verify(self, backup_id: str) -> BackupRecord:
        safe_id = "".join(char for char in backup_id if char.isalnum() or char in "-_")[:80]
        manifest = self.root / f"{safe_id}.json"
        if not manifest.is_file():
            raise ValueError("backup_manifest_unavailable")
        data = json.loads(manifest.read_text(encoding="utf-8"))
        destination = self.root / str(data.get("backup_name", ""))
        if not destination.is_file() or destination.stat().st_size > self.max_bytes:
            raise ValueError("backup_artifact_unavailable")
        digest = self._digest(destination)
        verified = digest == str(data.get("sha256", ""))
        return BackupRecord(safe_id, str(data.get("source_name", ""))[:120], destination.name[:120], destination.stat().st_size, digest, verified)

    def restore(self, backup_id: str, destination: Path) -> BackupRecord:
        record = self.verify(backup_id)
        if not record.verified:
            raise ValueError("backup_integrity_failed")
        target = Path(destination)
        if target.name.lower() in _BLOCKED_NAMES or "secret" in target.name.lower():
            raise ValueError("secret_restore_blocked")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.root / record.backup_name, target)
        return record
