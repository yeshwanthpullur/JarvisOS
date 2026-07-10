"""Tests for the Provider Execution Framework."""

from __future__ import annotations

import logging
import unittest

from provider_execution import (
    ExecutionManager,
    ExecutionStrategy,
    ModelMetadata,
    ModelSelector,
    ProviderBenchmark,
    ProviderCache,
    ProviderCapabilities,
    ProviderDiagnostics,
    ProviderExecutionContext,
    ProviderExecutionHealth,
    ProviderExecutionHistory,
    ProviderExecutionHistoryRecord,
    ProviderExecutionMetrics,
    ProviderExecutionRecord,
    ProviderExecutionRegistry,
    ProviderExecutionRequest,
    ProviderExecutionResponse,
    ProviderExecutionValidator,
    ProviderHealthState,
    ProviderRecovery,
    ProviderExecutionLogger,
    ProviderSelector,
)
from providers.provider_types import ModelInfo, ProviderCapability


def build_record(
    provider_id: str = "test-provider",
    *,
    reasoning: bool = True,
    healthy: bool = True,
    enabled: bool = True,
) -> ProviderExecutionRecord:
    """Build a provider execution record for tests."""
    health = ProviderExecutionHealth()
    if healthy:
        health.mark_healthy()
    return ProviderExecutionRecord(
        provider_id=provider_id,
        enabled=enabled,
        capabilities=ProviderCapabilities(
            models=(
                ModelInfo(
                    model_id="model-a",
                    display_name="Model A",
                    capabilities=(ProviderCapability.CHAT, ProviderCapability.REASONING),
                    context_window=4096,
                ),
            ),
            reasoning=reasoning,
            streaming=True,
            structured_output=True,
        ),
        health=health,
    )


