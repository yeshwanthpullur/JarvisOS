"""Governance-wrapped optional Mem0 and Graphiti metadata adapters."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
import importlib.util

from .runtime import GovernedMemoryRecord, GovernedMemoryStore, GovernedMemoryStatus, MemoryScope


class Mem0Adapter:
    def __init__(self,store:GovernedMemoryStore,client:object|None=None)->None:self.store=store;self.client=client
    def detect(self)->dict[str,object]:
        installed=importlib.util.find_spec("mem0") is not None;return {"backend":"mem0","installed":installed,"state":"ready" if self.client else "degraded" if installed else "unavailable","authority":"jarvis_memory_governance"}
    def health(self)->dict[str,object]:return self.detect()
    def add(self,*args,**kwargs)->GovernedMemoryRecord:return self.store.create(*args,**kwargs)
    def search(self,*args,**kwargs)->tuple[GovernedMemoryRecord,...]:return self.store.search(*args,**kwargs)
    def update(self,*args,**kwargs)->GovernedMemoryRecord:return self.store.update(*args,**kwargs)
    def delete(self,*args,**kwargs)->bool:return self.store.delete(*args,**kwargs)
    def list(self,scope:MemoryScope|str)->tuple[GovernedMemoryRecord,...]:return tuple(item for item in self.store.records.values() if item.scope is MemoryScope(scope))
    def capabilities(self)->tuple[str,...]:return ("add","search","update","delete","list","governance_wrapped")


@dataclass(frozen=True,slots=True)
class TemporalFact:
    fact_id:str;subject:str;relation:str;object_value:str;valid_from:str;valid_to:str|None;observed_at:str;source:str;confidence:float;status:str="current";supersedes:str="";superseded_by:str=""


class GraphitiAdapter:
    def __init__(self,client:object|None=None)->None:self.client=client;self.facts:dict[str,TemporalFact]={}
    def detect(self)->dict[str,object]:
        installed=importlib.util.find_spec("graphiti_core") is not None;return {"backend":"graphiti","installed":installed,"state":"ready" if self.client else "degraded" if installed else "unavailable","fallback":"local_temporal_metadata"}
    def add(self,fact:TemporalFact)->TemporalFact:
        if fact.fact_id in self.facts:raise ValueError("duplicate_temporal_fact")
        self.facts[fact.fact_id]=fact;return fact
    def supersede(self,old_id:str,new_fact:TemporalFact)->TemporalFact:
        old=self.facts.get(old_id)
        if not old:raise ValueError("temporal_fact_not_found")
        if old.subject!=new_fact.subject or old.relation!=new_fact.relation:raise ValueError("temporal_relationship_mismatch")
        current=replace(new_fact,supersedes=old_id);self.facts[current.fact_id]=current;self.facts[old_id]=replace(old,valid_to=current.valid_from,status="superseded",superseded_by=current.fact_id);return current
    def current(self,subject:str,relation:str)->tuple[TemporalFact,...]:return tuple(item for item in self.facts.values() if item.subject==subject and item.relation==relation and item.status=="current")
    def traverse(self,subject:str)->tuple[TemporalFact,...]:return tuple(item for item in self.facts.values() if item.subject==subject or item.object_value==subject)
