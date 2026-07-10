"""Application entry point for JARVIS OS."""

from __future__ import annotations

from core import StartupManager


def main() -> int:
    """Start the JARVIS OS runnable application skeleton."""
    return StartupManager().run()


if __name__ == "__main__":
    raise SystemExit(main())
