"""Lightweight local-first knowledge index with lexical retrieval."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
import hashlib, re
from typing import Protocol
from uuid import uuid4

def now(): return datetime.now(UTC).isoformat()
def norm(v:str)->str: return "\n".join(" ".join(x.split()) for x in v.replace("\r\n","\n").replace("\r","\n").split("\n")).strip()
def checksum(v:str)->str: return hashlib.sha256(v.encode("utf-8")).hexdigest()
TOK=re.compile(r"[a-z0-9_+-]+",re.I)

class SourceType(StrEnum):
 RESEARCH_SOURCE="research_source";PUBLIC_WEB="public_web";DOCUMENTATION="documentation";LOCAL_DOCUMENT="local_document";PROJECT_DOCUMENT="project_document";REPOSITORY="repository";GITHUB="github";MCP_RESOURCE="mcp_resource";PLUGIN_RESOURCE="plugin_resource";PROVIDER_RESOURCE="provider_resource";MANUAL_KNOWLEDGE="manual_knowledge";FUTURE_CONNECTOR="future_connector"
class AccessScope(StrEnum): PUBLIC="public";PROJECT="project";USER_PRIVATE="user_private";RESTRICTED="restricted"
class IngestionMode(StrEnum): MANUAL="manual";ON_DEMAND="on_demand";APPROVED_SYNC="approved_sync";FUTURE_SCHEDULED="future_scheduled"
class EmbeddingState(StrEnum): NOT_REQUIRED="not_required";PENDING="pending";PROVIDER_UNAVAILABLE="provider_unavailable";GENERATED="generated";STALE="stale";ERROR="error"
class RetrievalMode(StrEnum): LEXICAL="lexical";SEMANTIC="semantic";HYBRID="hybrid";AUTO="auto"

@dataclass(slots=True)
class KnowledgeSource:
 source_id:str;source_type:SourceType;display_name:str;origin:str;provider_id:str="native";external_reference:str="";trust_class:str="untrusted_evidence";privacy_class:str="public";access_scope:AccessScope=AccessScope.PUBLIC;ingestion_mode:IngestionMode=IngestionMode.MANUAL;enabled:bool=True;created_at:str=field(default_factory=now);updated_at:str=field(default_factory=now);last_ingested_at:str|None=None;freshness_policy:str="unknown";retention_policy:str="manual";content_state:str="registered";index_state:str="empty";warnings:tuple[str,...]=();limitations:tuple[str,...]=()
 def __post_init__(self):
  if not self.source_id or len(self.display_name)>200 or self.ingestion_mode is IngestionMode.FUTURE_SCHEDULED: raise ValueError("invalid_knowledge_source")
@dataclass(frozen=True,slots=True)
class KnowledgeRecord:
 record_id:str;source_id:str;source_version:str;title:str;content_type:str="text/plain";language:str="unknown";created_at:str=field(default_factory=now);published_at:str|None=None;updated_at:str|None=None;retrieved_at:str|None=None;indexed_at:str=field(default_factory=now);trust_class:str="untrusted_evidence";privacy_class:str="public";freshness:str="unknown";checksum:str="";metadata:tuple[tuple[str,str],...]=();warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class KnowledgeChunk:
 chunk_id:str;record_id:str;source_id:str;ordinal:int;text_or_reference:str;token_or_char_count:int;section:str="";locator:str="";metadata:tuple[tuple[str,str],...]=();embedding_state:EmbeddingState=EmbeddingState.PROVIDER_UNAVAILABLE;trust_class:str="untrusted_evidence";privacy_class:str="public";freshness:str="unknown";checksum:str=""
@dataclass(frozen=True,slots=True)
class RetrievalRequest:
 query:str;source_scope:tuple[str,...]=();privacy_scope:tuple[str,...]=("public","project");trust_requirement:tuple[str,...]=();freshness_requirement:str="any";max_results:int=5;retrieval_mode:RetrievalMode=RetrievalMode.AUTO;filters:tuple[tuple[str,str],...]=();requesting_agent:str="conversation_agent";purpose:str="context"
@dataclass(frozen=True,slots=True)
class RetrievalResult:
 chunk_id:str;source_id:str;record_id:str;score:float;lexical_score:float;semantic_score:float|None;trust_class:str;privacy_class:str;freshness:str;locator:str;provenance:tuple[str,...];warnings:tuple[str,...]=()
@dataclass(frozen=True,slots=True)
class KnowledgeContext:
 query:str;results:tuple[RetrievalResult,...];text_chunks:tuple[str,...];total_chars:int;authoritative:bool=False
@dataclass(frozen=True,slots=True)
class AdmissionPlan:
 eligible:bool;reason:str;source_id:str|None=None;approval_required:bool=True;auto_admit:bool=False

class EmbeddingProvider(Protocol):
 provider_id:str;ready:bool;dimension:int
 def embed(self,text:str)->tuple[float,...]:...

@dataclass
class InMemoryKnowledgeIndex:
 sources:dict[str,KnowledgeSource]=field(default_factory=dict);records:dict[str,KnowledgeRecord]=field(default_factory=dict);chunks:dict[str,KnowledgeChunk]=field(default_factory=dict);embeddings:dict[str,tuple[float,...]]=field(default_factory=dict);embedding_provider:EmbeddingProvider|None=None;max_chunk_chars:int=800;overlap_chars:int=80;max_chunks_per_record:int=50
 def register(self,source:KnowledgeSource):
  if source.source_id in self.sources: raise ValueError("duplicate_knowledge_source")
  self.sources[source.source_id]=source
 def chunk_text(self,text:str)->tuple[str,...]:
  value=norm(text)
  if not value:return ()
  parts=[];start=0
  while start<len(value) and len(parts)<self.max_chunks_per_record:
   end=min(len(value),start+self.max_chunk_chars)
   if end<len(value):
    boundary=value.rfind("\n",start,end)
    if boundary<=start:boundary=value.rfind(" ",start,end)
    if boundary>start+100:end=boundary
   parts.append(value[start:end].strip());start=max(end-self.overlap_chars,end if end==len(value) else 0)
   if end==len(value):break
  return tuple(x for x in parts if x)
 def ingest(self,source_id:str,title:str,text:str,*,privacy_class:str|None=None,freshness:str="unknown",source_version:str="1")->KnowledgeRecord:
  source=self.sources.get(source_id)
  if not source or not source.enabled: raise ValueError("knowledge_source_unavailable")
  value=norm(text)
  if not value or re.search(r"(?i)(api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*\S+",value): raise ValueError("unsafe_knowledge_content")
  digest=checksum(value)
  existing=next((r for r in self.records.values() if r.source_id==source_id and r.checksum==digest),None)
  if existing:return existing
  record=KnowledgeRecord(str(uuid4()),source_id,source_version,title,trust_class=source.trust_class,privacy_class=privacy_class or source.privacy_class,freshness=freshness,checksum=digest)
  self.records[record.record_id]=record
  for i,part in enumerate(self.chunk_text(value)):
   chunk=KnowledgeChunk(str(uuid4()),record.record_id,source_id,i,part,len(part),locator=f"chunk:{i}",trust_class=record.trust_class,privacy_class=record.privacy_class,freshness=freshness,checksum=checksum(part))
   self.chunks[chunk.chunk_id]=chunk
  source.last_ingested_at=now();source.content_state="indexed";source.index_state="ready"
  return record
 def search(self,request:RetrievalRequest)->tuple[RetrievalResult,...]:
  mode=RetrievalMode(request.retrieval_mode);semantic_ready=bool(self.embedding_provider and self.embedding_provider.ready)
  if mode is RetrievalMode.SEMANTIC and not semantic_ready:return ()
  if mode in {RetrievalMode.HYBRID,RetrievalMode.AUTO} and not semantic_ready:mode=RetrievalMode.LEXICAL
  q=set(TOK.findall(request.query.lower()));results=[]
  for c in self.chunks.values():
   s=self.sources.get(c.source_id)
   if not s or not s.enabled or c.privacy_class not in request.privacy_scope:continue
   if request.source_scope and c.source_id not in request.source_scope:continue
   if request.trust_requirement and c.trust_class not in request.trust_requirement:continue
   terms=set(TOK.findall(c.text_or_reference.lower()));lex=len(q&terms)/max(1,len(q));fresh=.05 if c.freshness in {"current","recent"} else 0
   if lex<=0:continue
   results.append(RetrievalResult(c.chunk_id,c.source_id,c.record_id,min(1,lex+fresh),lex,None,c.trust_class,c.privacy_class,c.freshness,c.locator,(c.source_id,c.record_id,c.chunk_id),("relevance_score_not_truth_probability",)))
  results.sort(key=lambda x:(-x.score,x.source_id,x.chunk_id));return tuple(results[:max(1,min(request.max_results,20))])
 def context(self,request:RetrievalRequest,max_chunks:int=5,max_chars:int=4000)->KnowledgeContext:
  selected=[];texts=[];seen=set();total=0
  for r in self.search(request):
   if r.source_id in seen and len(seen)<2:continue
   text=self.chunks[r.chunk_id].text_or_reference
   if total+len(text)>max_chars:continue
   selected.append(r);texts.append(text);seen.add(r.source_id);total+=len(text)
   if len(selected)>=max_chunks:break
  return KnowledgeContext(request.query,tuple(selected),tuple(texts),total,False)
 def remove_source(self,source_id:str):
  if source_id not in self.sources:return False
  self.sources[source_id].enabled=False
  ids={r.record_id for r in self.records.values() if r.source_id==source_id}
  for cid in [k for k,c in self.chunks.items() if c.record_id in ids]:self.chunks.pop(cid,None);self.embeddings.pop(cid,None)
  for rid in ids:self.records.pop(rid,None)
  return True
 def admission_plan(self,candidate)->AdmissionPlan:
  if getattr(candidate,"memory_write_allowed",True):return AdmissionPlan(False,"candidate authority invalid")
  if not getattr(candidate,"provenance_source_ids",()):return AdmissionPlan(False,"provenance required")
  return AdmissionPlan(True,"eligible for explicit controlled indexing",approval_required=True,auto_admit=False)
 def status(self):
  return {"backend":"in_memory","lexical":"ready","semantic":"ready" if self.embedding_provider and self.embedding_provider.ready else "unavailable","hybrid":"ready" if self.embedding_provider and self.embedding_provider.ready else "lexical_fallback","sources":len(self.sources),"records":len(self.records),"chunks":len(self.chunks),"auto_admit_research":False,"direct_memory_writes":False}
