"""Canonical document/research ingestion and provenance-aware retrieval."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path

from jarvis.documents import CanonicalDocument
from jarvis.research import ResearchSource as ExternalSource, EvidenceChunk
from jarvis.workers.assurance import evidence_integrity
from jarvis.workers.assurance_models import EvidenceRecord, EvidenceType
from .embeddings import DeterministicEmbeddingProvider, DeterministicReranker
from .runtime import AccessScope, EmbeddingState, InMemoryKnowledgeIndex, IngestionMode, KnowledgeChunk, KnowledgeRecord, KnowledgeSource, RetrievalRequest, SourceType
from .vector import LocalVectorStore, VectorRecord, VectorStoreRouter


@dataclass(frozen=True,slots=True)
class GroundingFragment:
    chunk_id:str; source_id:str; source_type:str; document_id:str; document_version:str; page:int|None; section:str; block:str; text:str; retrieval_score:float; rerank_score:float|None; backend:str; embedding_model:str; embedding_version:str; trust:str; freshness:str; retrieved_at:str; stale:bool=False; conflicting:bool=False
@dataclass(frozen=True,slots=True)
class GroundingContext:
    query:str;fragments:tuple[GroundingFragment,...];total_chars:int;state:str;citations:tuple[str,...]


class RAGRuntime:
    SCHEMA=1
    def __init__(self,index:InMemoryKnowledgeIndex|None=None,vector_router:VectorStoreRouter|None=None,embedding:DeterministicEmbeddingProvider|None=None,reranker:DeterministicReranker|None=None,state_path:Path|None=None)->None:
        self.index=index or InMemoryKnowledgeIndex();self.vector_router=vector_router or VectorStoreRouter(());self.embedding=embedding or DeterministicEmbeddingProvider();self.reranker=reranker or DeterministicReranker();self.state_path=state_path;self.chunk_meta:dict[str,dict[str,str]]={};self.invalid_chunks:set[str]=set();self.stale_chunks:set[str]=set();self.conflicting_chunks:set[str]=set()
        if state_path and state_path.exists():self._load()
    def ingest_document(self,document:CanonicalDocument,*,project_id:str="default",persist:bool=True)->tuple[str,...]:
        source_id=document.source.source_id
        if source_id not in self.index.sources:self.index.register(KnowledgeSource(source_id,SourceType.LOCAL_DOCUMENT,document.source.display_name,document.source.raw_reference,trust_class="explicit_document",privacy_class="project",access_scope=AccessScope.PROJECT,ingestion_mode=IngestionMode.MANUAL))
        refs=[]
        for item in document.blocks:
            record=self.index.ingest(source_id,document.metadata.title or document.source.display_name,item.text,privacy_class="project",source_version=document.version_id)
            chunk=next(chunk for chunk in self.index.chunks.values() if chunk.record_id==record.record_id)
            self.chunk_meta[chunk.chunk_id]={"document_id":document.document_id,"document_version":document.version_id,"page":str(item.page_number or ""),"section":item.parent_ref,"block":item.block_id,"parser":item.backend,"project_id":project_id,"source_id":source_id}
            refs.append(chunk.chunk_id)
        self._upsert(refs,namespace=f"project:{project_id}");
        if persist:self.persist()
        return tuple(refs)
    def ingest_research(self,source:ExternalSource,evidence:tuple[EvidenceChunk,...],*,retain:bool=False)->tuple[str,...]:
        if not retain:return ()
        if source.source_id not in self.index.sources:self.index.register(KnowledgeSource(source.source_id,SourceType.RESEARCH_SOURCE,source.title,source.normalized_url,trust_class=source.trust_class,privacy_class="public",ingestion_mode=IngestionMode.MANUAL))
        refs=[]
        for item in evidence:
            if item.source_id!=source.source_id:continue
            record=self.index.ingest(source.source_id,source.title,item.text_or_summary,freshness=source.freshness)
            chunk=next(chunk for chunk in self.index.chunks.values() if chunk.record_id==record.record_id);self.chunk_meta[chunk.chunk_id]={"document_id":"","document_version":"","page":"","section":"","block":item.location_ref,"parser":"research","project_id":"","source_id":source.source_id};refs.append(chunk.chunk_id)
        self._upsert(refs,namespace="knowledge:public");self.persist();return tuple(refs)
    def _upsert(self,refs:list[str],namespace:str)->None:
        store=self.vector_router.select(persistence=False,metadata_filtering=False)
        if not store:return
        store.create_collection("jarvis_knowledge")
        for chunk_id in refs:
            chunk=self.index.chunks[chunk_id];vector=self.embedding.embed(chunk.text_or_reference);meta=self.chunk_meta[chunk_id]
            store.upsert("jarvis_knowledge",VectorRecord(chunk_id,namespace,vector,tuple(sorted(meta.items())),self.embedding.metadata.model_id,self.embedding.metadata.version,len(vector),chunk.checksum))
    def retrieve(self,query:str,*,project_id:str="default",top_k:int=5,max_context_chars:int=4000)->GroundingContext:
        lexical=self.index.search(RetrievalRequest(query,privacy_scope=("public","project"),max_results=min(top_k*2,20)))
        scores={result.chunk_id:result.score for result in lexical}
        store=self.vector_router.select(persistence=False,metadata_filtering=False)
        backend="lexical"
        if store:
            try:
                matches=store.search("jarvis_knowledge",self.embedding.embed(query),limit=min(top_k*2,20))
                for match in matches:scores[match.record_id]=max(scores.get(match.record_id,0),max(0,match.score))
                if matches:backend=f"hybrid:{store.backend_id}"
            except ValueError:
                backend="lexical_vector_incompatible"
        candidates=[]
        for chunk_id,score in scores.items():
            if chunk_id in self.invalid_chunks:continue
            chunk=self.index.chunks.get(chunk_id);meta=self.chunk_meta.get(chunk_id)
            if not chunk or not meta:continue
            if meta.get("project_id") not in {"",project_id}:continue
            candidates.append((chunk_id,chunk.text_or_reference,score))
        reranked=dict(self.reranker.rerank(query,tuple(candidates)));fragments=[];total=0
        for chunk_id,text,base in sorted(candidates,key=lambda item:(-reranked.get(item[0],item[2]),item[0])):
            if total+len(text)>max_context_chars:continue
            meta=self.chunk_meta[chunk_id];page=int(meta["page"]) if meta.get("page") else None
            source=self.index.sources.get(meta["source_id"])
            fragments.append(GroundingFragment(chunk_id,meta["source_id"],source.source_type.value if source else "unknown",meta["document_id"],meta["document_version"],page,meta["section"],meta["block"],text,base,reranked.get(chunk_id),backend,self.embedding.metadata.model_id,self.embedding.metadata.version,self.index.chunks[chunk_id].trust_class,self.index.chunks[chunk_id].freshness,datetime.now(UTC).isoformat(),chunk_id in self.stale_chunks,chunk_id in self.conflicting_chunks));total+=len(text)
            if len(fragments)>=top_k:break
        citations=tuple(f"{item.source_id}:{item.document_id or 'source'}:{item.page if item.page else item.block or item.chunk_id}" for item in fragments)
        state="SUPPORTED" if fragments else "UNSUPPORTED"
        if any(item.conflicting for item in fragments):state="CONFLICTING"
        return GroundingContext(query,tuple(fragments),total,state,citations)
    def citation(self,chunk_id:str)->str:
        if chunk_id in self.invalid_chunks or chunk_id in self.stale_chunks or chunk_id not in self.index.chunks or chunk_id not in self.chunk_meta:raise ValueError("invalid_retrieval_citation")
        meta=self.chunk_meta[chunk_id];return f"{meta['source_id']}:{meta['document_id'] or 'source'}:{meta['page'] or meta['block'] or chunk_id}"
    def mark_document_stale(self,document_id:str,current_version:str)->tuple[str,...]:
        stale=tuple(key for key,value in self.chunk_meta.items() if value["document_id"]==document_id and value["document_version"]!=current_version)
        self.stale_chunks.update(stale);self.persist();return stale
    def mark_conflicting(self,*chunk_ids:str)->tuple[str,...]:
        valid=tuple(key for key in chunk_ids if key in self.index.chunks and key not in self.invalid_chunks)
        self.conflicting_chunks.update(valid);self.persist();return valid
    def claim_support(self,claims:tuple[str,...],context:GroundingContext)->dict[str,tuple[str,...]]:
        mapping={}
        for claim in claims[:20]:
            terms={term.lower() for term in claim.split() if len(term)>2}
            refs=tuple(item.chunk_id for item in context.fragments if terms & {term.lower().strip(".,:;()") for term in item.text.split()})
            mapping[claim[:300]]=refs
        return mapping
    def delete_source(self,source_id:str)->bool:
        ids=[key for key,value in self.chunk_meta.items() if value["source_id"]==source_id];self.invalid_chunks.update(ids)
        removed=self.index.remove_source(source_id)
        for store in self.vector_router.stores:
            for item in ids:store.delete("jarvis_knowledge",item)
        self.persist();return removed
    def proof(self,context:GroundingContext)->EvidenceRecord:
        summary=f"Retrieval state={context.state} fragments={len(context.fragments)} citations={len(context.citations)}";reference=f"retrieval:{hashlib.sha256(context.query.encode()).hexdigest()[:12]}"
        return EvidenceRecord("rag-query",reference,EvidenceType.RETRIEVAL_RESULT,"rag_runtime",summary,reference,validated=context.state=="SUPPORTED",integrity=evidence_integrity(summary,reference))
    def persist(self)->None:
        if not self.state_path:return
        payload={"schema":self.SCHEMA,"chunk_meta":self.chunk_meta,"invalid":sorted(self.invalid_chunks),"stale":sorted(self.stale_chunks),"conflicting":sorted(self.conflicting_chunks),"sources":[asdict(item) for item in self.index.sources.values()],"records":[asdict(item) for item in self.index.records.values()],"chunks":[asdict(item) for item in self.index.chunks.values()]}
        self.state_path.parent.mkdir(parents=True,exist_ok=True);temp=self.state_path.with_suffix(".tmp");temp.write_text(json.dumps(payload,sort_keys=True),encoding="utf-8");temp.replace(self.state_path)
    def _load(self)->None:
        try:
            raw=json.loads(self.state_path.read_text(encoding="utf-8"));assert raw["schema"]==self.SCHEMA
            self.chunk_meta={str(k):{str(a):str(b) for a,b in v.items()} for k,v in raw["chunk_meta"].items()};self.invalid_chunks=set(raw["invalid"]);self.stale_chunks=set(raw.get("stale",()));self.conflicting_chunks=set(raw.get("conflicting",()))
            for item in raw.get("sources",()):
                source=KnowledgeSource(**{**item,"source_type":SourceType(item["source_type"]),"access_scope":AccessScope(item["access_scope"]),"ingestion_mode":IngestionMode(item["ingestion_mode"]),"warnings":tuple(item.get("warnings",())),"limitations":tuple(item.get("limitations",()))});self.index.sources[source.source_id]=source
            for item in raw.get("records",()):
                record=KnowledgeRecord(**{**item,"metadata":tuple(tuple(pair) for pair in item.get("metadata",())),"warnings":tuple(item.get("warnings",()))});self.index.records[record.record_id]=record
            for item in raw.get("chunks",()):
                chunk=KnowledgeChunk(**{**item,"metadata":tuple(tuple(pair) for pair in item.get("metadata",())),"embedding_state":EmbeddingState(item["embedding_state"])});self.index.chunks[chunk.chunk_id]=chunk
        except (OSError,ValueError,KeyError,TypeError,AssertionError) as exc:raise ValueError("invalid_rag_state") from exc
    def status(self)->dict[str,object]:return {"pipeline":"ready","vector":self.vector_router.status(),"embedding":asdict(self.embedding.metadata),"reranking":"deterministic" if self.reranker.available else "base_ranking","chunks":len(self.chunk_meta),"citations":"provenance_required"}
