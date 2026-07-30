"""Application entry point for JARVIS OS."""

from __future__ import annotations

import argparse

from core import StartupManager


def main() -> int:
    """Start the JARVIS OS runnable application skeleton."""
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--ui", action="store_true", help="Start the local desktop interface.")
    parser.add_argument("--no-browser", action="store_true", help="Do not open the default browser in UI mode.")
    parser.add_argument("--port", type=int, help="Override the configured local interface port.")
    arguments = parser.parse_args()
    if arguments.ui:
        from server.local_interface import run_local_interface

        return run_local_interface(port=arguments.port, open_browser=not arguments.no_browser)
    return StartupManager().run()


if __name__ == "__main__":
    raise SystemExit(main())
