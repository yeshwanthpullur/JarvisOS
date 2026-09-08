"""Versioned local embeddings and deterministic reranking."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import re


TOK=re.compile(r"[a-z0-9_+-]+",re.I)
@dataclass(frozen=True,slots=True)
class EmbeddingMetadata: model_id:str; provider:str; dimension:int; local:bool; privacy_class:str; version:str; healthy:bool; available:bool
@dataclass(frozen=True,slots=True)
class EmbeddedText: text_hash:str; vector:tuple[float,...]; metadata:EmbeddingMetadata


class DeterministicEmbeddingProvider:
    def __init__(self,model_id:str="jarvis-hash-embedding",version:str="1",dimension:int=32,*,local:bool=True,available:bool=True,max_batch:int=32)->None:
        self.metadata=EmbeddingMetadata(model_id,"builtin_local",dimension,local,"local_only" if local else "external",version,available,available);self.max_batch=max(1,min(max_batch,128))
    @property
    def ready(self)->bool:return self.metadata.available and self.metadata.healthy
    @property
    def provider_id(self)->str:return self.metadata.provider
    @property
    def dimension(self)->int:return self.metadata.dimension
    def embed(self,text:str)->tuple[float,...]:
        values=[0.0]*self.dimension
        for token in TOK.findall(text.lower()):
            digest=hashlib.sha256(token.encode()).digest(); index=int.from_bytes(digest[:4],"big")%self.dimension; values[index]+=1 if digest[4]%2 else -1
        length=math.sqrt(sum(v*v for v in values)); return tuple(v/length for v in values) if length else tuple(values)
    def embed_batch(self,texts:tuple[str,...],*,privacy_mode:str="local_only")->tuple[EmbeddedText,...]:
        if len(texts)>self.max_batch: raise ValueError("embedding_batch_too_large")
        if privacy_mode=="local_only" and not self.metadata.local: raise ValueError("cloud_embedding_denied")
        return tuple(EmbeddedText(hashlib.sha256(text.encode()).hexdigest(),self.embed(text),self.metadata) for text in texts)


class DeterministicReranker:
    def __init__(self,available:bool=True)->None:self.available=available
    def rerank(self,query:str,candidates:tuple[tuple[str,str,float],...])->tuple[tuple[str,float],...]:
        if not self.available:return tuple((identifier,base) for identifier,_,base in candidates)
        terms=set(TOK.findall(query.lower())); output=[]
        for identifier,text,base in candidates:
            overlap=len(terms&set(TOK.findall(text.lower())))/max(1,len(terms));output.append((identifier,min(1,base*.25+overlap*.75)))
        return tuple(sorted(output,key=lambda item:(-item[1],item[0])))
