from __future__ import annotations

from dataclasses import replace
import io
from pathlib import Path
import tempfile
import unittest
import zipfile

from jarvis.documents import (
    BlockType,
    CanonicalDocument,
    CloudOCRAdapter,
    DoclingAdapter,
    DocumentIntelligenceRuntime,
    DocumentRouter,
    MarkerAdapter,
    OCRRequest,
    OCRRouter,
    OCRState,
    PaddleOCRAdapter,
    ParserRegistry,
    BuiltinDocumentParser,
)
from jarvis.workers.assurance_models import WorkCheckpoint
from jarvis.workers.checkpoints import CheckpointStore
from jarvis.workers.models import WorkerTaskStatus


PDF = b"%PDF-1.4\n1 0 obj <<>> endobj\nBT (Electric motor rotor) Tj ET\n%%EOF"
PNG = b"\x89PNG\r\n\x1a\n" + b"fixture"


def zip_bytes(files: dict[str, str]) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, value in files.items(): archive.writestr(name, value)
    return stream.getvalue()


DOCX = zip_bytes({"word/document.xml": """<w:document xmlns:w="urn:w"><w:body><w:p><w:r><w:t>Motor Notes</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>Part</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Rotor</w:t></w:r></w:p></w:tc></w:tr></w:tbl></w:body></w:document>"""})
PPTX = zip_bytes({"ppt/slides/slide1.xml": """<p:sld xmlns:p="urn:p" xmlns:a="urn:a"><p:cSld><a:t>Motor Slide</a:t><a:t>Rotor detail</a:t></p:cSld></p:sld>"""})


class DocumentFoundationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
    def tearDown(self) -> None: self.temp.cleanup()
    def write(self, name: str, data: bytes) -> Path:
        path=self.root/name; path.write_bytes(data); return path

    def test_supported_document_detected_and_source_is_immutable(self) -> None:
        path=self.write("notes.pdf",PDF); runtime=DocumentIntelligenceRuntime(self.root)
        doc=runtime.ingest(path.name)
        self.assertEqual(doc.source.display_name,"notes.pdf"); self.assertEqual(len(doc.source.immutable_digest),64)
        self.assertEqual(doc.blocks[0].text,"Electric motor rotor")

    def test_unsupported_empty_and_oversized_degrade_cleanly(self) -> None:
        self.write("bad.bin",b"x")
        with self.assertRaisesRegex(ValueError,"unsupported_document_type"): DocumentIntelligenceRuntime(self.root).ingest("bad.bin")
        self.write("empty.txt",b"")
        with self.assertRaisesRegex(ValueError,"document_empty"): DocumentIntelligenceRuntime(self.root).ingest("empty.txt")
        self.write("large.txt",b"x"*20)
        with self.assertRaisesRegex(ValueError,"document_too_large"): DocumentIntelligenceRuntime(self.root,max_file_bytes=10).ingest("large.txt")

    def test_structure_order_and_provenance_retained(self) -> None:
        path=self.write("notes.md",b"# Heading\nFirst\nSecond")
        doc=DocumentIntelligenceRuntime(self.root).ingest(path.name)
        self.assertEqual([item.order for item in doc.blocks],[0,1,2]); self.assertEqual(doc.sections[0].title,"Heading")
        self.assertEqual(doc.provenance[0].source_id,doc.source.source_id)

    def test_docling_heading_table_and_page_normalization(self) -> None:
        parser=DoclingAdapter(lambda data,media:{"blocks":[{"type":"heading","text":"Title","page":1},{"type":"paragraph","text":"Body","page":1}],"tables":[{"rows":[["A","B"],["1","2"]],"page":1}]})
        doc=CanonicalDocument.create("fixture.pdf","application/pdf",PDF)
        parsed=parser.parse(doc,PDF)
        self.assertEqual(parsed.blocks[0].block_type,BlockType.HEADING); self.assertEqual(parsed.tables[0].rows[1][1],"2")
        self.assertEqual(parsed.pages[0].page_number,1); self.assertEqual(parsed.provenance[0].backend,"docling")

    def test_docling_malformed_error_and_output_limit(self) -> None:
        failing=DoclingAdapter(lambda data,media:(_ for _ in ()).throw(RuntimeError("bad")))
        doc=CanonicalDocument.create("fixture.pdf","application/pdf",PDF)
        with self.assertRaisesRegex(ValueError,"parser_failed"): failing.parse(doc,PDF)
        parser=DoclingAdapter(lambda data,media:{"blocks":[{"type":"paragraph","text":"x"*1000}]})
        self.assertLessEqual(len(parser.parse(doc,PDF,max_chars=100).blocks[0].text),100)

    def test_marker_fallback_and_successful_primary_not_overwritten(self) -> None:
        path=self.write("fixture.pdf",PDF)
        docling=DoclingAdapter(lambda d,m:(_ for _ in ()).throw(RuntimeError("bad")))
        marker=MarkerAdapter(lambda d,m:{"blocks":[{"type":"paragraph","text":"Marker result","page":1}]})
        runtime=DocumentIntelligenceRuntime(self.root,docling=docling,marker=marker)
        self.assertEqual(runtime.ingest(path.name).provenance[0].backend,"marker")
        docling_ok=DoclingAdapter(lambda d,m:{"blocks":[{"type":"paragraph","text":"Docling result","page":1}]})
        runtime=DocumentIntelligenceRuntime(self.root,docling=docling_ok,marker=marker)
        self.assertEqual(runtime.ingest(path.name).provenance[0].backend,"docling")

    def test_marker_detection_is_truthful(self) -> None:
        status=MarkerAdapter().detect(); self.assertIn(status["state"],{"unavailable","degraded"}); self.assertNotEqual(status["state"],"ready")

    def test_document_checkpoint_resumes_at_page(self) -> None:
        path=self.root/"state.json"; item=WorkCheckpoint("goal","project","doc-task","run","document_agent",WorkerTaskStatus.RUNNING,pending_stage="parse_page_35",completed_stages=("pages_1_34",))
        CheckpointStore(path).save(item); self.assertEqual(CheckpointStore(path).latest("doc-task").pending_stage,"parse_page_35")


