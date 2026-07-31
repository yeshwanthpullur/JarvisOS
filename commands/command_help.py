"""Command help generator."""

from __future__ import annotations

from commands.command_registry import CommandRegistry


class CommandHelp:
    """Generates help text from the registry."""

    initialized = True

    def render(self, registry: CommandRegistry) -> str:
        """Render help."""
        enabled = {record.name for record in registry.list_commands() if record.enabled}
        primary = (
            ("local only on/off", "Keep provider requests local or restore automatic routing"),
            ("local use <model>", "Select an installed local model"),
            ("voice status", "Show voice and Windows SAPI readiness"),
            ("voice output on/off", "Enable or disable spoken assistant replies"),
            ("voice say <text>", "Speak text immediately through local TTS"),
            ("voice input status/on/off", "Show or control explicit local voice input"),
            ("voice listen", "Capture one utterance when local STT is ready"),
            ("voice cleanup", "Remove temporary voice audio"),
            ("provider status", "Show provider mode and current selection"),
            ("tools status", "Show registered tool readiness"),
            ("project status", "Show release, MVP health, and next milestone"),
            ("help", "Show this guide"),
            ("exit", "Shut down JARVIS cleanly"),
        )
        lines = ["Available commands", ""]
        for syntax, description in primary:
            command_name = syntax.replace(" on/off", "").replace(" <model>", "").replace(" <text>", "")
            if command_name in enabled or syntax in {"local only on/off", "voice output on/off"}:
                lines.append(f"  {syntax:<24} {description}")
        lines.extend(("", "Use '<area> status' or '<area> list' for more detail."))
        return "\n".join(lines)
