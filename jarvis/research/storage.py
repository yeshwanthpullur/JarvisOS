"""Ignored runtime storage for bounded research history."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import asdict
from pathlib import Path
import json


@dataclass(frozen=True, slots=True)
class ResearchHistoryRecord:
    request_id: str
    query: str
    status: str
    created_at: str = "phase3"


class ResearchHistoryStore:
    def __init__(self, base_dir: Path, max_records: int = 50) -> None:
        self.base_dir = Path(base_dir)
        self.max_records = max(1, min(int(max_records), 100))
        self.path = self.base_dir / "research_history.json"

    def load(self) -> tuple[ResearchHistoryRecord, ...]:
        if not self.path.exists():
            return ()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        items = [ResearchHistoryRecord(**item) for item in data.get("records", [])]
        return tuple(items[-self.max_records :])

    def save(self, records: tuple[ResearchHistoryRecord, ...]) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        payload = {"records": [asdict(record) for record in records[-self.max_records :]]}
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
