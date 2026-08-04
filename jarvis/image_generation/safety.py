"""Safety policy for governed image generation requests."""

from __future__ import annotations

from .models import ImageGenerationSafetyDecision


class ImageGenerationSafetyPolicy:
    """Bounded safety checks for local-first generation requests."""

    _blocked_markers = (
        (("sexual content involving minors", "child sexual", "minor sexual"), "sexual_minors", "This request involves exploitative sexual content and cannot be processed.", "Create a non-explicit educational safety poster instead.", "high"),
        (("explicit unsafe content", "explicit sexual", "porn", "nude", "nsfw"), "explicit_sexual_content", "This request asks for explicit sexual content and cannot be processed.", "Revise it toward a non-explicit character or fashion concept.", "high"),
        (("self-harm", "suicide", "kill myself"), "self_harm_imagery", "This request asks for self-harm imagery and cannot be processed.", "Request a supportive wellness illustration or a neutral safety infographic instead.", "high"),
        (("graphic violence", "gore", "dismember", "bloody corpse"), "graphic_violence", "This request asks for graphic violence or gore and cannot be processed.", "Request a non-graphic action scene or safety diagram instead.", "high"),
        (("deepfake", "exact face of", "make this real person", "celebrity face"), "deepfake_impersonation", "This request asks to imitate or fabricate a real person's identity and cannot be processed.", "Use a fictional character or a generic human silhouette instead.", "high"),
        (("face recognition", "identify this real person", "who is this person"), "identity_matching", "This request asks for identity recognition and cannot be processed.", "Request a neutral description of visible clothing or scene details instead.", "high"),
        (("non-consensual intimate", "revenge porn"), "non_consensual_intimate_imagery", "This request asks for abusive intimate imagery and cannot be processed.", "Request a privacy-respecting educational poster instead.", "high"),
        (("private personal data", "passport number", "credit card number"), "private_data_visualization", "This request asks to visualize private personal data and cannot be processed.", "Use fictional placeholders or a redacted UI mockup instead.", "high"),
        (("copyrighted character replication", "exact disney", "exact marvel", "exact pokemon"), "copyrighted_character_replication", "This request asks for exact copyrighted-character copying and cannot be processed.", "Create an original character inspired by broad genre traits instead.", "medium"),
        (("political persuasion", "campaign poster to convince voters", "propaganda"), "political_persuasion", "This request asks for political persuasion imagery and cannot be processed.", "Create a neutral civic-information poster instead.", "high"),
        (("illegal weapon construction", "how to build a bomb", "weapon blueprint"), "illegal_weapon_construction", "This request asks for dangerous weapon-construction imagery and cannot be processed.", "Create a generic industrial safety diagram instead.", "high"),
        (("bypass safety", "ignore your safety rules"), "safety_bypass", "This request tries to bypass generation safety controls and cannot be processed.", "Use a normal prompt that stays within the allowed policy.", "high"),
    )

    def __init__(self, max_prompt_chars: int = 600, max_negative_prompt_chars: int = 300) -> None:
        self.max_prompt_chars = max_prompt_chars
        self.max_negative_prompt_chars = max_negative_prompt_chars

    def assess(self, prompt: str, negative_prompt: str = "") -> ImageGenerationSafetyDecision:
        normalized = " ".join(prompt.lower().split())
        if not normalized:
            return ImageGenerationSafetyDecision(
                allowed=False,
                category="invalid_prompt",
                reason="A prompt is required before image generation can be planned.",
                safe_alternative="Describe the image you want in one clear sentence.",
                severity="low",
            )
        if len(prompt) > self.max_prompt_chars:
            return ImageGenerationSafetyDecision(
                allowed=False,
                category="prompt_too_long",
                reason=f"Prompts must stay within {self.max_prompt_chars} characters.",
                safe_alternative="Shorten the request to the most important visual details.",
                severity="low",
            )
        if len(negative_prompt) > self.max_negative_prompt_chars:
            return ImageGenerationSafetyDecision(
                allowed=False,
                category="negative_prompt_too_long",
                reason=f"Negative prompts must stay within {self.max_negative_prompt_chars} characters.",
                safe_alternative="Trim the negative prompt to the key exclusions only.",
                severity="low",
            )
        for markers, category, reason, alternative, severity in self._blocked_markers:
            if any(marker in normalized for marker in markers):
                return ImageGenerationSafetyDecision(
                    allowed=False,
                    category=category,
                    reason=reason,
                    safe_alternative=alternative,
                    severity=severity,
                )
        return ImageGenerationSafetyDecision(
            allowed=True,
            category="allowed",
            reason="The request fits the current local-first image generation policy.",
            safe_alternative=None,
            severity="low",
        )
