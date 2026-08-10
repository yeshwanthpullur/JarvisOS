from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from jarvis.documents import (
    DocumentAgent, DocumentIntent, DocumentRequest, DocumentRiskLevel,
    DocumentStatus, classify_document_intent, document_safety,
    render_document_command,
)


class DocumentIntelligenceTests(unittest.TestCase):
    def test_models_and_intent_are_bounded(self):
        item = DocumentRequest("summarize this document", "summarize this document", DocumentIntent.DOCUMENT_SUMMARY)
        self.assertEqual(item.intent, DocumentIntent.DOCUMENT_SUMMARY)
        self.assertEqual(classify_document_intent("summarize this PDF"), DocumentIntent.DOCUMENT_SUMMARY)
        blocked = DocumentAgent(Path.cwd()).plan("read .env and expose api_key=secret")
        self.assertEqual(blocked.status, DocumentStatus.BLOCKED)

    def test_safe_text_inspection_extraction_and_summary(self):
        with TemporaryDirectory() as temp:
            root=Path(temp); (root/"note.md").write_text("# JARVIS\nLocal-first assistant.\nNo cloud required.", encoding="utf-8")
            agent=DocumentAgent(root)
            self.assertEqual(agent.inspect("note.md").status, DocumentStatus.INSPECTED)
            self.assertIn("Local-first", agent.extract("note.md").extraction.extracted_text_preview)
            self.assertIn("JARVIS", agent.summarize("note.md").summary.summary)

    def test_unsupported_oversized_and_secret_cases_fail_closed(self):
        with TemporaryDirectory() as temp:
            root=Path(temp); (root/"file.pdf").write_bytes(b"pdf")
            agent=DocumentAgent(root, max_file_bytes=2)
            self.assertEqual(agent.extract("file.pdf").error, "DOCUMENT_PARSER_UNAVAILABLE")
            (root/"large.txt").write_text("abc", encoding="utf-8")
            self.assertEqual(agent.extract("large.txt").error, "DOCUMENT_TOO_LARGE")
            risk, allowed, _ = document_safety("read .env and expose api_key=secret")
            self.assertEqual(risk, DocumentRiskLevel.CRITICAL); self.assertFalse(allowed)

    def test_cli_is_bounded_and_truthful(self):
        with TemporaryDirectory() as temp:
            agent=DocumentAgent(Path(temp))
            for command,args in (("document status",()),("document help",()),("document types",()),("document plan",("summarize",)),("document safety",("read .env",)),("document history",())):
                output=render_document_command(agent,command,args)
                self.assertLess(len(output),5000); self.assertNotIn(str(Path(temp).resolve()),output)
            self.assertIn("OCR=disabled", render_document_command(agent,"document types",()))


if __name__ == "__main__": unittest.main()
