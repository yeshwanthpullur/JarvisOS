"""Ignored metadata-only history for Coding Agent jobs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CodingHistoryRecord:
    request_id: str
    intent: str
    status: str
    risk_level: str
    created_at: str


class CodingHistoryStore:
    def __init__(self, base_dir: Path, max_records: int = 25) -> None:
        self.base_dir = Path(base_dir)
        self.max_records = max(1, min(int(max_records), 100))
        self.path = self.base_dir / "coding_history.json"

    def load(self) -> tuple[CodingHistoryRecord, ...]:
        if not self.path.exists():
            return ()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            records = tuple(CodingHistoryRecord(**item) for item in payload.get("records", []))
        except (OSError, ValueError, TypeError):
            return ()
        return records[-self.max_records :]

    def save(self, records: tuple[CodingHistoryRecord, ...]) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        payload = {"records": [asdict(item) for item in records[-self.max_records :]]}
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temp, self.path)
