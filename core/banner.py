"""Console banner for the JARVIS OS bootstrap."""

from __future__ import annotations


BANNER_TEXT = r"""
     ____.  ___      __________  ____   ____  .___  _________
    |    | /   \     \______   \/  _ \ /  _ \ |   |/   _____/
    |    |/  ^  \     |       _/  /_\ \  /_\ \|   |\_____  \
/\__|    /  /_\  \    |    |   \  \_/ /\  \_/ /   |/        \
\__________/   \__\   |____|_  /\___  / \___  /|___/_______  /
                            \/     \/      \/             \/
"""


def render_banner() -> str:
    """Return the startup banner shown when JARVIS OS boots."""
    return f"{BANNER_TEXT}\nJARVIS OS - Runnable Foundation\n"


def display_banner() -> None:
    """Display the startup banner."""
    print(render_banner())

