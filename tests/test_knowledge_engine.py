"""Tests for the JARVIS OS Knowledge Engine."""

from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from knowledge import DocumentType, KnowledgeManager, NoOpSummarizer
from memory import MemoryManager


class KnowledgeEngineTests(unittest.TestCase):
    """Knowledge Engine import, search, and memory-link tests."""

    def test_import_txt_creates_document_chunks_and_memory_link(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "notes.txt"
            source.write_text(
                "JARVIS reads documents.\nKnowledge chunks are searchable.",
                encoding="utf-8",
            )
            memory_manager = MemoryManager(root / "memory")
            memory_manager.initialize()
            manager = KnowledgeManager(root / "knowledge", memory_manager=memory_manager)
            manager.initialize()

            result = manager.import_file(source, tags=("docs",), related_tasks=("task-1",))

            self.assertEqual(result.document.document_type, DocumentType.TXT)
            self.assertEqual(result.document.tags, ("docs",))
            self.assertEqual(result.document.related_tasks, ("task-1",))
            self.assertIsNotNone(result.linked_memory_id)
            self.assertEqual(manager.statistics().total_documents, 1)
            self.assertGreaterEqual(manager.statistics().total_chunks, 1)
            self.assertEqual(memory_manager.count_memories(), 1)

            search_results = manager.search_knowledge("searchable")
            self.assertEqual(len(search_results), 1)
            self.assertEqual(search_results[0].document_id, result.document.document_id)

    def test_import_json_csv_html_and_python_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            samples = {
                "data.json": '{"name": "Jarvis", "kind": "knowledge"}',
                "table.csv": "name,type\nJarvis,OS\n",
                "page.html": "<html><body><h1>Jarvis</h1><p>HTML knowledge</p></body></html>",
                "script.py": "def hello() -> str:\n    return 'jarvis'\n",
            }
            manager = KnowledgeManager(root / "knowledge")
            manager.initialize()

            imported_types = []
            for filename, content in samples.items():
                path = root / filename
                path.write_text(content, encoding="utf-8")
                imported_types.append(manager.import_file(path).document.document_type)

            self.assertEqual(
                imported_types,
                [
                    DocumentType.JSON,
                    DocumentType.CSV,
                    DocumentType.HTML,
                    DocumentType.PYTHON,
                ],
            )
            self.assertEqual(manager.statistics().total_documents, 4)
            self.assertTrue(manager.search_knowledge("Jarvis"))

    def test_import_docx_and_pdf_best_effort_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docx_path = root / "sample.docx"
            pdf_path = root / "sample.pdf"
            self._write_minimal_docx(docx_path, "DOCX knowledge")
            pdf_path.write_bytes(b"%PDF-1.4\n1 0 obj\n(Readable PDF knowledge)\nendobj\n")

            manager = KnowledgeManager(root / "knowledge")
            manager.initialize()

            docx = manager.import_file(docx_path)
            pdf = manager.import_file(pdf_path)

            self.assertEqual(docx.document.document_type, DocumentType.DOCX)
            self.assertEqual(pdf.document.document_type, DocumentType.PDF)
            self.assertTrue(manager.search_knowledge("DOCX"))
            self.assertTrue(manager.search_knowledge("PDF"))

    def test_noop_summarizer_is_future_interface_only(self) -> None:
        summarizer = NoOpSummarizer()

        with self.assertRaises(NotImplementedError):
            summarizer.summarize(None, ())  # type: ignore[arg-type]

    def _write_minimal_docx(self, path: Path, text: str) -> None:
        document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:r>
        <w:t>{text}</w:t>
      </w:r>
    </w:p>
  </w:body>
</w:document>
"""
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("word/document.xml", document_xml)


if __name__ == "__main__":
    unittest.main()
