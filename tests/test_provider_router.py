"""Tests for the JARVIS OS Provider Router."""

from __future__ import annotations

import unittest
from types import MappingProxyType

from config.schema import ProvidersConfig
from providers import (
    BaseProvider,
    ProviderCapability,
    ProviderConfig,
    ProviderKind,
    ProviderManager,
    ProviderRequest,
    ProviderRouter,
    ProviderSelectionContext,
    ProviderTaskType,
)


class ProviderRouterTests(unittest.TestCase):
    """Provider manager, registry, health, and routing tests."""

    def test_discovery_registration_and_health_from_default_config(self) -> None:
        manager = ProviderManager(
            ProvidersConfig(
                default_provider="",
                enabled_providers=("ollama",),
                timeout_seconds=30,
                max_retries=2,
                track_costs=True,
                definitions=MappingProxyType({}),
            )
        )

        stats = manager.initialize()

        self.assertGreaterEqual(stats.registered_providers, 10)
        self.assertEqual(stats.enabled_providers, 1)
        self.assertEqual(stats.healthy_providers, 1)
        self.assertIn("ollama", manager.registry.provider_ids())

    def test_routing_selects_provider_by_capability(self) -> None:
        manager = ProviderManager(
            ProvidersConfig(
                default_provider="",
                enabled_providers=(),
                timeout_seconds=30,
                max_retries=2,
                track_costs=True,
                definitions=MappingProxyType(
                    {
                        "coder": {
                            "kind": "deepseek",
                            "enabled": True,
                        },
                        "visioner": {
                            "kind": "google_gemini",
                            "enabled": True,
                        },
                    }
                ),
            )
        )
        manager.initialize()

        selected = manager.router.select_provider(
            ProviderSelectionContext(task_type=ProviderTaskType.VISION)
        )

        self.assertEqual(selected.provider_id, "visioner")

    def test_preferred_provider_wins_when_capable(self) -> None:
        manager = ProviderManager(
            ProvidersConfig(
                default_provider="",
                enabled_providers=("openai", "anthropic"),
                timeout_seconds=30,
                max_retries=2,
                track_costs=True,
                definitions=MappingProxyType({}),
            )
        )
        manager.initialize()

        selected = manager.router.select_provider(
            ProviderSelectionContext(
                task_type=ProviderTaskType.REASONING,
                preferred_provider="anthropic",
            )
        )

        self.assertEqual(selected.provider_id, "anthropic")

    def test_fallback_selection_skips_disabled_provider(self) -> None:
        manager = ProviderManager(
            ProvidersConfig(
                default_provider="",
                enabled_providers=(),
                timeout_seconds=30,
                max_retries=2,
                track_costs=True,
                definitions=MappingProxyType(
                    {
                        "disabled": {"kind": "openai", "enabled": False},
                        "fallback": {"kind": "openrouter", "enabled": True},
                    }
                ),
            )
        )
        manager.initialize()

        selected = manager.router.select_provider(
            ProviderSelectionContext(
                task_type=ProviderTaskType.CHAT,
                preferred_provider="disabled",
            )
        )

        self.assertEqual(selected.provider_id, "fallback")

    def test_local_only_routing_uses_local_provider(self) -> None:
        manager = ProviderManager(
            ProvidersConfig(
                default_provider="",
                enabled_providers=("openai", "ollama"),
                timeout_seconds=30,
                max_retries=2,
                track_costs=True,
                definitions=MappingProxyType({}),
            )
        )
        manager.initialize()

        selected = manager.router.select_provider(
            ProviderSelectionContext(
                task_type=ProviderTaskType.CODING,
                local_only=True,
            )
        )

        self.assertEqual(selected.provider_id, "ollama")

    def test_capability_detection_and_token_estimation(self) -> None:
        manager = ProviderManager(
            ProvidersConfig(
                default_provider="",
                enabled_providers=("openai",),
                timeout_seconds=30,
                max_retries=2,
                track_costs=True,
                definitions=MappingProxyType({}),
            )
        )
        manager.initialize()
        provider = manager.registry.require("openai").provider
        self.assertIsNotNone(provider)

        self.assertTrue(provider.capabilities().supports(ProviderCapability.CHAT))
        self.assertGreater(provider.estimate_tokens("hello world").total_tokens, 0)

    def test_router_raises_when_no_provider_matches(self) -> None:
        router = ProviderRouter(())

        with self.assertRaises(LookupError):
            router.select_provider(
                ProviderSelectionContext(task_type=ProviderTaskType.CHAT)
            )

    def test_provider_base_methods_are_interfaces_only(self) -> None:
        manager = ProviderManager(
            ProvidersConfig(
                default_provider="",
                enabled_providers=("future",),
                timeout_seconds=30,
                max_retries=2,
                track_costs=True,
                definitions=MappingProxyType(
                    {"future": {"kind": "future", "enabled": True}}
                ),
            )
        )
        manager.initialize()
        provider = manager.registry.require("future").provider
        self.assertIsInstance(provider, BaseProvider)

        with self.assertRaises(NotImplementedError):
            provider.chat(ProviderRequest(prompt="Hello"))

    def test_provider_config_aliases_google(self) -> None:
        manager = ProviderManager(
            ProvidersConfig(
                default_provider="",
                enabled_providers=(),
                timeout_seconds=30,
                max_retries=2,
                track_costs=True,
                definitions=MappingProxyType(
                    {"gemini": {"kind": "google", "enabled": True}}
                ),
            )
        )
        manager.initialize()
        record = manager.registry.require("gemini")

        self.assertEqual(record.config.kind, ProviderKind.GOOGLE_GEMINI)


if __name__ == "__main__":
    unittest.main()
