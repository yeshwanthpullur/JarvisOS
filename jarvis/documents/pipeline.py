"""Canonical ingestion, parser/OCR routing, and bounded document-local QA."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import re
from typing import Mapping

from .canonical import BlockType, CanonicalDocument, DocumentBlock, DocumentPage, DocumentProvenance, block
from .ocr import CloudOCRAdapter, OCRRequest, OCRRouter, OCRState, PaddleOCRAdapter
from .parsers import BuiltinDocumentParser, DoclingAdapter, MarkerAdapter, ParserRegistry


MEDIA_TYPES={".txt":"text/plain",".md":"text/markdown",".json":"application/json",".csv":"text/csv",".pdf":"application/pdf",".docx":"application/vnd.openxmlformats-officedocument.wordprocessingml.document",".pptx":"application/vnd.openxmlformats-officedocument.presentationml.presentation",".png":"image/png",".jpg":"image/jpeg",".jpeg":"image/jpeg",".tif":"image/tiff",".tiff":"image/tiff"}
@dataclass(frozen=True,slots=True)
class DocumentRoute:
    route_id:str; media_type:str; primary_backend:str; fallback_backends:tuple[str,...]; use_ocr:bool; cloud_allowed:bool; reason:str; max_attempts:int=2
@dataclass(frozen=True,slots=True)
class GroundedAnswer:
    status:str; answer:str; evidence_refs:tuple[str,...]; confidence:float; limitations:tuple[str,...]=(); context_chars:int=0


class DocumentRouter:
    def __init__(self, parsers:ParserRegistry, ocr:OCRRouter)->None: self.parsers=parsers; self.ocr=ocr
    def decide(self,media_type:str,*,native_text:bool=True,scanned:bool=False,privacy_mode:str="local_only",previous_failure:str="")->DocumentRoute:
        image=media_type.startswith("image/"); use_ocr=image or scanned or not native_text
        if use_ocr: return DocumentRoute("document-ocr",media_type,"paddleocr",("cloud_ocr",) if privacy_mode!="local_only" else (),True,privacy_mode!="local_only","Image/scanned input requires OCR; local backend is preferred.")
        primary="docling" if media_type in {"application/pdf","application/vnd.openxmlformats-officedocument.wordprocessingml.document","application/vnd.openxmlformats-officedocument.presentationml.presentation"} else "builtin_safe"
        fallback=("marker","builtin_safe") if media_type=="application/pdf" else ("builtin_safe",)
        if previous_failure==primary: primary,fallback=fallback[0],fallback[1:]
        return DocumentRoute("document-native",media_type,primary,fallback,False,False,"Native text avoids unnecessary OCR.")


class DocumentIntelligenceRuntime:
    def __init__(self,root:Path,*,max_file_bytes:int=10_000_000,max_extract_chars:int=100_000,max_context_chars:int=12_000,docling:DoclingAdapter|None=None,marker:MarkerAdapter|None=None,ocr:OCRRouter|None=None)->None:
        self.root=root.resolve(); self.max_file_bytes=max_file_bytes; self.max_extract_chars=max_extract_chars; self.max_context_chars=max_context_chars
        self.parsers=ParserRegistry((docling or DoclingAdapter(),marker or MarkerAdapter(),BuiltinDocumentParser()))
        self.ocr=ocr or OCRRouter((PaddleOCRAdapter(),),(CloudOCRAdapter(),),1); self.router=DocumentRouter(self.parsers,self.ocr); self.documents:dict[str,CanonicalDocument]={}; self.routes:dict[str,DocumentRoute]={}
    def ingest(self,value:str,*,privacy_mode:str="local_only",scanned:bool=False)->CanonicalDocument:
        path=Path(value); path=path if path.is_absolute() else self.root/path
        try: resolved=path.resolve(strict=True)
        except (OSError,RuntimeError) as exc: raise ValueError("document_not_found") from exc
        if not resolved.is_file(): raise ValueError("document_not_found")
        size=resolved.stat().st_size
        if size==0: raise ValueError("document_empty")
        if size>self.max_file_bytes: raise ValueError("document_too_large")
        media=MEDIA_TYPES.get(resolved.suffix.lower())
        if not media: raise ValueError("unsupported_document_type")
        data=resolved.read_bytes(); document=CanonicalDocument.create(resolved.name,media,data,raw_reference=resolved.name)
        route=self.router.decide(media,native_text=not scanned,scanned=scanned,privacy_mode=privacy_mode); self.routes[document.document_id]=route
        if route.use_ocr:
            result=self.ocr.route(OCRRequest(resolved.name,media,data,1,privacy_mode=privacy_mode))
            if result.status is not OCRState.READY: raise ValueError(result.error or "ocr_failed")
            blocks=tuple(block(BlockType.OCR_TEXT,line.text,index,page=result.page_number,backend=result.backend) for index,line in enumerate(result.blocks[0].lines))
            document=replace(document,pages=(DocumentPage(1,tuple(item.block_id for item in blocks),native_text=False),),blocks=blocks,metadata=replace(document.metadata,scanned=True),provenance=(DocumentProvenance(document.source.source_id,result.backend,confidence=result.confidence),))
        else:
            errors=[]; parsed=None
            for parser_id in (route.primary_backend,)+route.fallback_backends:
                parser=self.parsers.get(parser_id)
                if not parser or not parser.supports(media): continue
                try: parsed=parser.parse(document,data,max_chars=self.max_extract_chars); break
                except ValueError as exc: errors.append(f"{parser_id}:{exc}")
            if parsed is None: raise ValueError("parser_failed:"+";".join(errors[:2]))
            document=parsed
        self.documents[document.document_id]=document; return document
    def status(self)->dict[str,object]: return {"status":"ready_foundation","parsers":self.parsers.status(),"ocr":self.ocr.status(),"documents":len(self.documents),"cloud_ocr_default":False}
    def summarize(self,document_id:str,mode:str="concise")->GroundedAnswer:
        document=self.documents.get(document_id)
        if not document: return GroundedAnswer("NOT_FOUND_IN_DOCUMENT","Document not found.",(),0)
        blocks=document.blocks[:5 if mode=="concise" else 20]; answer=" | ".join(item.text for item in blocks)[:self.max_context_chars]
        refs=tuple(f"{document.document_id}:{item.location_ref or item.block_id}" for item in blocks)
        return GroundedAnswer("SUPPORTED_BY_DOCUMENT",answer or "No text found.",refs,.8 if blocks else 0,("Extractive summary preserves source terminology.",),len(answer))
    def ask(self,document_id:str,question:str)->GroundedAnswer:
        document=self.documents.get(document_id)
        if not document: return GroundedAnswer("NOT_FOUND_IN_DOCUMENT","Document not found.",(),0)
        terms={word for word in re.findall(r"[a-z0-9]+",question.lower()) if len(word)>2}
        scored=[]
        for item in document.blocks:
            score=sum(term in item.text.lower() for term in terms)
            if score: scored.append((score,item))
        scored.sort(key=lambda pair:(-pair[0],pair[1].order)); selected=[]; chars=0
        for _,item in scored:
            if chars+len(item.text)>self.max_context_chars: continue
            selected.append(item); chars+=len(item.text)
            if len(selected)>=8: break
        if not selected: return GroundedAnswer("NOT_FOUND_IN_DOCUMENT","Insufficient evidence in the document.",(),0,("No external world knowledge was used.",))
        normalized={item.text.strip().lower() for item in selected}; conflict=len(normalized)>1 and any(token in " ".join(normalized) for token in ("not ","however","contrary"))
        status="CONFLICTING_DOCUMENT_CONTENT" if conflict else "SUPPORTED_BY_DOCUMENT"
        answer=" | ".join(item.text for item in selected)[:self.max_context_chars]; refs=tuple(f"{document.document_id}:{item.location_ref or item.block_id}" for item in selected)
        return GroundedAnswer(status,answer,refs,.7 if not conflict else .45,("Conflicting passages preserved." if conflict else "Document-local evidence only.",),chars)
