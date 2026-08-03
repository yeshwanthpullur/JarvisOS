"""Bounded, validated access to the project limitations register."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any


VALID_STATUSES = frozenset({"fixed", "open", "deferred", "blocked", "experimental"})
VALID_CATEGORIES = frozenset({
    "fix_now",
    "next_roadmap_milestone",
    "blocked_hardware_environment",
    "blocked_external_service_cost",
    "deferred_by_design",
    "intentionally_restricted",
})


class LimitationsRegisterError(ValueError):
    """Raised when the bounded register contract is invalid."""


class LimitationsRegister:
    """Read and summarize the repository-owned limitations register."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(__file__).resolve().parents[1] / "docs" / "limitations_register.json"

    def load(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError) as exc:
            raise LimitationsRegisterError("limitations register is unavailable") from exc
        items = data.get("limitations")
        counts = data.get("counts")
        if not isinstance(items, list) or not isinstance(counts, dict) or len(items) > 200:
            raise LimitationsRegisterError("limitations register shape is invalid")
        ids = [item.get("limitation_id") for item in items if isinstance(item, dict)]
        statuses = Counter(item.get("status") for item in items if isinstance(item, dict))
        if len(ids) != len(items) or len(set(ids)) != len(ids):
            raise LimitationsRegisterError("limitations register IDs are invalid")
        if any(status not in VALID_STATUSES for status in statuses):
            raise LimitationsRegisterError("limitations register status is invalid")
        if counts.get("total") != len(items) or counts.get("fixed") != statuses["fixed"]:
            raise LimitationsRegisterError("limitations register counts do not reconcile")
        if counts.get("still_open") != len(items) - statuses["fixed"]:
            raise LimitationsRegisterError("limitations register open count does not reconcile")
        return data

    def command(self, name: str, arguments: tuple[str, ...] = ()) -> str:
        data = self.load()
        items = data["limitations"]
        counts = data["counts"]
        if name in {"limitations status", "limitations summary"}:
            categories = data.get("review", {}).get("category_totals", {})
            restricted = int(categories.get("intentionally_restricted", 0))
            blocked = int(categories.get("blocked_hardware_environment", 0)) + int(categories.get("blocked_external_service_cost", 0))
            return (
                f"Limitations: total={counts['total']} fixed={counts['fixed']} open={counts['still_open']} "
                f"restricted={restricted} blocked={blocked} next={data.get('next_major_limitation_id', 'unknown')}. "
                "Details: docs/LIMITATIONS_REGISTER.md"
            )
        if name in {"limitations open", "limitations fixed"}:
            wanted = "fixed" if name.endswith("fixed") else "open"
            selected = [item for item in items if (item["status"] == "fixed") == (wanted == "fixed")][:10]
            label = "Fixed" if wanted == "fixed" else "Open"
            body = "; ".join(f"{item['limitation_id']} {item['title']}" for item in selected)
            remaining = (counts["fixed"] if wanted == "fixed" else counts["still_open"]) - len(selected)
            suffix = f"; plus {remaining} more" if remaining > 0 else ""
            return f"{label} limitations: {body}{suffix}."
        if name == "limitations next":
            identifier = data.get("next_major_limitation_id")
            item = next((entry for entry in items if entry["limitation_id"] == identifier), None)
            if item is None:
                return "No priority limitation is recorded."
            return f"Next limitation: {identifier} {item['title']} Action: {item.get('recommended_action') or item.get('next_owner_prompt')}."
        if name == "limitations show":
            identifier = arguments[0].upper() if arguments else ""
            item = next((entry for entry in items if entry["limitation_id"] == identifier), None)
            if item is None:
                return "Limitation not found. Use limitations open or limitations fixed."
            return (
                f"{identifier}: {item['title']} status={item['status']} severity={item['severity']} "
                f"category={item.get('review_category', 'historical')} evidence={str(item['evidence'])[:240]} "
                f"next={item.get('recommended_action') or item.get('next_owner_prompt') or 'none'}."
            )
        if name == "limitations category":
            category = "_".join(arguments).lower()
            if category not in VALID_CATEGORIES:
                return "Unknown category. Use fix_now, next_roadmap_milestone, blocked_hardware_environment, blocked_external_service_cost, deferred_by_design, or intentionally_restricted."
            selected = [item for item in items if item.get("review_category") == category][:10]
            return f"Limitations category {category}: " + ("; ".join(item["limitation_id"] for item in selected) or "none") + "."
        return "Limitations commands: limitations status, open, fixed, show <id>, category <name>, next, summary."
