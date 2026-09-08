from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
import tempfile
import unittest

from jarvis.documents import BlockType, CanonicalDocument, DocumentBlock
from jarvis.knowledge import (
    ChromaVectorStore,
    DeterministicEmbeddingProvider,
    DeterministicReranker,
    FaissVectorStore,
    QdrantVectorStore,
    RAGRuntime,
    VectorRecord,
    VectorStoreRouter,
)
from jarvis.memory_governance import (
    GovernedMemoryStatus,
    GovernedMemoryStore,
    GraphitiAdapter,
    Mem0Adapter,
    MemoryOrigin,
    MemoryScope,
    TemporalFact,
)
from jarvis.workers.assurance import EvidenceStore


def document(texts: tuple[str, ...] = ("Electric motors use a rotor and stator.",), *, version: str = "version-1") -> CanonicalDocument:
    item = CanonicalDocument.create("motor-notes.txt", "text/plain", "\n".join(texts).encode())
    blocks = tuple(DocumentBlock(f"block-{index}", BlockType.PARAGRAPH, text, index, 1, "section-motors", f"page:1:block:{index}", backend="builtin") for index, text in enumerate(texts))
    return replace(item, version_id=version, blocks=blocks)


class RAGPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.vector = QdrantVectorStore(self.root / "vectors.json", available=True)
        self.runtime = RAGRuntime(vector_router=VectorStoreRouter((self.vector,)), state_path=self.root / "rag.json")

    def tearDown(self) -> None: self.temp.cleanup()

    def test_document_ingestion_is_bounded_deduplicated_and_provenance_aware(self) -> None:
        doc = document(("Rotor " * 300,))
        first = self.runtime.ingest_document(doc); second = self.runtime.ingest_document(doc)
        self.assertEqual(first, second); self.assertLessEqual(len(self.runtime.index.chunks[first[0]].text_or_reference), 800)
        result = self.runtime.retrieve("rotor")
        self.assertEqual(result.state, "SUPPORTED"); self.assertEqual(result.fragments[0].document_id, doc.document_id)
        self.assertEqual(result.fragments[0].source_type, "local_document"); self.assertIn(first[0], self.runtime.claim_support(("rotor",), result)["rotor"])

    def test_project_scope_isolation_and_unknown_query_do_not_fabricate_sources(self) -> None:
        self.runtime.ingest_document(document(("Project blue motor winding",)), project_id="blue")
        self.assertEqual(self.runtime.retrieve("winding", project_id="red").state, "UNSUPPORTED")
        unknown = self.runtime.retrieve("completely absent quasar")
        self.assertEqual(unknown.citations, ()); self.assertEqual(unknown.fragments, ())

    def test_rag_state_and_retrieval_survive_restart(self) -> None:
        refs = self.runtime.ingest_document(document(("Persistent rotor provenance",)))
        restored = RAGRuntime(vector_router=VectorStoreRouter((QdrantVectorStore(self.root / "vectors.json", available=True),)), state_path=self.root / "rag.json")
        self.assertEqual(restored.citation(refs[0]), self.runtime.citation(refs[0])); self.assertEqual(restored.retrieve("persistent rotor").state, "SUPPORTED")

    def test_stale_conflicting_and_deleted_citations_are_enforced(self) -> None:
        doc = document(("Motor efficiency is high.", "Motor efficiency is not high."))
        refs = self.runtime.ingest_document(doc); self.runtime.mark_conflicting(*refs)
        self.assertEqual(self.runtime.retrieve("motor efficiency").state, "CONFLICTING")
        self.assertEqual(self.runtime.mark_document_stale(doc.document_id, "version-2"), refs)
        with self.assertRaisesRegex(ValueError, "invalid_retrieval_citation"): self.runtime.citation(refs[0])
        self.assertTrue(self.runtime.delete_source(doc.source.source_id)); self.assertIsNone(self.vector.get("jarvis_knowledge", refs[0]))

    def test_retrieval_proof_persists_without_raw_query(self) -> None:
        self.runtime.ingest_document(document()); context = self.runtime.retrieve("rotor")
        proof = self.runtime.proof(context); store = EvidenceStore(self.root / "evidence.json")
        store.add(proof); restored = EvidenceStore(self.root / "evidence.json")
        self.assertEqual(restored.list()[0].integrity, proof.integrity); self.assertNotIn("rotor", restored.list()[0].safe_reference)


