from __future__ import annotations

import unittest

from commands import CommandManager
from conversation import ConversationContext, ConversationSession
from jarvis.models import (
    ModelCapability,
    ModelPrivacyMode,
    ModelProvider,
    ModelProviderRegistry,
    ModelProviderRegistryError,
    ModelProviderStatus,
    ModelProviderType,
    ModelRequest,
    ModelRiskLevel,
    ModelRoute,
    ModelRouter,
    build_default_model_registry,
    safe_hardware_summary,
)


class Phase3ModelRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = build_default_model_registry(ollama_ready=True, ollama_models=("llama3.2:1b", "llava:latest"), vision_ready=True)
        self.router = ModelRouter(self.registry)

    def test_models_are_typed(self) -> None:
        provider = ModelProvider("p", ModelProviderType.STUB, "P", ModelProviderStatus.READY, (ModelCapability.CHAT,), configured=True, enabled=True)
        route = ModelRoute("conversation", "p", "m", ModelCapability.CHAT, ModelProviderStatus.READY, confidence=1)
        request = ModelRequest("conversation", "hello", risk_level=ModelRiskLevel.LOW)
        self.assertEqual(provider.privacy_mode, ModelPrivacyMode.LOCAL_ONLY)
        self.assertEqual(route.selected_provider, "p")
        self.assertTrue(request.local_only)

    def test_duplicate_provider_rejected(self) -> None:
        provider = ModelProvider("p", ModelProviderType.STUB, "P", ModelProviderStatus.DISABLED, (ModelCapability.CHAT,))
        registry = ModelProviderRegistry((provider,))
        with self.assertRaises(ModelProviderRegistryError):
            registry.register_provider(provider)

    def test_local_only_routes_to_ready_ollama(self) -> None:
        route = self.router.route_for_task("conversation")
        self.assertEqual(route.selected_provider, "ollama_text")
        self.assertEqual(route.status, ModelProviderStatus.READY)
        self.assertTrue(route.local_only)

    def test_vision_route_uses_local_vision(self) -> None:
        self.assertEqual(self.router.route_for_task("vision").selected_provider, "ollama_vision")

    def test_cloud_providers_are_disabled(self) -> None:
        litellm = self.registry.get_provider("litellm")
        self.assertFalse(litellm.enabled)
        self.assertNotEqual(litellm.status, ModelProviderStatus.READY)

    def test_unavailable_and_fallback_route(self) -> None:
        registry = build_default_model_registry()
        route = ModelRouter(registry).route_for_task("coding")
        self.assertEqual(route.status, ModelProviderStatus.UNAVAILABLE)
        self.assertIn("llama_cpp", route.fallback_routes)

    def test_preferred_unavailable_provider_does_not_override_ready(self) -> None:
        route = self.router.route_for_task("coding", preferred_provider="vllm")
        self.assertEqual(route.selected_provider, "ollama_text")

    def test_hardware_discovery_is_safe(self) -> None:
        data = safe_hardware_summary()
        self.assertTrue(data["local_only"])
        self.assertNotIn("hostname", data)

    def test_model_cli_commands(self) -> None:
        commands = CommandManager(); commands.initialize()
        context = ConversationContext(session=ConversationSession(), metadata={"model_registry": self.registry, "model_router": self.router})
        for command in (
            "model status", "model providers", "model capabilities", "model route conversation",
            "model route coding", "model route vision", "model explain nemotron reasoning", "model hardware", "model policy",
        ):
            response = commands.execute(command, context).response
            self.assertTrue(response)
            self.assertLess(len(response), 5000)
            self.assertNotIn("C:\\Users", response)

    def test_config_defaults_block_cloud(self) -> None:
        from config import load_settings

        config = load_settings().models
        self.assertTrue(config.local_only_default)
        self.assertFalse(config.allow_cloud_providers)


if __name__ == "__main__":
    unittest.main()
