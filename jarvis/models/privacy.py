"""Explicit privacy modes for provider eligibility.

This module is policy metadata only.  It never uploads data, changes provider
configuration, or grants execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .types import ModelProvider, ModelProviderStatus


class PrivacyMode(StrEnum):
    LOCAL_ONLY = "local_only"
    PRIVATE_HYBRID = "private_hybrid"
    NORMAL_HYBRID = "normal_hybrid"
    CLOUD_MAX = "cloud_max"


@dataclass(frozen=True, slots=True)
class PrivacyDecision:
    provider_id: str
    mode: PrivacyMode
    allowed: bool
    reason: str


@dataclass(frozen=True, slots=True)
class PrivacyPolicy:
    """A visible, explicit routing policy with no silent downgrade."""

    mode: PrivacyMode = PrivacyMode.LOCAL_ONLY
    allow_cloud_providers: bool = False

    @classmethod
    def from_value(cls, value: PrivacyMode | str | None, *, allow_cloud_providers: bool = False) -> "PrivacyPolicy":
        try:
            mode = value if isinstance(value, PrivacyMode) else PrivacyMode(str(value or PrivacyMode.LOCAL_ONLY))
        except ValueError as exc:
            raise ValueError("invalid_privacy_mode") from exc
        return cls(mode, bool(allow_cloud_providers))

    def evaluate(self, provider: ModelProvider) -> PrivacyDecision:
        if provider.status is not ModelProviderStatus.READY:
            return PrivacyDecision(provider.provider_id, self.mode, False, "provider_not_ready")
        if not provider.enabled:
            return PrivacyDecision(provider.provider_id, self.mode, False, "provider_disabled")
        if provider.privacy_mode.value == "cloud_only_blocked":
            return PrivacyDecision(provider.provider_id, self.mode, False, "provider_cloud_policy_blocked")
        if self.mode is PrivacyMode.LOCAL_ONLY and not provider.local:
            return PrivacyDecision(provider.provider_id, self.mode, False, "local_only_rejects_remote_provider")
        if not provider.local and not self.allow_cloud_providers:
            return PrivacyDecision(provider.provider_id, self.mode, False, "cloud_providers_disabled")
        if self.mode is PrivacyMode.PRIVATE_HYBRID and not provider.local and provider.privacy_mode.value != "optional_cloud":
            return PrivacyDecision(provider.provider_id, self.mode, False, "private_hybrid_requires_optional_cloud_provider")
        return PrivacyDecision(provider.provider_id, self.mode, True, "provider_matches_explicit_privacy_policy")