class VectorAndEmbeddingTests(unittest.TestCase):
    def setUp(self) -> None: self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
    def tearDown(self) -> None: self.temp.cleanup()
    def record(self, identifier: str = "one", vector: tuple[float, ...] = (1.0, 0.0), *, version: str = "1", namespace: str = "project:a") -> VectorRecord:
        return VectorRecord(identifier, namespace, vector, (("project", namespace),), "fixture", version, len(vector), identifier * 8)

    def test_qdrant_contract_create_search_filter_delete_and_reload(self) -> None:
        path = self.root / "qdrant.json"; store = QdrantVectorStore(path, available=True)
        self.assertTrue(store.create_collection("items")); store.upsert("items", self.record()); store.upsert("items", self.record("two", (0.0, 1.0), namespace="project:b"))
        self.assertEqual(store.search("items", (1.0, 0.0), filters={"project": "project:a"})[0].record_id, "one")
        self.assertEqual(QdrantVectorStore(path, available=True).count("items"), 2)
        self.assertTrue(store.delete("items", "one")); self.assertTrue(store.delete_collection("items"))

    def test_shared_chroma_contract_and_faiss_limitations_are_truthful(self) -> None:
        chroma = ChromaVectorStore(self.root / "chroma.json", available=True); chroma.create_collection("c"); chroma.upsert("c", self.record())
        self.assertEqual(chroma.search("c", (1.0, 0.0))[0].record_id, "one")
        faiss = FaissVectorStore(self.root / "faiss.json", available=True); faiss.create_collection("c"); faiss.upsert("c", self.record())
        self.assertFalse(faiss.capabilities.persistence); self.assertFalse(faiss.capabilities.metadata_filtering)
        with self.assertRaisesRegex(ValueError, "metadata_filtering_unsupported"): faiss.search("c", (1.0, 0.0), filters={"project": "project:a"})

    def test_backend_order_fallback_and_namespace_isolation(self) -> None:
        qdrant = QdrantVectorStore(available=False); chroma = ChromaVectorStore(self.root / "chroma.json", available=True); faiss = FaissVectorStore(self.root / "faiss.json", available=True)
        self.assertIs(VectorStoreRouter((faiss, chroma, qdrant)).select(), chroma)
        chroma.create_collection("c"); chroma.upsert("c", self.record()); chroma.upsert("c", self.record("two", namespace="project:b"))
        self.assertEqual(chroma.count("c", "project:a"), 1); self.assertFalse(VectorStoreRouter((qdrant,)).status()["silent_data_migration"])

    def test_vector_dimension_and_model_version_mismatch_rejected(self) -> None:
        store = QdrantVectorStore(self.root / "q.json", available=True); store.create_collection("c"); store.upsert("c", self.record())
        with self.assertRaisesRegex(ValueError, "vector_dimension_mismatch"): store.search("c", (1.0,))
        with self.assertRaisesRegex(ValueError, "vector_index_version_mismatch"): store.upsert("c", self.record("two", version="2"))

    def test_embedding_metadata_batch_bounds_privacy_and_determinism(self) -> None:
        provider = DeterministicEmbeddingProvider(version="7", dimension=8, max_batch=2)
        self.assertEqual(provider.metadata.version, "7"); self.assertEqual(provider.embed("motor"), provider.embed("motor")); self.assertEqual(len(provider.embed("motor")), 8)
        with self.assertRaisesRegex(ValueError, "embedding_batch_too_large"): provider.embed_batch(("a", "b", "c"))
        with self.assertRaisesRegex(ValueError, "cloud_embedding_denied"): DeterministicEmbeddingProvider(local=False).embed_batch(("private",))

    def test_reranking_and_unavailable_fallback(self) -> None:
        candidates = (("one", "motor rotor", .2), ("two", "unrelated", .9))
        self.assertEqual(DeterministicReranker().rerank("motor rotor", candidates)[0][0], "one")
        self.assertEqual(DeterministicReranker(False).rerank("motor rotor", candidates), (("one", .2), ("two", .9)))

    def test_optional_backend_detection_never_fakes_native_readiness(self) -> None:
        for store in (QdrantVectorStore(), ChromaVectorStore(), FaissVectorStore()):
            status = store.detect(); self.assertIn(status["state"], {"ready", "unavailable"})
            if not status["installed"]: self.assertEqual(status["state"], "unavailable")


class GovernedMemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.vector = QdrantVectorStore(self.root / "memory-vectors.json", available=True)
        self.store = GovernedMemoryStore(self.root / "memory.json", vector_store=self.vector)
    def tearDown(self) -> None: self.temp.cleanup()
    def create(self, content: str = "Prefer concise technical explanations", **kwargs):
        values = dict(scope=MemoryScope.PERSONAL, source="explicit_command", provenance="user:memory remember", explicit=True, authority=True)
        values.update(kwargs); return self.store.create("response preference", content, **values)

    def test_explicit_and_inferred_memory_have_distinct_states_and_provenance(self) -> None:
        explicit = self.create(); inferred = self.create("May prefer diagrams", scope=MemoryScope.PROJECT, project_id="alpha", explicit=False)
        self.assertEqual(explicit.origin, MemoryOrigin.EXPLICIT); self.assertTrue(explicit.provenance)
        self.assertEqual(inferred.origin, MemoryOrigin.INFERRED); self.assertEqual(inferred.status, GovernedMemoryStatus.NEEDS_REVIEW)

    def test_authority_scope_and_project_session_isolation(self) -> None:
        with self.assertRaisesRegex(PermissionError, "memory_authority_required"): self.store.create("x", "value", scope=MemoryScope.KNOWLEDGE, source="test", provenance="test", explicit=True)
        with self.assertRaisesRegex(ValueError, "memory_scope_required"): self.store.create("x", "value", scope=None, source="test", provenance="test", explicit=True, authority=True)
        self.create("Alpha build uses pytest", scope=MemoryScope.PROJECT, project_id="alpha")
        self.create("Beta build uses unittest", scope=MemoryScope.PROJECT, project_id="beta")
        self.assertEqual({item.project_id for item in self.store.search("build", scope=MemoryScope.PROJECT, project_id="alpha", requesting_agent="coding_agent")}, {"alpha"})
        self.create("Session red note", scope=MemoryScope.SESSION, session_id="red")
        self.assertFalse(self.store.search("note", scope=MemoryScope.SESSION, session_id="blue", requesting_agent="conversation_agent"))

    def test_personal_memory_denied_to_unrelated_agent(self) -> None:
        self.create()
        with self.assertRaisesRegex(PermissionError, "personal_memory_denied"): self.store.search("concise", scope=MemoryScope.PERSONAL, requesting_agent="coding_agent", personal_allowed=True)
        self.assertTrue(self.store.search("concise", scope=MemoryScope.PERSONAL, requesting_agent="memory_agent", personal_allowed=True))

    def test_update_supersede_and_identical_update(self) -> None:
        original = self.create(); same = self.store.update(original.memory_id, original.content, provenance="user:update", authority=True)
        self.assertEqual(same.memory_id, original.memory_id); self.assertEqual(self.store.records[original.memory_id].status, GovernedMemoryStatus.ACTIVE)
        current = self.store.update(original.memory_id, "Prefer detailed technical explanations", provenance="user:update", authority=True)
        self.assertEqual(current.supersedes, original.memory_id); self.assertEqual(self.store.records[original.memory_id].status, GovernedMemoryStatus.SUPERSEDED)
        self.assertNotIn(original.memory_id, {item.memory_id for item in self.store.search("explanations", scope=MemoryScope.PERSONAL, requesting_agent="memory_agent", personal_allowed=True)})

    def test_stale_delete_expiry_restore_and_vector_propagation(self) -> None:
        stale = self.create("Temporary old preference"); self.assertIsNotNone(self.vector.get("jarvis_memory", stale.memory_id))
        self.assertTrue(self.store.mark_stale(stale.memory_id, authority=True)); self.assertIsNone(self.vector.get("jarvis_memory", stale.memory_id))
        deleted = self.create("Delete this preference"); self.assertTrue(self.store.delete(deleted.memory_id, authority=True)); self.assertFalse(self.store.inspect(deleted.memory_id)["content_available"])
        due = (datetime.now(UTC) - timedelta(seconds=1)).isoformat(); expiring = self.create("Temporary expiring preference", expiry=due)
        self.assertEqual(self.store.expire(authority=True), (expiring.memory_id,)); self.assertTrue(self.store.restore(expiring.memory_id, authority=True))

    def test_deduplication_conflict_secret_rejection_and_restart(self) -> None:
        first = self.create("Prefer short answers"); self.assertEqual(self.create("Prefer short answers").memory_id, first.memory_id)
        conflict = self.create("Prefer long answers"); self.assertEqual(conflict.status, GovernedMemoryStatus.CONFLICTING)
        with self.assertRaisesRegex(ValueError, "unsafe_memory_content"): self.create("api_key=abc123")
        restored = GovernedMemoryStore(self.root / "memory.json", vector_store=QdrantVectorStore(self.root / "memory-vectors.json", available=True))
        self.assertEqual(restored.records[first.memory_id].content, first.content); self.assertTrue(restored.history)

    def test_cross_scope_and_least_context_policy(self) -> None:
        self.create("Project rotor detail", scope=MemoryScope.PROJECT, project_id="alpha")
        self.create("Knowledge rotor definition", scope=MemoryScope.KNOWLEDGE)
        with self.assertRaisesRegex(PermissionError, "cross_scope_memory_denied"): self.store.search("rotor", scope=MemoryScope.KNOWLEDGE, requesting_agent="coding_agent", allow_cross_scope=True)
        context = self.store.context("rotor", ((MemoryScope.PROJECT, "alpha", ""), (MemoryScope.KNOWLEDGE, "", "")), requesting_agent="memory_agent", max_chars=60)
        self.assertLessEqual(sum(len(item.content) for item in context), 60); self.assertEqual({item.scope for item in context}, {MemoryScope.PROJECT, MemoryScope.KNOWLEDGE})

    def test_mem0_adapter_is_governance_wrapped_and_degrades_truthfully(self) -> None:
        adapter = Mem0Adapter(self.store); status = adapter.detect(); self.assertEqual(status["authority"], "jarvis_memory_governance")
        item = adapter.add("topic", "Remember motor notes", scope=MemoryScope.KNOWLEDGE, source="user", provenance="explicit", explicit=True, authority=True)
        self.assertTrue(adapter.search("motor", scope=MemoryScope.KNOWLEDGE, requesting_agent="memory_agent")); self.assertTrue(adapter.delete(item.memory_id, authority=True))
        if not status["installed"]: self.assertEqual(status["state"], "unavailable")

    def test_graphiti_temporal_foundation_preserves_history(self) -> None:
        adapter = GraphitiAdapter(); start = datetime.now(UTC).isoformat()
        old = TemporalFact("fact-1", "project", "phase", "design", start, None, start, "user", .9); adapter.add(old)
        new = TemporalFact("fact-2", "project", "phase", "build", start, None, start, "user", .9); adapter.supersede(old.fact_id, new)
        self.assertEqual(adapter.current("project", "phase")[0].object_value, "build"); self.assertEqual(adapter.facts[old.fact_id].status, "superseded"); self.assertEqual(len(adapter.traverse("project")), 2)


if __name__ == "__main__": unittest.main()
