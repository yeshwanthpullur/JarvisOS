"""Tests for the Retrieval and Precision Lookup Layer."""

from __future__ import annotations

import unittest

from jarvis import JarvisContext, JarvisCore, JarvisRequest
from jarvis.jarvis_manager import JarvisManager
from retrieval import (
    RetrievalCache,
    RetrievalContext,
    RetrievalDiagnostics,
    RetrievalEngine,
    RetrievalHistory,
    RetrievalHistoryRecord,
    RetrievalLogger,
    RetrievalManager,
    RetrievalMetrics,
    RetrievalRanker,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalSelector,
    RetrievalStatistics,
    RetrievalStrategy,
    RetrievalValidator,
)


def build_request(**overrides: object) -> RetrievalRequest:
    payload = {
        "intent": "research",
        "goal": "Find relevant context",
        "query": "relevant context",
        "retrieval_strategy": RetrievalStrategy.HYBRID,
    }
    payload.update(overrides)
    return RetrievalRequest(**payload)


class RetrievalEngineTests(unittest.TestCase):
    """Retrieval layer unit tests."""

    def test_strategy_enum_contains_hybrid(self) -> None:
        self.assertEqual(RetrievalStrategy.HYBRID.value, "hybrid")

    def test_strategy_enum_contains_exact_match(self) -> None:
        self.assertEqual(RetrievalStrategy.EXACT_MATCH.value, "exact_match")

    def test_request_defaults_include_id(self) -> None:
        request = build_request()
        self.assertTrue(request.request_id)

    def test_request_preserves_conversation_id(self) -> None:
        request = build_request(conversation_id="c1")
        self.assertEqual(request.conversation_id, "c1")

    def test_request_preserves_workflow_id(self) -> None:
        request = build_request(workflow_id="w1")
        self.assertEqual(request.workflow_id, "w1")

    def test_request_required_sources(self) -> None:
        request = build_request(required_sources=("memory", "knowledge"))
        self.assertEqual(request.required_sources, ("memory", "knowledge"))

    def test_request_context_metadata(self) -> None:
        request = build_request(context={"project": "x"})
        self.assertEqual(request.context["project"], "x")

    def test_response_defaults(self) -> None:
        response = RetrievalResponse()
        self.assertEqual(response.confidence, 0.0)

    def test_context_defaults_logger(self) -> None:
        self.assertIsNotNone(RetrievalContext().logger)

    def test_context_metadata(self) -> None:
        context = RetrievalContext(metadata={"k": "v"})
        self.assertEqual(context.metadata["k"], "v")

    def test_selector_determines_memory_first(self) -> None:
        selector = RetrievalSelector()
        self.assertEqual(
            selector.determine_retrieval_strategy(build_request(retrieval_strategy=RetrievalStrategy.MEMORY_FIRST)),
            RetrievalStrategy.MEMORY_FIRST,
        )

    def test_selector_chooses_memory_sources(self) -> None:
        selector = RetrievalSelector()
        self.assertEqual(selector.determine_sources(build_request()), ("memory", "knowledge"))

    def test_selector_chooses_required_sources(self) -> None:
        selector = RetrievalSelector()
        self.assertEqual(selector.determine_sources(build_request(required_sources=("task",))), ("task",))

    def test_selector_search_order(self) -> None:
        selector = RetrievalSelector()
        self.assertEqual(selector.determine_search_order(("memory", "knowledge")), ("memory", "knowledge"))

    def test_selector_search_depth_exact_match(self) -> None:
        selector = RetrievalSelector()
        depth = selector.determine_search_depth(build_request(retrieval_strategy=RetrievalStrategy.EXACT_MATCH))
        self.assertEqual(depth, 1)

    def test_selector_ranking_strategy_recent(self) -> None:
        selector = RetrievalSelector()
        self.assertEqual(
            selector.determine_ranking_strategy(build_request(retrieval_strategy=RetrievalStrategy.RECENT_FIRST)),
            "recency",
        )

    def test_selector_confidence(self) -> None:
        selector = RetrievalSelector()
        self.assertGreater(selector.estimate_confidence(build_request()), 0)

    def test_selector_optimize_returns_request(self) -> None:
        selector = RetrievalSelector()
        request = build_request()
        self.assertIs(selector.optimize_retrieval(request), request)

    def test_ranker_orders_by_priority(self) -> None:
        ranker = RetrievalRanker()
        ranked = ranker.rank(({"priority": 1}, {"priority": 2}))
        self.assertEqual(ranked[0]["priority"], 2)

    def test_ranker_handles_empty_items(self) -> None:
        self.assertEqual(RetrievalRanker().rank(()), ())

    def test_cache_create_lookup(self) -> None:
        cache = RetrievalCache()
        cache.create("recent_queries", "q1", {"query": "x"})
        self.assertEqual(cache.lookup("recent_queries", "q1")["query"], "x")

    def test_cache_refresh(self) -> None:
        cache = RetrievalCache()
        cache.create("recent_queries", "q1", 1)
        cache.refresh("recent_queries", "q1", 2)
        self.assertEqual(cache.lookup("recent_queries", "q1"), 2)

    def test_cache_expire(self) -> None:
        cache = RetrievalCache()
        cache.create("recent_queries", "q1", 1)
        cache.expire("recent_queries", "q1")
        self.assertIsNone(cache.lookup("recent_queries", "q1"))

    def test_cache_invalidate_namespace(self) -> None:
        cache = RetrievalCache()
        cache.create("recent_queries", "q1", 1)
        cache.invalidate("recent_queries")
        self.assertEqual(cache.lookup("recent_queries", "q1"), None)

    def test_cache_statistics(self) -> None:
        cache = RetrievalCache()
        cache.create("recent_queries", "q1", 1)
        self.assertEqual(cache.statistics()["recent_queries"], 1)

    def test_history_append_and_list(self) -> None:
        history = RetrievalHistory()
        history.append(
            RetrievalHistoryRecord(
                retrieval_id="r1",
                request_id="q1",
                conversation_id="c1",
                workflow_id="w1",
                strategy=RetrievalStrategy.HYBRID,
                sources_used=("memory", "knowledge"),
                retrieved_items=(),
                execution_time_ms=1.0,
                confidence=0.8,
            )
        )
        self.assertEqual(len(history.list()), 1)

    def test_history_statistics(self) -> None:
        self.assertEqual(RetrievalHistory().statistics()["retrievals"], 0)

    def test_history_record_contains_strategy(self) -> None:
        record = RetrievalHistoryRecord(
            retrieval_id="r1",
            request_id="q1",
            conversation_id=None,
            workflow_id=None,
            strategy=RetrievalStrategy.MEMORY_FIRST,
            sources_used=("memory",),
            retrieved_items=(),
            execution_time_ms=1.0,
            confidence=0.5,
        )
        self.assertEqual(record.strategy, RetrievalStrategy.MEMORY_FIRST)

    def test_metrics_default_statistics(self) -> None:
        self.assertEqual(RetrievalMetrics().statistics()["requests"], 0)

    def test_metrics_custom_counts(self) -> None:
        metrics = RetrievalMetrics(requests=3, successful_retrievals=2)
        self.assertEqual(metrics.requests, 3)
        self.assertEqual(metrics.successful_retrievals, 2)

    def test_validator_accepts_valid_request(self) -> None:
        valid, issues = RetrievalValidator().validate_request(build_request())
        self.assertTrue(valid)
        self.assertEqual(issues, ())

    def test_validator_rejects_blank_request(self) -> None:
        valid, issues = RetrievalValidator().validate_request(RetrievalRequest(intent="", goal="", query=""))
        self.assertFalse(valid)
        self.assertTrue(issues)

    def test_validator_context(self) -> None:
        valid, issues = RetrievalValidator().validate_context(object())
        self.assertTrue(valid)
        self.assertEqual(issues, ())

    def test_validator_sources(self) -> None:
        valid, issues = RetrievalValidator().validate_sources(("memory",))
        self.assertTrue(valid)
        self.assertEqual(issues, ())

    def test_validator_confidence(self) -> None:
        valid, issues = RetrievalValidator().validate_confidence(0.5)
        self.assertTrue(valid)
        self.assertEqual(issues, ())

    def test_validator_metadata(self) -> None:
        valid, issues = RetrievalValidator().validate_metadata({"a": 1})
        self.assertTrue(valid)
        self.assertEqual(issues, ())

    def test_diagnostics_reports_ready(self) -> None:
        self.assertEqual(RetrievalDiagnostics().retrieval_report()["status"], "ready")

    def test_diagnostics_cache_report(self) -> None:
        cache = RetrievalCache()
        self.assertEqual(RetrievalDiagnostics().cache_report(cache)["recent_queries"], 0)

    def test_diagnostics_history_report(self) -> None:
        history = RetrievalHistory()
        self.assertEqual(RetrievalDiagnostics().history_report(history)["retrievals"], 0)

    def test_diagnostics_statistics_report(self) -> None:
        metrics = RetrievalMetrics()
        self.assertEqual(RetrievalDiagnostics().statistics_report(metrics)["requests"], 0)

    def test_logger_exists(self) -> None:
        self.assertIsNotNone(RetrievalLogger().logger)

    def test_engine_initialized(self) -> None:
        self.assertTrue(RetrievalEngine().initialized)

    def test_manager_initialized(self) -> None:
        self.assertTrue(RetrievalManager().initialized)

    def test_manager_initializes(self) -> None:
        stats = RetrievalManager().initialize()
        self.assertEqual(stats.overall_retrieval_health, "healthy")

    def test_manager_statistics(self) -> None:
        stats = RetrievalManager().statistics()
        self.assertEqual(stats.retrieval_engine_status, "ready")

    def test_manager_retrieve(self) -> None:
        manager = RetrievalManager()
        response = manager.retrieve(build_request())
        self.assertTrue(response.retrieved_items)

    def test_engine_retrieve_memory_and_knowledge(self) -> None:
        engine = RetrievalEngine()
        response = engine.retrieve(build_request(), RetrievalContext())
        self.assertIn("memory:1", response.memory_references)
        self.assertIn("knowledge:1", response.knowledge_references)

    def test_engine_retrieve_with_required_sources(self) -> None:
        engine = RetrievalEngine()
        request = build_request(required_sources=("memory", "task"))
        response = engine.retrieve(request, RetrievalContext(task_history=object()))
        self.assertIn("memory:1", response.memory_references)

    def test_engine_retrieve_context_with_conversation(self) -> None:
        engine = RetrievalEngine()
        response = engine.retrieve(build_request(required_sources=("conversation",)), RetrievalContext(conversation_history=object()))
        self.assertTrue(response.conversation_references)

    def test_engine_retrieve_context_with_workflow(self) -> None:
        engine = RetrievalEngine()
        response = engine.retrieve(build_request(required_sources=("workflow",)), RetrievalContext(workflow_history=object()))
        self.assertTrue(response.workflow_references)

    def test_engine_retrieve_context_with_task(self) -> None:
        engine = RetrievalEngine()
        response = engine.retrieve(build_request(required_sources=("task",)), RetrievalContext(task_history=object()))
        self.assertTrue(response.task_references)

    def test_engine_retrieve_context_with_provider(self) -> None:
        engine = RetrievalEngine()
        response = engine.retrieve(build_request(required_sources=("provider",)), RetrievalContext(provider_history=object()))
        self.assertEqual(response.retrieved_items[0]["source"], "provider")

    def test_engine_retrieve_context_with_plugin(self) -> None:
        engine = RetrievalEngine()
        response = engine.retrieve(build_request(required_sources=("plugin",)), RetrievalContext(plugin_history=object()))
        self.assertEqual(response.retrieved_items[0]["source"], "plugin")

    def test_engine_retrieve_context_with_execution(self) -> None:
        engine = RetrievalEngine()
        response = engine.retrieve(build_request(required_sources=("execution",)), RetrievalContext(execution_history=object()))
        self.assertEqual(response.retrieved_items[0]["source"], "execution")

    def test_engine_retrieve_hybrid_strategy(self) -> None:
        response = RetrievalEngine().retrieve(build_request(retrieval_strategy=RetrievalStrategy.HYBRID), RetrievalContext())
        self.assertGreaterEqual(response.confidence, 0.0)

    def test_engine_retrieve_exact_match_strategy(self) -> None:
        response = RetrievalEngine().retrieve(build_request(retrieval_strategy=RetrievalStrategy.EXACT_MATCH), RetrievalContext())
        self.assertEqual(response.metadata["strategy"], "exact_match")

    def test_engine_retrieve_recent_first_strategy(self) -> None:
        response = RetrievalEngine().retrieve(build_request(retrieval_strategy=RetrievalStrategy.RECENT_FIRST), RetrievalContext())
        self.assertEqual(response.metadata["strategy"], "recent_first")

    def test_engine_retrieve_priority_first_strategy(self) -> None:
        response = RetrievalEngine().retrieve(build_request(retrieval_strategy=RetrievalStrategy.PRIORITY_FIRST), RetrievalContext())
        self.assertEqual(response.metadata["strategy"], "priority_first")

    def test_engine_retrieve_metadata_search_strategy(self) -> None:
        response = RetrievalEngine().retrieve(build_request(retrieval_strategy=RetrievalStrategy.METADATA_SEARCH), RetrievalContext())
        self.assertEqual(response.metadata["strategy"], "metadata_search")

    def test_engine_retrieve_reference_search_strategy(self) -> None:
        response = RetrievalEngine().retrieve(build_request(retrieval_strategy=RetrievalStrategy.REFERENCE_SEARCH), RetrievalContext())
        self.assertEqual(response.metadata["strategy"], "reference_search")

    def test_engine_cache_is_populated(self) -> None:
        engine = RetrievalEngine()
        request = build_request()
        engine.retrieve(request, RetrievalContext())
        self.assertEqual(engine.cache.lookup("recent_queries", request.request_id), request.query)

    def test_engine_history_is_populated(self) -> None:
        engine = RetrievalEngine()
        engine.retrieve(build_request(), RetrievalContext())
        self.assertEqual(engine.history.statistics()["retrievals"], 1)

    def test_engine_metrics_increment(self) -> None:
        engine = RetrievalEngine()
        engine.retrieve(build_request(), RetrievalContext())
        self.assertEqual(engine.metrics.requests, 1)

    def test_engine_response_contains_statistics(self) -> None:
        response = RetrievalEngine().retrieve(build_request(), RetrievalContext())
        self.assertIn("sources_used", response.statistics)

    def test_engine_response_contains_metadata(self) -> None:
        response = RetrievalEngine().retrieve(build_request(), RetrievalContext())
        self.assertEqual(response.metadata["strategy"], "hybrid")

    def test_manager_statistics_object(self) -> None:
        stats = RetrievalManager().statistics()
        self.assertIsInstance(stats, RetrievalStatistics)

    def test_retrieval_manager_logs(self) -> None:
        manager = RetrievalManager()
        self.assertIsNotNone(manager.logger_factory.logger)

    def test_retrieval_history_record_timestamp(self) -> None:
        record = RetrievalHistoryRecord(
            retrieval_id="r",
            request_id="q",
            conversation_id=None,
            workflow_id=None,
            strategy=RetrievalStrategy.HYBRID,
            sources_used=("memory",),
            retrieved_items=(),
            execution_time_ms=1.0,
            confidence=0.5,
        )
        self.assertIsNotNone(record.timestamp)

    def test_retrieval_confidence_validates_range(self) -> None:
        self.assertTrue(RetrievalValidator().validate_confidence(1.0)[0])

    def test_retrieval_confidence_invalid_range(self) -> None:
        self.assertFalse(RetrievalValidator().validate_confidence(1.5)[0])

    def test_retrieval_selector_default_sources_include_memory(self) -> None:
        self.assertIn("memory", RetrievalSelector().determine_sources(build_request()))

    def test_retrieval_selector_default_sources_include_knowledge(self) -> None:
        self.assertIn("knowledge", RetrievalSelector().determine_sources(build_request()))

    def test_retrieval_engine_response_lists_references(self) -> None:
        response = RetrievalEngine().retrieve(build_request(), RetrievalContext())
        self.assertTrue(response.memory_references or response.knowledge_references)

    def test_retrieval_engine_query_requires_sources(self) -> None:
        response = RetrievalEngine().retrieve(build_request(required_sources=("memory",)), RetrievalContext())
        self.assertTrue(response.retrieved_items)

    def test_retrieval_manager_statistics_health(self) -> None:
        self.assertEqual(RetrievalManager().statistics().overall_retrieval_health, "healthy")

    def test_jarvis_manager_exposes_retrieval(self) -> None:
        self.assertTrue(JarvisManager().retrieval.initialized)

    def test_jarvis_manager_statistics_include_retrieval(self) -> None:
        self.assertEqual(JarvisManager().statistics().retrieval_status, "ready")

    def test_jarvis_core_initializes_retrieval(self) -> None:
        self.assertTrue(JarvisCore(context=JarvisContext(request_id="test")).manager.retrieval.initialized)

    def test_jarvis_request_can_flow_to_retrieval(self) -> None:
        request = JarvisRequest(request_id="r1", content="retrieve")
        self.assertEqual(request.request_id, "r1")

    def test_retrieval_result_confidence_stored(self) -> None:
        response = RetrievalEngine().retrieve(build_request(), RetrievalContext())
        self.assertGreaterEqual(response.confidence, 0.0)

    def test_cache_lookup_missing_returns_none(self) -> None:
        self.assertIsNone(RetrievalCache().lookup("recent_results", "missing"))

    def test_cache_invalidate_all(self) -> None:
        cache = RetrievalCache()
        cache.create("recent_queries", "q1", 1)
        cache.invalidate()
        self.assertIsNone(cache.lookup("recent_queries", "q1"))

    def test_manager_retrieve_respects_context(self) -> None:
        manager = RetrievalManager(context=RetrievalContext(conversation_history=object()))
        response = manager.retrieve(build_request(required_sources=("conversation",)))
        self.assertTrue(response.conversation_references)

    def test_engine_statistics_response_metadata(self) -> None:
        response = RetrievalEngine().retrieve(build_request(), RetrievalContext())
        self.assertIn("strategy", response.metadata)

    def test_validator_results_api(self) -> None:
        self.assertTrue(RetrievalValidator().validate_results(RetrievalResponse())[0])

    def test_validator_ranking_api(self) -> None:
        self.assertTrue(RetrievalValidator().validate_ranking(RetrievalResponse())[0])

    def test_validator_references_api(self) -> None:
        self.assertTrue(RetrievalValidator().validate_references(RetrievalResponse())[0])

    def test_request_metadata_default(self) -> None:
        self.assertEqual(build_request().metadata, {})

    def test_response_metadata_default(self) -> None:
        self.assertEqual(RetrievalResponse().metadata, {})

    def test_history_strategy_persistence(self) -> None:
        history = RetrievalHistory()
        history.append(
            RetrievalHistoryRecord(
                retrieval_id="r2",
                request_id="q2",
                conversation_id="c2",
                workflow_id="w2",
                strategy=RetrievalStrategy.KNOWLEDGE_FIRST,
                sources_used=("knowledge",),
                retrieved_items=(),
                execution_time_ms=1.0,
                confidence=0.7,
            )
        )
        self.assertEqual(history.list()[0].strategy, RetrievalStrategy.KNOWLEDGE_FIRST)

    def test_diagnostics_source_report(self) -> None:
        self.assertEqual(RetrievalDiagnostics().source_report()["status"], "ready")

    def test_diagnostics_performance_report(self) -> None:
        self.assertEqual(RetrievalDiagnostics().performance_report()["status"], "ready")

    def test_diagnostics_validation_report(self) -> None:
        self.assertEqual(RetrievalDiagnostics().validation_report()["status"], "ready")

    def test_selector_prioritizes_sources(self) -> None:
        self.assertEqual(RetrievalSelector().determine_search_order(("knowledge", "memory")), ("knowledge", "memory"))

    def test_manager_statistics_cache_status(self) -> None:
        self.assertEqual(RetrievalManager().statistics().cache_status, "ready")

    def test_engine_can_return_empty_metadata_for_invalid_request(self) -> None:
        response = RetrievalEngine().retrieve(RetrievalRequest(intent="", goal="", query=""), RetrievalContext())
        self.assertIn("errors", response.metadata)

    def test_context_has_metadata_dict(self) -> None:
        self.assertIsInstance(RetrievalContext().metadata, dict)

    def test_history_empty_after_new_manager(self) -> None:
        self.assertEqual(len(RetrievalManager().history.list()), 0)

    def test_metrics_object_is_mutable(self) -> None:
        metrics = RetrievalMetrics(requests=1)
        metrics.requests += 1
        self.assertEqual(metrics.requests, 2)

    def test_ranker_context_argument(self) -> None:
        self.assertEqual(RetrievalRanker().rank(({"priority": 1},), context=object())[0]["priority"], 1)

    def test_engine_source_selection_memory_and_knowledge(self) -> None:
        response = RetrievalEngine().retrieve(build_request(), RetrievalContext())
        self.assertGreaterEqual(len(response.retrieved_items), 2)

    def test_manager_initialization_statistics(self) -> None:
        self.assertEqual(RetrievalManager().initialize().retrieval_engine_status, "ready")


if __name__ == "__main__":
    unittest.main()