class OCRAndRoutingTests(unittest.TestCase):
    def recognizer(self,data:bytes,language:str|None): return ({"text":"Rotor label","confidence":.42,"box":(1,2,30,10)},)
    def test_image_request_normalized_and_source_page_retained(self) -> None:
        request=OCRRequest("scan.png","image/png",PNG,page_number=2,language="en")
        result=PaddleOCRAdapter(self.recognizer).recognize(request)
        self.assertEqual(result.status,OCRState.READY); self.assertEqual(result.page_number,2); self.assertEqual(result.source_ref,"scan.png")
        self.assertIn("low_confidence",result.warnings); self.assertEqual(result.blocks[0].lines[0].box.x,1)

    def test_invalid_image_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError,"invalid_ocr_input"): OCRRequest("bad.png","image/png",b"not png")

    def test_local_only_and_private_modes_block_cloud(self) -> None:
        cloud=CloudOCRAdapter(configured=True,recognizer=self.recognizer)
        self.assertEqual(cloud.recognize(OCRRequest("scan.png","image/png",PNG)).error,"cloud_ocr_denied")
        request=OCRRequest("scan.png","image/png",PNG,privacy_mode="normal_hybrid",classification="private")
        self.assertEqual(cloud.recognize(request).error,"private_document_cloud_ocr_denied")

    def test_cloud_secret_is_symbolic_and_unconfigured_degrades(self) -> None:
        status=CloudOCRAdapter().detect(); self.assertEqual(status["state"],"unconfigured"); self.assertTrue(status["credential_reference"].endswith("_ENV"))
        with self.assertRaises(ValueError): CloudOCRAdapter(credential_reference="real-secret")

    def test_local_failure_routes_once_to_allowed_cloud_fallback(self) -> None:
        local=PaddleOCRAdapter(lambda d,l:(_ for _ in ()).throw(RuntimeError("fail"))); cloud=CloudOCRAdapter(configured=True,recognizer=self.recognizer)
        request=OCRRequest("scan.png","image/png",PNG,privacy_mode="normal_hybrid")
        result=OCRRouter((local,),(cloud,),1).route(request)
        self.assertTrue(result.cloud_used); self.assertEqual(result.backend,"baidu_ocr")

    def test_native_pdf_avoids_ocr_and_scanned_uses_it(self) -> None:
        router=DocumentRouter(ParserRegistry((BuiltinDocumentParser(),)),OCRRouter((PaddleOCRAdapter(self.recognizer),)))
        native=router.decide("application/pdf",native_text=True); scanned=router.decide("application/pdf",native_text=False,scanned=True)
        self.assertFalse(native.use_ocr); self.assertTrue(scanned.use_ocr); self.assertFalse(scanned.cloud_allowed)

    def test_route_reason_is_persisted_and_fallback_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/"scan.png").write_bytes(PNG)
            ocr=OCRRouter((PaddleOCRAdapter(self.recognizer),),(),1); runtime=DocumentIntelligenceRuntime(root,ocr=ocr)
            doc=runtime.ingest("scan.png",scanned=True)
            self.assertIn("local backend",runtime.routes[doc.document_id].reason.lower()); self.assertEqual(runtime.routes[doc.document_id].max_attempts,2)


