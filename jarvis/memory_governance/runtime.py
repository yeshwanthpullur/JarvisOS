"""Explicit-scope local memory with tombstones and least-context retrieval."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
import hashlib
import json
from pathlib import Path
import re
from uuid import uuid4

from jarvis.knowledge.vector import LocalVectorStore, VectorRecord


SECRET=re.compile(r"(?i)(api[_-]?key|access[_-]?token|password|secret|credential|authorization)\s*[:=]\s*\S+")
TOK=re.compile(r"[a-z0-9_+-]+",re.I)
class MemoryScope(StrEnum): SESSION="session";PROJECT="project";KNOWLEDGE="knowledge";PERSONAL="personal"
class GovernedMemoryStatus(StrEnum): ACTIVE="active";STALE="stale";SUPERSEDED="superseded";EXPIRED="expired";DELETED="deleted";CONFLICTING="conflicting";NEEDS_REVIEW="needs_review"
class MemoryOrigin(StrEnum): EXPLICIT="explicit";INFERRED="inferred"


@dataclass(frozen=True,slots=True)
class GovernedMemoryRecord:
    memory_id:str;memory_type:str;subject:str;content:str;source:str;scope:MemoryScope;status:GovernedMemoryStatus;origin:MemoryOrigin;privacy_class:str;confidence:float;provenance:str;content_hash:str;created_at:str;updated_at:str;last_used:str="";expiry:str="";project_id:str="";session_id:str="";supersedes:str="";superseded_by:str="";version:int=1;instruction_like:bool=False
    def __post_init__(self)->None:
        if not self.subject or not self.provenance or not 0<=self.confidence<=1:raise ValueError("invalid_governed_memory")
        if self.scope is MemoryScope.PROJECT and not self.project_id:raise ValueError("project_scope_requires_project_id")
        if self.scope is MemoryScope.SESSION and not self.session_id:raise ValueError("session_scope_requires_session_id")


class GovernedMemoryStore:
    SCHEMA=1
    def __init__(self,path:Path|None=None,*,vector_store:LocalVectorStore|None=None,max_records:int=2000)->None:
        self.path=path;self.vector_store=vector_store;self.max_records=max(1,min(max_records,10000));self.records:dict[str,GovernedMemoryRecord]={};self.history:list[tuple[str,str,str]]=[]
        if path and path.exists():self._load()
    @staticmethod
    def _now()->str:return datetime.now(UTC).isoformat()
    def create(self,subject:str,content:str,*,scope:MemoryScope|str|None,source:str,provenance:str,explicit:bool,project_id:str="",session_id:str="",memory_type:str="context",privacy_class:str="normal",confidence:float=.7,expiry:str="",authority:bool=False)->GovernedMemoryRecord:
        if not authority:raise PermissionError("memory_authority_required")
        if scope is None:raise ValueError("memory_scope_required")
        scope=MemoryScope(scope);value=" ".join(content.split())
        if not value or SECRET.search(" ".join((subject,value,source,provenance))):raise ValueError("unsafe_memory_content")
        digest=hashlib.sha256(value.encode()).hexdigest()
        duplicate=next((item for item in self.records.values() if item.scope is scope and item.project_id==project_id and item.session_id==session_id and item.content_hash==digest and item.status in {GovernedMemoryStatus.ACTIVE,GovernedMemoryStatus.NEEDS_REVIEW}),None)
        if duplicate:return duplicate
        if len(self.records)>=self.max_records:raise ValueError("memory_record_limit")
        now=self._now();origin=MemoryOrigin.EXPLICIT if explicit else MemoryOrigin.INFERRED;status=GovernedMemoryStatus.ACTIVE if explicit else GovernedMemoryStatus.NEEDS_REVIEW
        conflict=next((item for item in self.records.values() if item.scope is scope and item.subject.lower()==subject.lower() and item.project_id==project_id and item.status is GovernedMemoryStatus.ACTIVE and item.content_hash!=digest),None)
        if conflict:status=GovernedMemoryStatus.CONFLICTING
        item=GovernedMemoryRecord(f"memory-{uuid4().hex[:12]}",memory_type,subject[:200],value[:4000],source[:120],scope,status,origin,privacy_class[:40],confidence,provenance[:240],digest,now,now,expiry=expiry,project_id=project_id[:80],session_id=session_id[:80],instruction_like=bool(re.search(r"(?i)(ignore .*instructions|execute .*command|reveal .*secret)",value)))
        self.records[item.memory_id]=item;self._index(item);self._audit("create",item.memory_id);self._flush();return item
    def update(self,memory_id:str,content:str,*,provenance:str,authority:bool=False)->GovernedMemoryRecord:
        current=self._active(memory_id);return self.supersede(memory_id,content,provenance=provenance,authority=authority,operation="update")
    def supersede(self,memory_id:str,content:str,*,provenance:str,authority:bool=False,operation:str="supersede")->GovernedMemoryRecord:
        if not authority:raise PermissionError("memory_authority_required")
        current=self._active(memory_id)
        if hashlib.sha256(" ".join(content.split()).encode()).hexdigest()==current.content_hash:return current
        replacement=self.create(current.subject,content,scope=current.scope,source=current.source,provenance=provenance,explicit=True,project_id=current.project_id,session_id=current.session_id,memory_type=current.memory_type,privacy_class=current.privacy_class,confidence=current.confidence,expiry=current.expiry,authority=True)
        replacement=replace(replacement,supersedes=current.memory_id,version=current.version+1);self.records[replacement.memory_id]=replacement
        self.records[current.memory_id]=replace(current,status=GovernedMemoryStatus.SUPERSEDED,superseded_by=replacement.memory_id,updated_at=self._now());self._deindex(current.memory_id);self._index(replacement);self._audit(operation,replacement.memory_id);self._flush();return replacement
    def delete(self,memory_id:str,*,authority:bool=False)->bool:
        if not authority:raise PermissionError("memory_authority_required")
        current=self.records.get(memory_id)
        if not current:return False
        self.records[memory_id]=replace(current,content="[deleted]",status=GovernedMemoryStatus.DELETED,updated_at=self._now());self._deindex(memory_id);self._audit("delete",memory_id);self._flush();return True
    def expire(self,current_time:datetime|None=None,*,authority:bool=False)->tuple[str,...]:
        if not authority:raise PermissionError("memory_authority_required")
        now=current_time or datetime.now(UTC);expired=[]
        for key,item in tuple(self.records.items()):
            if item.status not in {GovernedMemoryStatus.ACTIVE,GovernedMemoryStatus.NEEDS_REVIEW} or not item.expiry:continue
            try:due=datetime.fromisoformat(item.expiry)
            except ValueError:continue
            if due<=now:self.records[key]=replace(item,status=GovernedMemoryStatus.EXPIRED,updated_at=self._now());self._deindex(key);expired.append(key)
        if expired:self._audit("expire",str(len(expired)));self._flush()
        return tuple(expired)
    def restore(self,memory_id:str,*,authority:bool=False)->bool:
        if not authority:raise PermissionError("memory_authority_required")
        item=self.records.get(memory_id)
        if not item or item.status is not GovernedMemoryStatus.EXPIRED:return False
        self.records[memory_id]=replace(item,status=GovernedMemoryStatus.ACTIVE,expiry="",updated_at=self._now());self._index(self.records[memory_id]);self._audit("restore",memory_id);self._flush();return True
    def mark_stale(self,memory_id:str,*,authority:bool=False)->bool:
        if not authority:raise PermissionError("memory_authority_required")
        item=self._active(memory_id);self.records[memory_id]=replace(item,status=GovernedMemoryStatus.STALE,updated_at=self._now());self._deindex(memory_id);self._audit("stale",memory_id);self._flush();return True
    def search(self,query:str,*,scope:MemoryScope|str|None,requesting_agent:str,project_id:str="",session_id:str="",allow_cross_scope:bool=False,personal_allowed:bool=False,limit:int=8,max_chars:int=3000)->tuple[GovernedMemoryRecord,...]:
        if scope is None:raise ValueError("memory_scope_required")
        scope=MemoryScope(scope)
        if allow_cross_scope and requesting_agent not in {"executive_jarvis","memory_agent"}:raise PermissionError("cross_scope_memory_denied")
        if scope is MemoryScope.PERSONAL and (not personal_allowed or requesting_agent not in {"executive_jarvis","memory_agent"}):raise PermissionError("personal_memory_denied")
        terms=set(TOK.findall(query.lower()));ranked=[]
        for item in self.records.values():
            if item.status is not GovernedMemoryStatus.ACTIVE or item.scope is not scope:continue
            if scope is MemoryScope.PROJECT and item.project_id!=project_id:continue
            if scope is MemoryScope.SESSION and item.session_id!=session_id:continue
            score=len(terms & set(TOK.findall((item.subject+" "+item.content).lower()))) / max(1,len(terms))
            if score:ranked.append((score,item))
        output=[];chars=0
        for _,item in sorted(ranked,key=lambda pair:(-pair[0],pair[1].memory_id)):
            if chars+len(item.content)>max_chars:continue
            output.append(item);chars+=len(item.content)
            if len(output)>=min(limit,20):break
        return tuple(output)
    def context(self,query:str,requests:tuple[tuple[MemoryScope,str,str],...],*,requesting_agent:str,max_chars:int=3000)->tuple[GovernedMemoryRecord,...]:
        output=[];seen=set();chars=0
        for scope,project_id,session_id in requests:
            for item in self.search(query,scope=scope,requesting_agent=requesting_agent,project_id=project_id,session_id=session_id,personal_allowed=requesting_agent in {"executive_jarvis","memory_agent"}):
                if item.memory_id in seen or chars+len(item.content)>max_chars:continue
                output.append(item);seen.add(item.memory_id);chars+=len(item.content)
        return tuple(output)
    def inspect(self,memory_id:str)->dict[str,object]:
        item=self.records.get(memory_id)
        if not item:return {"status":"not_found"}
        return {"memory_id":item.memory_id,"scope":item.scope.value,"status":item.status.value,"origin":item.origin.value,"privacy":item.privacy_class,"version":item.version,"provenance":item.provenance,"content_available":item.status is not GovernedMemoryStatus.DELETED}
    def _active(self,memory_id:str)->GovernedMemoryRecord:
        item=self.records.get(memory_id)
        if not item or item.status not in {GovernedMemoryStatus.ACTIVE,GovernedMemoryStatus.NEEDS_REVIEW,GovernedMemoryStatus.CONFLICTING}:raise ValueError("memory_not_active")
        return item
    def _index(self,item:GovernedMemoryRecord)->None:
        if not self.vector_store or self.vector_store.detect()["state"]!="ready" or item.status is not GovernedMemoryStatus.ACTIVE:return
        vector=tuple((byte-127.5)/127.5 for byte in hashlib.sha256(item.content.encode()).digest()[:16]);self.vector_store.create_collection("jarvis_memory")
        self.vector_store.upsert("jarvis_memory",VectorRecord(item.memory_id,item.scope.value,vector,(("scope",item.scope.value),("project_id",item.project_id),("privacy",item.privacy_class)),"memory-hash","1",16,item.content_hash))
    def _deindex(self,memory_id:str)->None:
        if self.vector_store:self.vector_store.delete("jarvis_memory",memory_id)
    def _audit(self,operation:str,reference:str)->None:self.history=(self.history+[(self._now(),operation,reference)])[-200:]
    def _flush(self)->None:
        if not self.path:return
        self.path.parent.mkdir(parents=True,exist_ok=True);temp=self.path.with_suffix(".tmp");temp.write_text(json.dumps({"schema":self.SCHEMA,"records":[asdict(item) for item in self.records.values()],"history":self.history},sort_keys=True),encoding="utf-8");temp.replace(self.path)
    def _load(self)->None:
        try:
            raw=json.loads(self.path.read_text(encoding="utf-8"));assert raw["schema"]==self.SCHEMA
            for item in raw["records"]:record=GovernedMemoryRecord(**{**item,"scope":MemoryScope(item["scope"]),"status":GovernedMemoryStatus(item["status"]),"origin":MemoryOrigin(item["origin"])});self.records[record.memory_id]=record
            self.history=[tuple(item) for item in raw.get("history",())][-200:]
        except (OSError,ValueError,TypeError,KeyError,AssertionError) as exc:raise ValueError("invalid_memory_store") from exc
    def status(self)->dict[str,object]:
        return {"authority":"memory_intelligence","records":len(self.records),"scopes":{scope.value:sum(item.scope is scope and item.status is GovernedMemoryStatus.ACTIVE for item in self.records.values()) for scope in MemoryScope},"stale":sum(item.status is GovernedMemoryStatus.STALE for item in self.records.values()),"expired":sum(item.status is GovernedMemoryStatus.EXPIRED for item in self.records.values()),"conflicting":sum(item.status is GovernedMemoryStatus.CONFLICTING for item in self.records.values()),"deleted":sum(item.status is GovernedMemoryStatus.DELETED for item in self.records.values()),"automatic_conversation_write":False,"worker_direct_access":False}
