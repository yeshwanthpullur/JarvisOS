"""Local-first OCR contracts, adapters, and bounded routing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import importlib.util
from typing import Callable
from uuid import uuid4


class OCRState(StrEnum): READY="ready"; DEGRADED="degraded"; UNCONFIGURED="unconfigured"; UNAVAILABLE="unavailable"; BLOCKED="blocked"; FAILED="failed"
@dataclass(frozen=True, slots=True)
class OCRBoundingBox: x: float; y: float; width: float; height: float
@dataclass(frozen=True, slots=True)
class OCRToken: text: str; confidence: float | None = None; box: OCRBoundingBox | None = None
@dataclass(frozen=True, slots=True)
class OCRLine: line_id: str; text: str; tokens: tuple[OCRToken,...]=(); confidence: float|None=None; box: OCRBoundingBox|None=None
@dataclass(frozen=True, slots=True)
class OCRBlock: block_id: str; lines: tuple[OCRLine,...]; page_number:int|None=None; confidence:float|None=None
@dataclass(frozen=True, slots=True)
class OCRRequest:
    source_ref:str; media_type:str; data:bytes; page_number:int|None=None; language:str|None=None; privacy_mode:str="local_only"; classification:str="normal"; max_chars:int=20000
    def __post_init__(self) -> None:
        if not self.data or len(self.data)>20_000_000: raise ValueError("invalid_ocr_input")
        if self.media_type not in {"image/png","image/jpeg","image/tiff","application/pdf"}: raise ValueError("invalid_ocr_input")
        signatures={"image/png":self.data.startswith(b"\x89PNG\r\n\x1a\n"),"image/jpeg":self.data.startswith(b"\xff\xd8"),"image/tiff":self.data.startswith((b"II*\x00",b"MM\x00*")),"application/pdf":self.data.startswith(b"%PDF")}
        if not signatures[self.media_type]: raise ValueError("invalid_ocr_input")
@dataclass(frozen=True, slots=True)
class OCRResult:
    request_id:str; status:OCRState; backend:str; source_ref:str; page_number:int|None; blocks:tuple[OCRBlock,...]=(); text:str=""; language:str|None=None; confidence:float|None=None; cloud_used:bool=False; warnings:tuple[str,...]=(); error:str=""


Recognizer=Callable[[bytes,str|None],tuple[dict[str,object],...]]
class OCRAdapter:
    def __init__(self, backend_id:str, *, local:bool, configured:bool, installed:bool, recognizer:Recognizer|None=None, credential_reference:str="") -> None:
        if credential_reference and not credential_reference.endswith("_ENV"): raise ValueError("credential_reference_must_be_symbolic")
        self.backend_id=backend_id; self.local=local; self.configured=configured; self.installed=installed; self.recognizer=recognizer; self.credential_reference=credential_reference
    def detect(self)->dict[str,object]:
        ready=self.installed and self.configured and self.recognizer is not None
        return {"backend":self.backend_id,"local":self.local,"installed":self.installed,"configured":self.configured,"state":"ready" if ready else "unconfigured" if self.installed and not self.configured else "degraded" if self.installed else "unavailable","credential_reference":self.credential_reference}
    def health(self)->dict[str,object]: return self.detect()
    def capabilities(self)->tuple[str,...]: return ("recognize","recognize_regions")
    def recognize(self, request:OCRRequest)->OCRResult:
        if not self.local and request.privacy_mode=="local_only": return OCRResult(str(uuid4()),OCRState.BLOCKED,self.backend_id,request.source_ref,request.page_number,error="cloud_ocr_denied")
        if not self.local and request.classification in {"private","sensitive","secret"}: return OCRResult(str(uuid4()),OCRState.BLOCKED,self.backend_id,request.source_ref,request.page_number,error="private_document_cloud_ocr_denied")
        if self.recognizer is None or not self.configured: return OCRResult(str(uuid4()),OCRState.UNAVAILABLE,self.backend_id,request.source_ref,request.page_number,error="ocr_unavailable")
        try: raw=self.recognizer(request.data,request.language)
        except Exception: return OCRResult(str(uuid4()),OCRState.FAILED,self.backend_id,request.source_ref,request.page_number,error="ocr_failed")
        lines=[]
        for index,item in enumerate(raw[:500]):
            confidence=item.get("confidence"); box=item.get("box"); box=OCRBoundingBox(*box) if box is not None else None
            lines.append(OCRLine(f"line-{index}",str(item.get("text",""))[:1000],confidence=confidence,box=box))
        values=[item.confidence for item in lines if item.confidence is not None]; confidence=sum(values)/len(values) if values else None
        text="\n".join(item.text for item in lines)[:request.max_chars]
        warnings=("low_confidence",) if confidence is not None and confidence<.5 else ()
        block=OCRBlock("block-1",tuple(lines),request.page_number,confidence)
        return OCRResult(str(uuid4()),OCRState.READY,self.backend_id,request.source_ref,request.page_number,(block,),text,request.language,confidence,not self.local,warnings)


class PaddleOCRAdapter(OCRAdapter):
    def __init__(self, recognizer:Recognizer|None=None)->None: super().__init__("paddleocr",local=True,configured=True,installed=recognizer is not None or importlib.util.find_spec("paddleocr") is not None,recognizer=recognizer)
class CloudOCRAdapter(OCRAdapter):
    def __init__(self, provider_id:str="baidu_ocr",*,configured:bool=False,recognizer:Recognizer|None=None,credential_reference:str="BAIDU_OCR_CREDENTIAL_ENV")->None: super().__init__(provider_id,local=False,configured=configured,installed=True,recognizer=recognizer,credential_reference=credential_reference)


class OCRRouter:
    def __init__(self, local_adapters:tuple[OCRAdapter,...], cloud_adapters:tuple[OCRAdapter,...]=(), max_fallbacks:int=1)->None: self.local=local_adapters; self.cloud=cloud_adapters; self.max_fallbacks=max(0,min(max_fallbacks,2))
    def route(self,request:OCRRequest)->OCRResult:
        attempts=0; last=None
        for adapter in self.local+self.cloud:
            if attempts>self.max_fallbacks: break
            result=adapter.recognize(request); attempts+=1; last=result
            if result.status is OCRState.READY: return result
            if result.status is OCRState.BLOCKED: continue
        return last or OCRResult(str(uuid4()),OCRState.UNAVAILABLE,"none",request.source_ref,request.page_number,error="ocr_unavailable")
    def status(self)->dict[str,object]: return {"local":[item.detect() for item in self.local],"cloud":[item.detect() for item in self.cloud],"max_fallbacks":self.max_fallbacks,"local_preferred":True}
