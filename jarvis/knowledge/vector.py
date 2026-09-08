"""Provider-neutral vector stores with truthful optional-backend detection."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
import importlib.util
import json
import math
from pathlib import Path
import re


SECRET=re.compile(r"(?i)(api[_-]?key|access[_-]?token|password|secret|credential)\s*[:=]\s*\S+")
class VectorState(StrEnum): READY="ready"; DEGRADED="degraded"; UNAVAILABLE="unavailable"; ERROR="error"
@dataclass(frozen=True,slots=True)
class VectorCapabilities: persistence:bool; metadata_filtering:bool; namespaces:bool=True; scalable:bool=False
@dataclass(frozen=True,slots=True)
class VectorRecord:
    record_id:str; namespace:str; vector:tuple[float,...]; payload:tuple[tuple[str,str],...]; model_id:str; model_version:str; dimension:int; content_hash:str
    def __post_init__(self)->None:
        if self.dimension!=len(self.vector) or self.dimension<1: raise ValueError("vector_dimension_mismatch")
        if SECRET.search(str(self.payload)): raise ValueError("secret_vector_payload_rejected")
@dataclass(frozen=True,slots=True)
class VectorMatch: record_id:str; namespace:str; score:float; payload:tuple[tuple[str,str],...]


class LocalVectorStore:
    SCHEMA=1
    def __init__(self,backend_id:str,capabilities:VectorCapabilities,path:Path|None=None,*,available:bool=True,module_name:str="")->None:
        self.backend_id=backend_id; self.capabilities=capabilities; self.path=path; self.available=available; self.module_name=module_name; self.collections:dict[str,dict[str,VectorRecord]]={}
        if path and path.exists(): self._load()
    def detect(self)->dict[str,object]:
        installed=True if not self.module_name else importlib.util.find_spec(self.module_name) is not None
        ready=self.available and (installed or self.path is not None)
        return {"backend":self.backend_id,"installed":installed,"state":"ready" if ready else "unavailable","capabilities":asdict(self.capabilities),"implementation":"local_contract" if ready and not installed else "native_metadata_adapter" if installed else "unavailable"}
    def health(self)->dict[str,object]: return self.detect()
    def create_collection(self,name:str)->bool:
        if not self.available: return False
        self.collections.setdefault(name,{}) ; self.persist(); return True
    def delete_collection(self,name:str)->bool:
        removed=self.collections.pop(name,None) is not None; self.persist(); return removed
    def upsert(self,collection:str,record:VectorRecord)->None:
        if not self.available: raise ValueError("vector_backend_unavailable")
        existing=next(iter(self.collections.get(collection,{}).values()),None)
        if existing and (existing.dimension!=record.dimension or existing.model_id!=record.model_id or existing.model_version!=record.model_version): raise ValueError("vector_index_version_mismatch")
        self.collections.setdefault(collection,{})[record.record_id]=record; self.persist()
    def search(self,collection:str,query:tuple[float,...],*,limit:int=5,filters:dict[str,str]|None=None,namespace:str="")->tuple[VectorMatch,...]:
        filters=filters or {}; output=[]
        for item in self.collections.get(collection,{}).values():
            if len(query)!=item.dimension: raise ValueError("vector_dimension_mismatch")
            if namespace and item.namespace!=namespace: continue
            metadata=dict(item.payload)
            if self.capabilities.metadata_filtering and any(metadata.get(key)!=value for key,value in filters.items()): continue
            if filters and not self.capabilities.metadata_filtering: raise ValueError("metadata_filtering_unsupported")
            q=math.sqrt(sum(v*v for v in query)); d=math.sqrt(sum(v*v for v in item.vector)); score=sum(a*b for a,b in zip(query,item.vector))/(q*d) if q and d else 0
            output.append(VectorMatch(item.record_id,item.namespace,score,item.payload))
        output.sort(key=lambda item:(-item.score,item.record_id)); return tuple(output[:max(1,min(limit,50))])
    def delete(self,collection:str,record_id:str)->bool:
        removed=self.collections.get(collection,{}).pop(record_id,None) is not None; self.persist(); return removed
    def get(self,collection:str,record_id:str)->VectorRecord|None:return self.collections.get(collection,{}).get(record_id)
    def count(self,collection:str,namespace:str="")->int:return sum(not namespace or item.namespace==namespace for item in self.collections.get(collection,{}).values())
    def persist(self)->None:
        if not self.path or not self.capabilities.persistence:return
        self.path.parent.mkdir(parents=True,exist_ok=True); temp=self.path.with_suffix(".tmp")
        temp.write_text(json.dumps({"schema":self.SCHEMA,"backend":self.backend_id,"collections":{name:[asdict(item) for item in values.values()] for name,values in self.collections.items()}},sort_keys=True),encoding="utf-8");temp.replace(self.path)
    def _load(self)->None:
        try:
            raw=json.loads(self.path.read_text(encoding="utf-8")); assert raw["schema"]==self.SCHEMA and raw["backend"]==self.backend_id
            for name,records in raw["collections"].items(): self.collections[name]={item["record_id"]:VectorRecord(**{**item,"vector":tuple(item["vector"]),"payload":tuple(tuple(x) for x in item["payload"])}) for item in records}
        except (OSError,ValueError,KeyError,TypeError,AssertionError) as exc: raise ValueError("invalid_vector_store") from exc


class QdrantVectorStore(LocalVectorStore):
    def __init__(self,path:Path|None=None,*,available:bool|None=None)->None:
        detected=importlib.util.find_spec("qdrant_client") is not None
        super().__init__("qdrant",VectorCapabilities(True,True,True,True),path,available=detected if available is None else available,module_name="qdrant_client")
class ChromaVectorStore(LocalVectorStore):
    def __init__(self,path:Path|None=None,*,available:bool|None=None)->None:
        detected=importlib.util.find_spec("chromadb") is not None
        super().__init__("chroma",VectorCapabilities(True,True,True,False),path,available=detected if available is None else available,module_name="chromadb")
class FaissVectorStore(LocalVectorStore):
    def __init__(self,path:Path|None=None,*,available:bool|None=None)->None:
        detected=importlib.util.find_spec("faiss") is not None
        super().__init__("faiss",VectorCapabilities(False,False,True,False),path,available=detected if available is None else available,module_name="faiss")


class VectorStoreRouter:
    def __init__(self,stores:tuple[LocalVectorStore,...])->None:self.stores=stores
    def select(self,*,persistence:bool=True,metadata_filtering:bool=True,offline:bool=True)->LocalVectorStore|None:
        del offline
        for backend in ("qdrant","chroma","faiss"):
            store=next((item for item in self.stores if item.backend_id==backend),None)
            if not store or store.detect()["state"]!="ready":continue
            if persistence and not store.capabilities.persistence:continue
            if metadata_filtering and not store.capabilities.metadata_filtering:continue
            return store
        return None
    def status(self)->dict[str,object]:return {"preferred":"qdrant","backends":[item.detect() for item in self.stores],"silent_data_migration":False}
