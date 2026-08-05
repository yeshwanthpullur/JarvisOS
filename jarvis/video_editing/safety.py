"""Safety policy for governed video editing requests."""

from __future__ import annotations

from .models import VideoEditingSafetyDecision


class VideoEditingSafetyPolicy:
    """Bounded safety checks for local-first editing plans."""

    _blocked_markers = (
        (("explicit sexual", "sexual content", "nsfw", "porn"), "explicit_sexual_content", "This request asks for explicit sexual content and cannot be processed.", "Create a neutral, non-explicit edit plan instead.", "high"),
        (("self-harm", "suicide", "kill myself"), "self_harm_content", "This request asks for self-harm content and cannot be processed.", "Request a supportive or educational edit plan instead.", "high"),
        (("graphic violence", "gore", "dismember", "bloody corpse"), "graphic_violence", "This request asks for graphic violence or gore and cannot be processed.", "Request a non-graphic action edit or safety-focused cut plan instead.", "high"),
        (("deepfake", "exact face of", "make this real person", "celebrity face"), "deepfake_impersonation", "This request asks to imitate or fabricate a real person's identity and cannot be processed.", "Use a fictional subject or generic scene plan instead.", "high"),
        (("face recognition", "identify this real person", "who is this person"), "identity_matching", "This request asks for identity recognition and cannot be processed.", "Request a neutral description of visible scene details instead.", "high"),
        (("private personal data", "passport number", "credit card number"), "private_data_visualization", "This request asks to expose private personal data and cannot be processed.", "Use fictional placeholders or a redacted workflow mockup instead.", "high"),
        (("illegal weapon", "weapon blueprint", "how to build a bomb"), "illegal_weapon_construction", "This request asks for dangerous weapon-construction content and cannot be processed.", "Create a benign safety or training edit plan instead.", "high"),
        (("political persuasion", "campaign poster", "propaganda"), "political_persuasion", "This request asks for political persuasion content and cannot be processed.", "Create a neutral informational plan instead.", "high"),
        (("bypass safety", "ignore your safety rules"), "safety_bypass", "This request tries to bypass editing safety controls and cannot be processed.", "Use a normal prompt that stays within the allowed policy.", "high"),
        (("hidden recording", "surveillance", "secretly record", "spy on"), "surveillance_content", "This request asks for hidden recording or surveillance and cannot be processed.", "Request a transparent, user-approved edit plan instead.", "high"),
        (("misleading evidence", "fake evidence", "make it look real"), "misleading_editing", "This request asks for deceptive or misleading edits and cannot be processed.", "Request a clearly labeled montage or illustrative edit instead.", "high"),
    )

    def __init__(self, max_prompt_chars: int = 600, max_source_media_items: int = 12) -> None:
        self.max_prompt_chars = max_prompt_chars
        self.max_source_media_items = max_source_media_items

    def assess(self, prompt: str, source_media: tuple[str, ...] = ()) -> VideoEditingSafetyDecision:
        normalized = " ".join(prompt.lower().split())
        if not normalized:
            return VideoEditingSafetyDecision(
                allowed=False,
                category="invalid_prompt",
                reason="A prompt is required before video editing can be planned.",
                safe_alternative="Describe the edit you want in one clear sentence.",
                severity="low",
            )
        if len(prompt) > self.max_prompt_chars:
            return VideoEditingSafetyDecision(
                allowed=False,
                category="prompt_too_long",
                reason=f"Prompts must stay within {self.max_prompt_chars} characters.",
                safe_alternative="Shorten the request to the core edit goal.",
                severity="low",
            )
        if len(source_media) > self.max_source_media_items:
            return VideoEditingSafetyDecision(
                allowed=False,
                category="too_many_source_files",
                reason=f"Source media lists must stay within {self.max_source_media_items} items.",
                safe_alternative="Trim the source list to the most important clips.",
                severity="low",
            )
        for markers, category, reason, alternative, severity in self._blocked_markers:
            if any(marker in normalized for marker in markers):
                return VideoEditingSafetyDecision(
                    allowed=False,
                    category=category,
                    reason=reason,
                    safe_alternative=alternative,
                    severity=severity,
                )
        return VideoEditingSafetyDecision(
            allowed=True,
            category="allowed",
            reason="The request fits the current local-first video editing policy.",
            safe_alternative=None,
            severity="low",
        )
