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
            ("voice listen", "Capture one utterance when local Vosk STT is ready"),
            ("voice listen send", "Explicitly submit a transcript to JARVIS"),
            ("voice input test", "Run one explicit local capture/transcription test"),
            ("voice cleanup", "Remove temporary voice audio"),
            ("vision status", "Show local vision readiness"),
            ("vision describe <path>", "Describe an image with a permitted model"),
            ("vision ask <path> <question>", "Ask a question about an image"),
            ("sync status", "Show local queue and remote sync readiness"),
            ("sync on/off", "Enable manual queue mode or disable sync"),
            ("sync add project_status", "Queue one sanitized project snapshot"),
            ("sync queue summary", "Show bounded local queue counts"),
            ("sync run", "Attempt manual sync when a real backend exists"),
            ("web status", "Show safe browser foundation readiness"),
            ("web open <url>", "Policy-check a read-only browser request"),
            ("web title/url/snapshot", "Read metadata from an active web session"),
            ("web policy", "Show blocked and permitted web actions"),
            ("mobile status", "Show planning-only mobile foundation status"),
            ("mobile policy", "Show blocked and permitted mobile actions"),
            ("mobile capabilities", "Separate current planning from future control"),
            ("mobile setup", "Show safe future Android setup guidance"),
            ("mobile plan <task>", "Plan without accessing or controlling a phone"),
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