class ProviderExecutionTests(unittest.TestCase):
    """Provider execution unit tests."""

    def test_request_defaults_include_ids(self) -> None:
        request = ProviderExecutionRequest(intent="chat", goal="Say hello")
        self.assertTrue(request.request_id)
        self.assertTrue(request.execution_id)

    def test_response_defaults_success(self) -> None:
        response = ProviderExecutionResponse(response="ok")
        self.assertTrue(response.success)

    def test_health_mark_healthy(self) -> None:
        health = ProviderExecutionHealth()
        health.mark_healthy(12)
        self.assertEqual(health.state, ProviderHealthState.HEALTHY)
        self.assertEqual(health.latency_ms, 12)

    def test_health_mark_failure(self) -> None:
        health = ProviderExecutionHealth()
        health.mark_failure("timeout")
        self.assertEqual(health.state, ProviderHealthState.DEGRADED)
        self.assertGreater(health.failure_rate, 0)

    def test_metrics_record_request(self) -> None:
        metrics = ProviderExecutionMetrics()
        metrics.record_request(estimated_tokens=10, estimated_cost=0.2)
        self.assertEqual(metrics.requests, 1)
        self.assertEqual(metrics.estimated_tokens, 10)

    def test_metrics_record_response(self) -> None:
        metrics = ProviderExecutionMetrics()
        metrics.record_response(20)
        self.assertEqual(metrics.responses, 1)
        self.assertEqual(metrics.average_response_time_ms, 20)

    def test_metrics_record_failure(self) -> None:
        metrics = ProviderExecutionMetrics(requests=2)
        metrics.record_failure()
        self.assertEqual(metrics.failures, 1)

    def test_capabilities_support_reasoning(self) -> None:
        capabilities = ProviderCapabilities(reasoning=True)
        self.assertTrue(capabilities.supports(ProviderCapability.REASONING))

    def test_capabilities_reject_unsupported(self) -> None:
        capabilities = ProviderCapabilities()
        self.assertFalse(capabilities.supports(ProviderCapability.VISION))

    def test_registry_register_lookup(self) -> None:
        registry = ProviderExecutionRegistry()
        record = build_record()
        registry.register(record)
        self.assertIs(registry.lookup("test-provider"), record)

    def test_registry_enable_disable(self) -> None:
        registry = ProviderExecutionRegistry()
        registry.register(build_record())
        registry.disable("test-provider")
        self.assertFalse(registry.require("test-provider").enabled)
        registry.enable("test-provider")
        self.assertTrue(registry.require("test-provider").enabled)

    def test_registry_capability_lookup(self) -> None:
        registry = ProviderExecutionRegistry()
        registry.register(build_record())
        self.assertEqual(len(registry.capability_lookup(ProviderCapability.REASONING)), 1)

    def test_registry_statistics(self) -> None:
        registry = ProviderExecutionRegistry()
        registry.register(build_record())
        stats = registry.statistics()
        self.assertEqual(stats["registered_providers"], 1)

    def test_registry_health_lookup(self) -> None:
        registry = ProviderExecutionRegistry()
        record = build_record()
        registry.register(record)
        self.assertEqual(len(registry.health_lookup(ProviderHealthState.HEALTHY)), 1)

    def test_registry_unregistered_lookup_returns_none(self) -> None:
        registry = ProviderExecutionRegistry()
        self.assertIsNone(registry.lookup("missing"))

    def test_registry_validate_record(self) -> None:
        registry = ProviderExecutionRegistry()
        self.assertTrue(registry.validate("missing") is False)

    def test_selector_selects_matching_provider(self) -> None:
        registry = ProviderExecutionRegistry()
        registry.register(build_record())
        request = ProviderExecutionRequest(
            intent="reasoning",
            goal="Think",
            capabilities=(ProviderCapability.REASONING,),
        )
        selected = ProviderSelector().select(request, registry)
        self.assertEqual(selected.provider_id if selected else None, "test-provider")

    def test_selector_ignores_disabled_provider(self) -> None:
        registry = ProviderExecutionRegistry()
        registry.register(build_record(enabled=False))
        request = ProviderExecutionRequest(intent="chat", goal="Talk")
        self.assertIsNone(ProviderSelector().select(request, registry))

    def test_selector_prefers_requested_provider(self) -> None:
        registry = ProviderExecutionRegistry()
        registry.register(build_record("a"))
        registry.register(build_record("b"))
        request = ProviderExecutionRequest(intent="chat", goal="Talk", provider="b")
        selected = ProviderSelector().select(request, registry)
        self.assertEqual(selected.provider_id if selected else None, "b")

    def test_selector_local_first_prefers_local_provider(self) -> None:
        registry = ProviderExecutionRegistry()
        local = build_record("local")
        local.metadata["local"] = True
        remote = build_record("remote")
        registry.register(remote)
        registry.register(local)
        request = ProviderExecutionRequest(
            intent="chat",
            goal="Talk",
            strategy=ExecutionStrategy.LOCAL_FIRST,
        )
        selected = ProviderSelector().select(request, registry)
        self.assertEqual(selected.provider_id if selected else None, "local")

    def test_selector_cloud_first_prefers_non_local_provider(self) -> None:
        registry = ProviderExecutionRegistry()
        local = build_record("local")
        local.metadata["local"] = True
        remote = build_record("remote")
        registry.register(local)
        registry.register(remote)
        request = ProviderExecutionRequest(
            intent="chat",
            goal="Talk",
            strategy=ExecutionStrategy.CLOUD_FIRST,
        )
        selected = ProviderSelector().select(request, registry)
        self.assertEqual(selected.provider_id if selected else None, "remote")

    def test_model_selector_discovers_models(self) -> None:
        selector = ModelSelector()
        models = selector.discover_models(build_record())
        self.assertEqual(models[0].model_id, "model-a")

    def test_model_selector_registers_model(self) -> None:
        selector = ModelSelector()
        selector.register_model(ModelMetadata(model_id="x", provider_id="p"))
        self.assertEqual(selector.statistics()["registered_models"], 1)

    def test_model_selector_selects_preferred_model(self) -> None:
        selector = ModelSelector()
        request = ProviderExecutionRequest(intent="chat", goal="Talk", model="model-a")
        model = selector.select_model(build_record(), request)
        self.assertEqual(model.model_id if model else None, "model-a")

    def test_model_selector_fallback_model(self) -> None:
        model = ModelSelector().fallback_model(build_record(), failed_model="other")
        self.assertEqual(model.model_id if model else None, "model-a")

    def test_model_selector_validate_model(self) -> None:
        selector = ModelSelector()
        self.assertTrue(selector.validate_model(ModelMetadata(model_id="x", provider_id="p")))

    def test_model_selector_benchmark_models(self) -> None:
        selector = ModelSelector()
        ranked = selector.benchmark_models(build_record())
        self.assertGreaterEqual(len(ranked), 1)

    def test_model_selector_collect_metrics(self) -> None:
        selector = ModelSelector()
        model = ModelMetadata(model_id="x", provider_id="p", latency_ms=10.0)
        metrics = selector.collect_metrics(model)
        self.assertEqual(metrics["model_id"], "x")

    def test_validator_accepts_valid_request(self) -> None:
        valid, issues = ProviderExecutionValidator().validate_request(
            ProviderExecutionRequest(intent="chat", goal="Talk")
        )
        self.assertTrue(valid)
        self.assertEqual(issues, ())

    def test_validator_rejects_empty_request(self) -> None:
        valid, issues = ProviderExecutionValidator().validate_request(
            ProviderExecutionRequest(intent="", goal="")
        )
        self.assertFalse(valid)
        self.assertGreaterEqual(len(issues), 2)

    def test_validator_response_requires_content_on_success(self) -> None:
        valid, issues = ProviderExecutionValidator().validate_response(
            ProviderExecutionResponse(response="", success=True)
        )
        self.assertFalse(valid)
        self.assertTrue(issues)

    def test_validator_accepts_failed_response_without_content(self) -> None:
        valid, issues = ProviderExecutionValidator().validate_response(
            ProviderExecutionResponse(response="", success=False)
        )
        self.assertTrue(valid)
        self.assertEqual(issues, ())

    def test_validator_validates_record(self) -> None:
        valid, issues = ProviderExecutionValidator().validate_record(build_record())
        self.assertTrue(valid)
        self.assertEqual(issues, ())

    def test_history_append_and_search(self) -> None:
        history = ProviderExecutionHistory()
        history.append(
            ProviderExecutionHistoryRecord(
                execution_id="1",
                provider="p",
                model="m",
                department=None,
                agent=None,
                execution_strategy=ExecutionStrategy.SINGLE_PROVIDER,
            )
        )
        self.assertEqual(len(history.search(provider="p")), 1)

    def test_history_statistics(self) -> None:
        history = ProviderExecutionHistory()
        self.assertEqual(history.statistics()["executions"], 0)

    def test_history_search_success_filter(self) -> None:
        history = ProviderExecutionHistory()
        history.append(
            ProviderExecutionHistoryRecord(
                execution_id="1",
                provider="p",
                model="m",
                department=None,
                agent=None,
                execution_strategy=ExecutionStrategy.SINGLE_PROVIDER,
                success=False,
            )
        )
        self.assertEqual(len(history.search(success=False)), 1)

    def test_cache_set_get(self) -> None:
        cache = ProviderCache()
        cache.set("metadata", "p", {"ready": True})
        self.assertEqual(cache.get("metadata", "p"), {"ready": True})

    def test_cache_clear_namespace(self) -> None:
        cache = ProviderCache()
        cache.set("metadata", "p", 1)
        cache.clear("metadata")
        self.assertIsNone(cache.get("metadata", "p"))

    def test_cache_statistics(self) -> None:
        cache = ProviderCache()
        cache.set("metadata", "p", 1)
        self.assertEqual(cache.statistics()["metadata"], 1)

    def test_recovery_classifies_timeout(self) -> None:
        recovery = ProviderRecovery()
        self.assertEqual(recovery.classify_failure("timeout waiting").value, "timeout")

    def test_recovery_plan_records_history(self) -> None:
        recovery = ProviderRecovery()
        plan = recovery.plan("provider unavailable")
        self.assertTrue(plan.actions)
        self.assertEqual(recovery.statistics()["recovery_plans"], 1)

    def test_recovery_classifies_provider_failure(self) -> None:
        recovery = ProviderRecovery()
        self.assertEqual(recovery.classify_failure("provider unavailable").value, "provider_unavailable")

    def test_recovery_plan_backoff_grows(self) -> None:
        recovery = ProviderRecovery()
        first = recovery.plan("provider unavailable", retry_count=0)
        second = recovery.plan("provider unavailable", retry_count=2)
        self.assertLess(first.backoff_seconds, second.backoff_seconds)

    def test_benchmark_latency_ranking(self) -> None:
        fast = build_record("fast")
        slow = build_record("slow")
        slow.health.latency_ms = 100
        ranked = ProviderBenchmark().latency_ranking((slow, fast))
        self.assertEqual(ranked[0].provider_id, "fast")

    def test_benchmark_reliability_ranking(self) -> None:
        reliable = build_record("reliable")
        weak = build_record("weak")
        weak.metrics.reliability_score = 0.1
        ranked = ProviderBenchmark().reliability_ranking((weak, reliable))
        self.assertEqual(ranked[0].provider_id, "reliable")

    def test_benchmark_cost_ranking(self) -> None:
        a = build_record("a")
        b = build_record("b")
        a.metrics.estimated_cost = 10
        b.metrics.estimated_cost = 1
        ranked = ProviderBenchmark().cost_ranking((a, b))
        self.assertEqual(ranked[0].provider_id, "b")

    def test_benchmark_historical_ranking(self) -> None:
        a = build_record("a")
        b = build_record("b")
        a.metrics.responses = 1
        b.metrics.responses = 5
        ranked = ProviderBenchmark().historical_ranking((a, b))
        self.assertEqual(ranked[0].provider_id, "b")

    def test_diagnostics_health_report(self) -> None:
        registry = ProviderExecutionRegistry()
        registry.register(build_record())
        report = ProviderDiagnostics().health_report(registry)
        self.assertIn("test-provider", report["providers"])

    def test_diagnostics_capability_report(self) -> None:
        registry = ProviderExecutionRegistry()
        registry.register(build_record())
        report = ProviderDiagnostics().capability_report(registry)
        self.assertIn("test-provider", report["providers"])

    def test_diagnostics_performance_report(self) -> None:
        registry = ProviderExecutionRegistry()
        registry.register(build_record())
        report = ProviderDiagnostics().performance_report(registry)
        self.assertIn("test-provider", report["providers"])

    def test_diagnostics_failure_report(self) -> None:
        registry = ProviderExecutionRegistry()
        registry.register(build_record())
        report = ProviderDiagnostics().failure_report(registry)
        self.assertIn("test-provider", report["providers"])

    def test_diagnostics_statistics_report(self) -> None:
        registry = ProviderExecutionRegistry()
        registry.register(build_record())
        report = ProviderDiagnostics().statistics_report(registry)
        self.assertEqual(report["registered_providers"], 1)

    def test_logger_child(self) -> None:
        child = ProviderExecutionLogger(logging.getLogger("root")).child("nested")
        self.assertEqual(child.name, "nested")

    def test_manager_initializes(self) -> None:
        manager = ExecutionManager(context=ProviderExecutionContext(logger=logging.getLogger("test")))
        stats = manager.initialize()
        self.assertEqual(stats.status, "ready")

    def test_manager_builds_request_with_capability(self) -> None:
        manager = ExecutionManager()
        request = manager.build_execution_request("coding", "Write a function")
        self.assertIn(ProviderCapability.CODING, request.capabilities)

    def test_manager_estimates_complexity(self) -> None:
        self.assertGreater(ExecutionManager().estimate_complexity("one two three"), 0)

    def test_manager_selects_provider(self) -> None:
        manager = ExecutionManager()
        manager.registry.register(build_record())
        request = ProviderExecutionRequest(intent="chat", goal="Talk")
        self.assertIsNotNone(manager.select_provider(request))

    def test_manager_selects_model(self) -> None:
        manager = ExecutionManager()
        record = build_record()
        request = ProviderExecutionRequest(intent="chat", goal="Talk")
        model = manager.select_model(record, request)
        self.assertEqual(model.model_id if model else None, "model-a")

    def test_manager_execute_success_is_architectural(self) -> None:
        manager = ExecutionManager()
        manager.initialize()
        manager.registry.register(build_record())
        request = manager.build_execution_request("chat", "Talk")
        response = manager.execute(request)
        self.assertTrue(response.success)
        self.assertEqual(response.warnings[0], "provider_api_execution_not_implemented")

    def test_manager_execute_no_provider_fails_gracefully(self) -> None:
        manager = ExecutionManager()
        manager.initialize()
        request = manager.build_execution_request("chat", "Talk")
        response = manager.execute(request)
        self.assertFalse(response.success)

    def test_manager_records_execution_history(self) -> None:
        manager = ExecutionManager()
        manager.initialize()
        manager.registry.register(build_record())
        response = manager.execute(manager.build_execution_request("chat", "Talk"))
        self.assertTrue(response.success)
        self.assertEqual(manager.history.statistics()["executions"], 1)

    def test_manager_handle_recovery(self) -> None:
        recovery = ExecutionManager().handle_recovery("model unavailable")
        self.assertEqual(recovery["classification"], "model_unavailable")

    def test_manager_statistics_include_models(self) -> None:
        manager = ExecutionManager()
        manager.initialize()
        manager.registry.register(build_record())
        manager.model_selector.discover_models(manager.registry.require("test-provider"))
        self.assertEqual(manager.statistics().registered_models, 1)

    def test_manager_determines_local_first_strategy(self) -> None:
        manager = ExecutionManager()
        request = ProviderExecutionRequest(intent="chat", goal="Talk", metadata={"local_only": True})
        self.assertEqual(manager.determine_strategy(request), ExecutionStrategy.LOCAL_FIRST)

    def test_manager_determines_multi_provider_strategy(self) -> None:
        manager = ExecutionManager()
        request = ProviderExecutionRequest(intent="chat", goal="Talk", metadata={"multi_provider": True})
        self.assertEqual(manager.determine_strategy(request), ExecutionStrategy.MULTI_PROVIDER)

    def test_manager_determines_fallback_strategy(self) -> None:
        manager = ExecutionManager()
        request = ProviderExecutionRequest(intent="chat", goal="Talk", metadata={"fallback": True})
        self.assertEqual(manager.determine_strategy(request), ExecutionStrategy.FALLBACK)

    def test_manager_capabilities_for_coding_intent(self) -> None:
        manager = ExecutionManager()
        caps = manager._capabilities_for_intent("coding")
        self.assertIn(ProviderCapability.CODING, caps)

    def test_manager_capabilities_for_default_intent(self) -> None:
        manager = ExecutionManager()
        caps = manager._capabilities_for_intent("chat")
        self.assertIn(ProviderCapability.CHAT, caps)

    def test_manager_estimate_tokens(self) -> None:
        self.assertGreater(ExecutionManager().estimate_tokens("hello world"), 0)

    def test_manager_estimate_latency_from_provider(self) -> None:
        record = build_record()
        record.health.latency_ms = 42
        self.assertEqual(ExecutionManager().estimate_latency(record), 42)

    def test_manager_validate_response(self) -> None:
        valid, issues = ExecutionManager().validate_response(ProviderExecutionResponse(response="ok"))
        self.assertTrue(valid)
        self.assertEqual(issues, ())

    def test_manager_failure_response(self) -> None:
        manager = ExecutionManager()
        request = ProviderExecutionRequest(intent="chat", goal="Talk")
        response = manager.handle_failures(request, "provider unavailable")
        self.assertFalse(response.success)

    def test_manager_execution_statistics_created_state(self) -> None:
        manager = ExecutionManager()
        self.assertEqual(manager.statistics().status, "created")

    def test_manager_execution_statistics_ready_state(self) -> None:
        manager = ExecutionManager()
        manager.initialize()
        self.assertEqual(manager.statistics().status, "ready")

    def test_provider_capabilities_from_router_capabilities(self) -> None:
        router_caps = build_record().capabilities
        execution_caps = ProviderCapabilities.from_router_capabilities(router_caps)
        self.assertTrue(execution_caps.reasoning)

    def test_execution_context_defaults_logger(self) -> None:
        context = ProviderExecutionContext()
        self.assertIsNotNone(context.logger)

    def test_execution_strategy_enum_contains_hybrid(self) -> None:
        self.assertEqual(ExecutionStrategy.HYBRID.value, "hybrid")

    def test_fallback_action_enum_contains_retry(self) -> None:
        from provider_execution import FallbackAction

        self.assertEqual(FallbackAction.RETRY_DIFFERENT_PROVIDER.value, "retry_different_provider")

    def test_execution_request_infers_strategy_field(self) -> None:
        request = ProviderExecutionRequest(intent="chat", goal="Talk", strategy=ExecutionStrategy.HYBRID)
        self.assertEqual(request.strategy, ExecutionStrategy.HYBRID)

    def test_execution_response_statistics_default(self) -> None:
        response = ProviderExecutionResponse(response="ok")
        self.assertEqual(response.statistics, {})

    def test_execution_manager_cache_statistics(self) -> None:
        manager = ExecutionManager()
        manager.cache.set("health", "p", True)
        self.assertEqual(manager.cache.statistics()["health"], 1)


if __name__ == "__main__":
    unittest.main()
