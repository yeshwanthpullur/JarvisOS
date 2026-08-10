"""Approved, workspace-scoped text file operations."""
from __future__ import annotations
from dataclasses import dataclass,field
from pathlib import Path
import os, shutil
from jarvis.foundation_common import bounded,new_id,safe_ref
from jarvis.approvals import ApprovalRegistry
from .broker import ExecutionBroker,ToolExecutionRequest
from .models import ExecutionMode,ExecutionPermission,ExecutionRisk
SENSITIVE={".env","id_rsa","id_ed25519"}; SENSITIVE_SUFFIXES={".pem",".key",".pfx",".p12",".db",".sqlite"}
@dataclass(frozen=True,slots=True)
class FileExecutionPolicy:
 allowed_roots:tuple[Path,...];allow_create:bool=True;allow_write:bool=True;allow_append:bool=True;allow_rename:bool=True;allow_move:bool=True;allow_directory_create:bool=True;allow_delete:bool=False;allow_overwrite:bool=False;max_write_chars:int=8000;require_approval:bool=True;block_sensitive_files:bool=True;block_system_paths:bool=True;block_symlink_escape:bool=True
@dataclass(frozen=True,slots=True)
class FilePathValidation:
 target_allowed:bool;within_allowed_root:bool;traversal_detected:bool;symlink_detected:bool;sensitive_file_detected:bool;system_path_detected:bool;overwrite_allowed:bool;blocked_reason:str="";validation_id:str=field(default_factory=new_id)
@dataclass(frozen=True,slots=True)
class FileOperationResult:
 request_id:str;status:str;operation:str;target_summary:str;chars_changed:int=0;rollback_available:bool=False;rollback_id:str="";warnings:tuple[str,...]=();error:str|None=None
class FileExecutor:
 def __init__(self,root:Path,broker:ExecutionBroker):self.root=root.resolve();self.policy=FileExecutionPolicy((self.root,));self.broker=broker;self.history=[];self.rollbacks={}
 def _resolve(self,value):return (self.root/Path(value)).resolve() if not Path(value).is_absolute() else Path(value).resolve()
 def validate_path(self,value,*,overwrite=False):
  raw=str(value);p=self._resolve(value);within=any(p==r or r in p.parents for r in self.policy.allowed_roots);traversal=".." in Path(raw).parts;symlink=any(x.is_symlink() for x in [p,*p.parents] if x.exists());low=p.name.lower();sensitive=low in SENSITIVE or p.suffix.lower() in SENSITIVE_SUFFIXES or any(x.lower() in {".git","models","data"} for x in p.parts) or any(x in low for x in ("secret","credential","token","api_key"));system=any(str(p).lower().startswith(x) for x in ("c:\\windows","c:\\program files","/etc","/usr","/bin"));allowed=within and not traversal and not symlink and not sensitive and not system and (not p.exists() or overwrite or not overwrite)
  reason="outside_allowed_root" if not within else "path_traversal" if traversal else "symlink_escape" if symlink else "sensitive_file" if sensitive else "system_path" if system else "overwrite_disabled" if p.exists() and overwrite and not self.policy.allow_overwrite else ""
  if reason:allowed=False
  return FilePathValidation(allowed,within,traversal,symlink,sensitive,system,not p.exists() or self.policy.allow_overwrite,reason)
 def dry_run(self,operation,path,content="",destination=""):
  v=self.validate_path(path,overwrite=operation=="write_text");ok=v.target_allowed and len(content)<=self.policy.max_write_chars
  if destination:ok=ok and self.validate_path(destination).target_allowed
  return FileOperationResult(new_id(),"dry_run_completed" if ok else "blocked",operation,safe_ref(path),warnings=("No mutation occurred.",),error=None if ok else v.blocked_reason or "content_too_large")
 def execute(self,operation,path,content="",destination="",approval_id=""):
  preview=self.dry_run(operation,path,content,destination)
  if preview.status!="dry_run_completed":return preview
  resources=(safe_ref(path),)+( (safe_ref(destination),) if destination else ())
  req=ToolExecutionRequest("file_write","file_executor","files",f"{operation} {safe_ref(path)}",ExecutionMode.APPROVED_EXECUTION,ExecutionRisk.HIGH,(ExecutionPermission.WRITE_FILES,),resources,approval_id,False)
  if self.broker.route(req).status!="approved_for_executor":return FileOperationResult(req.request_id,"approval_required",operation,safe_ref(path),error="invalid_or_missing_approval")
  p=self._resolve(path);rid=new_id()
  try:
   if operation in {"create_text_file","write_text"}:
    if p.exists() and (operation=="create_text_file" or not self.policy.allow_overwrite):raise FileExistsError("overwrite_disabled")
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content,encoding="utf-8");self.rollbacks[rid]=("delete",p,len(content))
   elif operation=="append_text":
    old=p.stat().st_size if p.exists() else 0;p.parent.mkdir(parents=True,exist_ok=True);f=p.open("a",encoding="utf-8");f.write(content);f.close();self.rollbacks[rid]=("truncate",p,old)
   elif operation=="create_directory":p.mkdir(parents=False,exist_ok=False);self.rollbacks[rid]=("rmdir",p,0)
   elif operation in {"rename_file","move_file"}:
    d=self._resolve(destination);d.parent.mkdir(parents=True,exist_ok=True);p.rename(d);self.rollbacks[rid]=("move",d,p)
   else:return FileOperationResult(req.request_id,"unavailable",operation,safe_ref(path),error="operation_disabled")
   result=FileOperationResult(req.request_id,"completed",operation,safe_ref(path),len(content),True,rid);self.history=(self.history+[result])[-50:];return result
  except Exception as e:return FileOperationResult(req.request_id,"failed",operation,safe_ref(path),error=bounded(e,120))
 def rollback(self,rid):
  item=self.rollbacks.pop(rid,None)
  if not item:return False
  kind,p,arg=item
  try:
   if kind=="delete" and p.exists():p.unlink()
   elif kind=="truncate" and p.exists():
    with p.open("r+b") as f:f.truncate(arg)
   elif kind=="rmdir" and p.exists():p.rmdir()
   elif kind=="move" and p.exists():p.rename(arg)
   return True
  except OSError:return False
