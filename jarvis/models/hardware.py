"""Non-invasive hardware hints for future local model routing."""

from __future__ import annotations

import os
import platform


def safe_hardware_summary() -> dict[str, object]:
    return {
        "cpu_available": bool(os.cpu_count()),
        "cpu_count_bucket": "1-4" if (os.cpu_count() or 0) <= 4 else "5-8" if (os.cpu_count() or 0) <= 8 else "9+",
        "architecture": platform.machine()[:32] or "unknown",
        "ram_bucket": "unknown",
        "gpu": "unknown",
        "cuda": "unknown",
        "local_only": True,
    }