class UnifiedFormatsAndQATests(unittest.TestCase):
    def setUp(self)->None: self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
    def tearDown(self)->None:self.temp.cleanup()
    def test_serialization_roundtrip_and_unknown_block_forward_compatible(self)->None:
        doc=CanonicalDocument.create("notes.txt","text/plain",b"hello"); doc=BuiltinDocumentParser().parse(doc,b"hello")
        raw=doc.to_json().replace('"paragraph"','"future_block"')
        restored=CanonicalDocument.from_json(raw); self.assertEqual(restored.blocks[0].block_type,BlockType.UNKNOWN); self.assertEqual(restored.source.immutable_digest,doc.source.immutable_digest)
    def test_docx_text_table_and_pptx_pages(self)->None:
        (self.root/"fixture.docx").write_bytes(DOCX); (self.root/"fixture.pptx").write_bytes(PPTX); runtime=DocumentIntelligenceRuntime(self.root)
        docx=runtime.ingest("fixture.docx"); pptx=runtime.ingest("fixture.pptx")
        self.assertTrue(any("Motor Notes" in b.text for b in docx.blocks)); self.assertEqual(docx.tables[0].rows[0],("Part","Rotor"))
        self.assertEqual(pptx.pages[0].page_number,1); self.assertTrue(any("Motor Slide" in b.text for b in pptx.blocks))
    def test_pdf_encrypted_and_malformed_are_not_bypassed(self)->None:
        (self.root/"encrypted.pdf").write_bytes(b"%PDF /Encrypt (secret) Tj")
        with self.assertRaisesRegex(ValueError,"parser_failed"): DocumentIntelligenceRuntime(self.root).ingest("encrypted.pdf")
        (self.root/"bad.docx").write_bytes(b"bad")
        with self.assertRaisesRegex(ValueError,"parser_failed"): DocumentIntelligenceRuntime(self.root).ingest("bad.docx")
    def test_grounded_answer_and_summary_include_source_references(self)->None:
        (self.root/"notes.md").write_text("# Motor\nThe rotor turns inside the stator.",encoding="utf-8"); runtime=DocumentIntelligenceRuntime(self.root); doc=runtime.ingest("notes.md")
        answer=runtime.ask(doc.document_id,"What does the rotor do?"); summary=runtime.summarize(doc.document_id)
        self.assertEqual(answer.status,"SUPPORTED_BY_DOCUMENT"); self.assertTrue(all(ref.startswith(doc.document_id) for ref in answer.evidence_refs)); self.assertTrue(summary.evidence_refs)
    def test_unsupported_answer_does_not_use_world_knowledge(self)->None:
        (self.root/"notes.txt").write_text("Only motor details.",encoding="utf-8"); runtime=DocumentIntelligenceRuntime(self.root); doc=runtime.ingest("notes.txt")
        answer=runtime.ask(doc.document_id,"Who won the tournament?"); self.assertEqual(answer.status,"NOT_FOUND_IN_DOCUMENT"); self.assertIn("No external",answer.limitations[0])
    def test_conflicting_sections_are_surfaced(self)->None:
        (self.root/"notes.txt").write_text("The rotor is active.\nHowever the rotor is not active.",encoding="utf-8"); runtime=DocumentIntelligenceRuntime(self.root); doc=runtime.ingest("notes.txt")
        self.assertEqual(runtime.ask(doc.document_id,"Is rotor active?").status,"CONFLICTING_DOCUMENT_CONTENT")
    def test_large_document_context_is_bounded(self)->None:
        (self.root/"large.txt").write_text("\n".join(f"rotor detail {i} "+"x"*100 for i in range(200)),encoding="utf-8"); runtime=DocumentIntelligenceRuntime(self.root,max_context_chars=500); doc=runtime.ingest("large.txt")
        self.assertLessEqual(runtime.ask(doc.document_id,"rotor detail").context_chars,500)


if __name__=="__main__":unittest.main()
