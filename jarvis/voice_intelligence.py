"""Local-first governed voice input and output for JARVIS OS."""
from __future__ import annotations

import base64, importlib.util, json, logging, os, re, subprocess, wave
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

def now()->str:return datetime.now(UTC).isoformat()
class VoiceMode(StrEnum): OFF="off"; PUSH_TO_TALK="push-to-talk"; SINGLE_LISTEN="single-listen"; CONTINUOUS_READY="continuous-session-ready"; WAKE_WORD_READY="wake-word-ready"
class VoiceState(StrEnum): CREATED="created"; READY="ready"; LISTENING="listening"; PROCESSING="processing"; AWAITING_CONFIRMATION="awaiting_confirmation"; RESPONDING="responding"; SPEAKING="speaking"; INTERRUPTED="interrupted"; PAUSED="paused"; COMPLETED="completed"; CANCELLED="cancelled"; FAILED="failed"; UNAVAILABLE="unavailable"
class VoiceStatus(StrEnum): PENDING="pending"; PROCESSING="processing"; COMPLETED="completed"; LOW_CONFIDENCE="low_confidence"; AMBIGUOUS="ambiguous"; NO_SPEECH="no_speech"; TIMED_OUT="timed_out"; CANCELLED="cancelled"; FAILED="failed"; INVALID_OUTPUT="invalid_output"; UNAVAILABLE="unavailable"
@dataclass(frozen=True,slots=True)
class VoiceLimits:
 max_capture_seconds:int=30; max_audio_size:int=20_000_000; max_audio_duration:int=300; max_transcript_length:int=4000; max_spoken_response_length:int=500; max_sessions:int=1; max_pending_synthesis:int=2; max_pending_transcription:int=2; transcription_timeout:int=60; synthesis_timeout:int=30; playback_timeout:int=30; temp_lifetime_seconds:int=300; retained_audio_count:int=0; retained_session_history:int=50; max_interruptions:int=10; retry_count:int=0
@dataclass(frozen=True,slots=True)
class AudioDeviceInfo:
 device_id:str; name:str; direction:str; backend:str; is_default:bool=False; available:bool=True; sample_rates:tuple[int,...]=(); channel_count:int|None=None; metadata:dict[str,object]=field(default_factory=dict)
@dataclass(frozen=True,slots=True)
class VoiceSession:
 voice_session_id:str; user_session_id:str; mode:VoiceMode; state:VoiceState; parent_request_id:str|None=None; input_backend_id:str|None=None; output_backend_id:str|None=None; input_device_id:str|None=None; output_device_id:str|None=None; language:str="en-US"; started_at:str=field(default_factory=now); updated_at:str=field(default_factory=now); ended_at:str|None=None; capture_started_at:str|None=None; capture_stopped_at:str|None=None; interruption_count:int=0; utterance_count:int=0; transcription_count:int=0; synthesis_count:int=0; privacy_mode:str="standard"; raw_audio_persistence:bool=False; local_only:bool=True; command_confirmation_policy:str="sensitive"; status_message:str=""; last_error:str|None=None; audit_metadata:dict[str,object]=field(default_factory=dict)
@dataclass(frozen=True,slots=True)
class AudioInputRequest:
 audio_request_id:str; voice_session_id:str; parent_request_id:str|None; source_type:str; device_id:str|None=None; file_path:str|None=None; format:str="wav"; sample_rate:int=16000; channels:int=1; language:str="en-US"; maximum_duration:int=30; silence_timeout:int=3; local_only:bool=True; permission_scope:tuple[str,...]=("voice.input",); created_at:str=field(default_factory=now)
@dataclass(frozen=True,slots=True)
class AudioCaptureResult:
 audio_request_id:str; voice_session_id:str; status:VoiceStatus; source_type:str; format:str="wav"; sample_rate:int=0; channels:int=0; duration:float=0; audio_reference:str|None=None; audio_size:int=0; warnings:tuple[str,...]=(); errors:tuple[str,...]=(); started_at:str=field(default_factory=now); completed_at:str=field(default_factory=now)
@dataclass(frozen=True,slots=True)
class TranscriptionRequest:
 transcription_id:str; voice_session_id:str; parent_request_id:str|None; audio_reference:str; backend_id:str; language:str="en-US"; local_only:bool=True; enable_partial_results:bool=False; confidence_threshold:float=.75; maximum_output_length:int=4000; timeout:int=60; created_at:str=field(default_factory=now)
@dataclass(frozen=True,slots=True)
class TranscriptionResult:
 transcription_id:str; voice_session_id:str; parent_request_id:str|None; backend_id:str; status:VoiceStatus; text:str=""; normalized_text:str=""; language:str="en-US"; confidence:float=0; segments:tuple[dict[str,object],...]=(); partial:bool=False; duration:float=0; warnings:tuple[str,...]=(); errors:tuple[str,...]=(); started_at:str=field(default_factory=now); completed_at:str=field(default_factory=now)
@dataclass(frozen=True,slots=True)
class SpeechSynthesisRequest:
 synthesis_id:str; voice_session_id:str; parent_request_id:str|None; backend_id:str; text:str; language:str="en-US"; voice_id:str|None=None; rate:int=0; volume:int=100; output_mode:str="file"; output_path:str|None=None; local_only:bool=True; timeout:int=30; created_at:str=field(default_factory=now)
@dataclass(frozen=True,slots=True)
class SpeechSynthesisResult:
 synthesis_id:str; voice_session_id:str; parent_request_id:str|None; backend_id:str; status:VoiceStatus; audio_reference:str|None=None; output_mode:str="file"; duration:float=0; audio_size:int=0; warnings:tuple[str,...]=(); errors:tuple[str,...]=(); started_at:str=field(default_factory=now); completed_at:str=field(default_factory=now)

class VoiceAdapter(Protocol):
 adapter_id:str; name:str; version:str; local:bool; capabilities:tuple[str,...]; supported_languages:tuple[str,...]; supported_formats:tuple[str,...]; available:bool
 def health_check(self)->dict[str,object]:...

class VoiceAdapterRegistry:
 def __init__(self):self._items:dict[str,VoiceAdapter]={}
 def register(self,adapter:VoiceAdapter):
  if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{2,63}",adapter.adapter_id) or adapter.adapter_id in self._items:raise ValueError("invalid_or_duplicate_adapter")
  if not adapter.capabilities:raise ValueError("adapter_capabilities_required")
  self._items[adapter.adapter_id]=adapter
 def get(self,aid):return self._items.get(aid)
 def list(self):return tuple(self._items.values())

class WindowsSapiAdapter:
 adapter_id="windows-sapi";name="Windows SAPI";version="1";local=True;capabilities=("synthesis","playback","wav");supported_languages=("en-US",);supported_formats=("wav",)
 def __init__(self):self.available=self._check()
 def _check(self):
  try:
   script="Add-Type -AssemblyName System.Speech;$s=[System.Speech.Synthesis.SpeechSynthesizer]::new();try{$s.GetInstalledVoices().Count}finally{$s.Dispose()}";encoded=base64.b64encode(script.encode("utf-16le")).decode("ascii")
   p=subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-EncodedCommand",encoded],capture_output=True,text=True,timeout=5,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0));return p.returncode==0 and int(p.stdout.strip() or 0)>0
  except Exception:return False
 def health_check(self):return {"status":"healthy" if self.available else "unavailable","local":True}
 @staticmethod
 def _script(output_mode:str)->str:
  common="""$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$text = [Environment]::GetEnvironmentVariable('JARVIS_SPEECH_TEXT', 'Process')
$rate = [int][Environment]::GetEnvironmentVariable('JARVIS_SPEECH_RATE', 'Process')
$volume = [int][Environment]::GetEnvironmentVariable('JARVIS_SPEECH_VOLUME', 'Process')
"""
  file_script="""$path = [Environment]::GetEnvironmentVariable('JARVIS_SPEECH_PATH', 'Process')
if ([string]::IsNullOrWhiteSpace($path)) { throw 'output_path_required' }
$directory = [IO.Path]::GetDirectoryName($path)
if (-not [string]::IsNullOrWhiteSpace($directory)) { [IO.Directory]::CreateDirectory($directory) | Out-Null }
$fileSynth = [System.Speech.Synthesis.SpeechSynthesizer]::new()
try {
    $fileSynth.Rate = $rate
    $fileSynth.Volume = $volume
    $fileSynth.SetOutputToWaveFile($path)
    $fileSynth.Speak($text)
} finally {
    $fileSynth.Dispose()
}
"""
  playback_script="""$playbackSynth = [System.Speech.Synthesis.SpeechSynthesizer]::new()
try {
    $playbackSynth.Rate = $rate
    $playbackSynth.Volume = $volume
    $playbackSynth.SetOutputToDefaultAudioDevice()
    $playbackSynth.Speak($text)
} finally {
    $playbackSynth.Dispose()
}
"""
  return common+(file_script if output_mode in {"file","both"} else "")+(playback_script if output_mode in {"playback","both"} else "")
 @staticmethod
 def _safe_error(stderr:str,text:str,path:Path|None)->str:
  message=" ".join((stderr or "").split())
  for sensitive in (text,str(path) if path else ""):
   if sensitive:message=message.replace(sensitive,"[REDACTED]")
  message=re.sub(r"(?i)(authorization|api[_-]?key|token|password|secret)\s*[:=]\s*\S+",r"\1=[REDACTED]",message)
  return message[:300]
 def synthesize(self,request:SpeechSynthesisRequest)->SpeechSynthesisResult:
  if not self.available:return SpeechSynthesisResult(request.synthesis_id,request.voice_session_id,request.parent_request_id,self.adapter_id,VoiceStatus.UNAVAILABLE,output_mode=request.output_mode,errors=("backend_unavailable",))
  if request.output_mode not in {"playback","file","both"}:return SpeechSynthesisResult(request.synthesis_id,request.voice_session_id,request.parent_request_id,self.adapter_id,VoiceStatus.FAILED,output_mode=request.output_mode,errors=("unsupported_output_mode",))
  path=Path(request.output_path).resolve() if request.output_path else None
  if request.output_mode in {"file","both"} and path is None:return SpeechSynthesisResult(request.synthesis_id,request.voice_session_id,request.parent_request_id,self.adapter_id,VoiceStatus.FAILED,request.output_path,request.output_mode,errors=("output_path_required",))
  before=(path.stat().st_mtime_ns,path.stat().st_size) if path and path.exists() else None
  try:
   if path:path.parent.mkdir(parents=True,exist_ok=True)
   encoded=base64.b64encode(self._script(request.output_mode).encode("utf-16le")).decode("ascii")
   environment=os.environ.copy();environment.update({"JARVIS_SPEECH_TEXT":request.text,"JARVIS_SPEECH_RATE":str(request.rate),"JARVIS_SPEECH_VOLUME":str(request.volume),"JARVIS_SPEECH_PATH":str(path) if path else ""})
   p=subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-EncodedCommand",encoded],capture_output=True,text=True,timeout=request.timeout,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0),env=environment)
   if p.returncode:
    detail=self._safe_error(p.stderr,request.text,path);errors=("synthesis_failed",detail) if detail else ("synthesis_failed",)
    return SpeechSynthesisResult(request.synthesis_id,request.voice_session_id,request.parent_request_id,self.adapter_id,VoiceStatus.FAILED,output_mode=request.output_mode,errors=errors)
   size=path.stat().st_size if path and path.exists() else 0
   if path and (size<=0 or (before is not None and before==(path.stat().st_mtime_ns,size))):return SpeechSynthesisResult(request.synthesis_id,request.voice_session_id,request.parent_request_id,self.adapter_id,VoiceStatus.FAILED,output_mode=request.output_mode,errors=("audio_file_not_created",))
   return SpeechSynthesisResult(request.synthesis_id,request.voice_session_id,request.parent_request_id,self.adapter_id,VoiceStatus.COMPLETED,str(path) if path else None,request.output_mode,audio_size=size)
  except subprocess.TimeoutExpired:return SpeechSynthesisResult(request.synthesis_id,request.voice_session_id,request.parent_request_id,self.adapter_id,VoiceStatus.TIMED_OUT,output_mode=request.output_mode,errors=("synthesis_timeout",))
  except FileNotFoundError:return SpeechSynthesisResult(request.synthesis_id,request.voice_session_id,request.parent_request_id,self.adapter_id,VoiceStatus.UNAVAILABLE,output_mode=request.output_mode,errors=("powershell_unavailable",))
  except OSError as exc:
   detail=self._safe_error(str(exc),request.text,path);errors=("synthesis_error",detail) if detail else ("synthesis_error",)
   return SpeechSynthesisResult(request.synthesis_id,request.voice_session_id,request.parent_request_id,self.adapter_id,VoiceStatus.FAILED,output_mode=request.output_mode,errors=errors)

class OfflineSttDiscoveryAdapter:
 adapter_id="offline-stt";name="Offline STT discovery";version="1";local=True;capabilities=("transcription",);supported_languages=("en",);supported_formats=("wav",)
 def __init__(self):self.engine="vosk" if importlib.util.find_spec("vosk") else "faster-whisper" if importlib.util.find_spec("faster_whisper") else None;self.available=False
 def health_check(self):return {"status":"unavailable","dependency":self.engine or "none","model_ready":False,"local":True}

class VoiceIntelligence:
 def __init__(self,settings:Any=None,storage_dir:Path|None=None,logger:logging.Logger|None=None):
  self.settings=settings;self.storage_dir=storage_dir;self.logger=logger or logging.getLogger("voice_intelligence");self.registry=VoiceAdapterRegistry();self.registry.register(WindowsSapiAdapter());self.registry.register(OfflineSttDiscoveryAdapter())
  config=getattr(settings,"voice",None)
  self.enabled=bool(getattr(config,"enabled",False));self.input_enabled=bool(getattr(config,"input_enabled",False));self.output_enabled=bool(getattr(config,"output_enabled",False))
  try:self.mode=VoiceMode(getattr(config,"mode","off"))
  except ValueError:self.mode=VoiceMode.OFF
  self.privacy_mode=str(getattr(config,"privacy_mode","standard"));self.raw_audio_persistence=bool(getattr(config,"raw_audio_persistence",False));self.local_only=bool(getattr(config,"local_only",True));self.language=str(getattr(config,"language","en-US"));self.rate=int(getattr(config,"rate",0));self.volume=int(getattr(config,"volume",100));self.wake_word_enabled=False
  requested_input=str(getattr(config,"input_backend","offline-stt"));requested_output=str(getattr(config,"output_backend","windows-sapi"));self.selected_input_backend=requested_input if self.registry.get(requested_input) else "offline-stt";self.selected_output_backend=requested_output if self.registry.get(requested_output) else "windows-sapi"
  self.allowed_audio_directories=tuple(getattr(config,"allowed_audio_directories",()) or ())
  self.sessions:dict[str,VoiceSession]={};self.limits=VoiceLimits(max_capture_seconds=int(getattr(config,"max_capture_seconds",30)),max_audio_size=int(getattr(config,"max_audio_size",20_000_000)),max_transcript_length=int(getattr(config,"max_transcript_length",4000)),max_spoken_response_length=int(getattr(config,"max_spoken_response_length",500)),retained_audio_count=int(getattr(config,"retention_limit",0)));self.initialized=True;self.logger.info("voice_initialized enabled=%s microphone=%s wake_word=false",self.enabled,self.input_enabled)
 def create_session(self,user_session_id="default",parent_request_id=None):
  if len([s for s in self.sessions.values() if s.state not in {VoiceState.COMPLETED,VoiceState.CANCELLED,VoiceState.FAILED}])>=self.limits.max_sessions:raise ValueError("voice_session_limit")
  s=VoiceSession(str(uuid4()),user_session_id,self.mode,VoiceState.READY if self.enabled else VoiceState.UNAVAILABLE,parent_request_id, self.selected_input_backend,self.selected_output_backend,language=self.language,privacy_mode=self.privacy_mode,raw_audio_persistence=self.raw_audio_persistence,local_only=self.local_only or self.privacy_mode=="strict");self.sessions[s.voice_session_id]=s;self._save();return s
 def devices(self,direction=None):
  items=(AudioDeviceInfo("default-output","Default Windows audio output","output","windows-sapi",True,self.registry.get("windows-sapi").available),)
  return tuple(x for x in items if direction in {None,x.direction})
 def validate_audio_file(self,path_text,allowed_dirs:tuple[Path,...]=()):
  path=Path(path_text).resolve(); roots=allowed_dirs or self.allowed_audio_directories or ((self.settings.base_dir if self.settings else Path.cwd()),)
  if not any(path==r.resolve() or r.resolve() in path.parents for r in roots):raise ValueError("audio_path_outside_allowed_scope")
  if path.suffix.lower()!=".wav" or not path.is_file():raise ValueError("unsupported_or_missing_audio_file")
  if path.stat().st_size>self.limits.max_audio_size:raise ValueError("audio_too_large")
  try:
   with wave.open(str(path),"rb") as w: duration=w.getnframes()/max(1,w.getframerate()); rate=w.getframerate(); channels=w.getnchannels()
  except (wave.Error,EOFError):raise ValueError("malformed_audio_file")
  if duration>self.limits.max_audio_duration:raise ValueError("audio_too_long")
  return AudioCaptureResult(str(uuid4()),"file",VoiceStatus.COMPLETED,"audio_file","wav",rate,channels,duration,str(path),path.stat().st_size)
 def validate_transcript(self,result:TranscriptionResult):
  text=result.text.strip()
  if not text or len(text)>self.limits.max_transcript_length or any(ord(c)<32 and c not in "\n\t" for c in text):return "rejected"
  if result.confidence<.6:return "low_confidence"
  if result.confidence<.75:return "ambiguous"
  return "accepted"
 def classify(self,text,command_manager=None):
  low=text.strip().lower()
  if low in {"stop","cancel","interrupt"}:return "cancellation"
  if command_manager and command_manager.registry.resolve(low.split()[0]) is not None:return "command"
  return "conversation"
 def response_policy(self,text,sensitive=False):
  if not self.output_enabled or sensitive or re.search(r"api[_ -]?key|password|authorization|credential|secret|access[_ -]?token",text,re.I):return {"speak":False,"reason":"disabled_or_sensitive"}
  if "```" in text:return {"speak":False,"reason":"code_text_only"}
  spoken=text if len(text)<=self.limits.max_spoken_response_length else text[:self.limits.max_spoken_response_length].rsplit(" ",1)[0]+". More detail is available on screen."
  return {"speak":True,"text":spoken}
 def say(self,text,parent_request_id="voice-command",output_path:Path|None=None,playback=False):
  if not self.output_enabled:raise ValueError("voice_output_disabled")
  policy=self.response_policy(text)
  if not policy["speak"]:raise ValueError(str(policy["reason"]))
  session=self.create_session(parent_request_id=parent_request_id);path=output_path
  if not playback:
   path=path or ((self.storage_dir or Path.cwd())/"voice-output"/f"{uuid4()}.wav");path.parent.mkdir(parents=True,exist_ok=True)
  req=SpeechSynthesisRequest(str(uuid4()),session.voice_session_id,parent_request_id,self.selected_output_backend,str(policy["text"]),self.language,rate=self.rate,volume=self.volume,output_mode="playback" if playback and path is None else "both" if playback else "file",output_path=str(path) if path else None,local_only=self.local_only,timeout=self.limits.synthesis_timeout)
  self.logger.info("synthesis_started request_id=%s voice_session_id=%s synthesis_id=%s backend_id=%s",parent_request_id,session.voice_session_id,req.synthesis_id,req.backend_id)
  result=self.registry.get(req.backend_id).synthesize(req);self.sessions[session.voice_session_id]=replace(session,state=VoiceState.COMPLETED if result.status==VoiceStatus.COMPLETED else VoiceState.FAILED,synthesis_count=1,ended_at=now(),updated_at=now(),last_error=result.errors[0] if result.errors else None);self._save();self.logger.info("synthesis_completed request_id=%s voice_session_id=%s synthesis_id=%s backend_id=%s status=%s",parent_request_id,session.voice_session_id,result.synthesis_id,result.backend_id,result.status.value);return result
 def transcribe_file(self,path):
  capture=self.validate_audio_file(path);adapter=self.registry.get(self.selected_input_backend)
  if not adapter.available:return TranscriptionResult(str(uuid4()),capture.voice_session_id,None,adapter.adapter_id,VoiceStatus.UNAVAILABLE,errors=("offline_stt_model_unavailable",))
  return TranscriptionResult(str(uuid4()),capture.voice_session_id,None,adapter.adapter_id,VoiceStatus.FAILED,errors=("adapter_execution_not_configured",))
 def interrupt(self):
  changed=False
  for sid,s in tuple(self.sessions.items()):
   if s.state not in {VoiceState.COMPLETED,VoiceState.CANCELLED,VoiceState.FAILED}:self.sessions[sid]=replace(s,state=VoiceState.INTERRUPTED,interruption_count=s.interruption_count+1,updated_at=now());changed=True
  self._save();return changed
 def cancel(self):
  for sid,s in tuple(self.sessions.items()):
   if s.state not in {VoiceState.COMPLETED,VoiceState.CANCELLED,VoiceState.FAILED}:self.sessions[sid]=replace(s,state=VoiceState.CANCELLED,ended_at=now(),updated_at=now())
  self._save();return True
 def health(self):return {a.adapter_id:a.health_check() for a in self.registry.list()}|{"enabled":self.enabled,"input_enabled":self.input_enabled,"output_enabled":self.output_enabled,"wake_word_enabled":False}
 def _save(self):
  if not self.storage_dir:return
  self.storage_dir.mkdir(parents=True,exist_ok=True);records=list(self.sessions.values())[-self.limits.retained_session_history:];(self.storage_dir/"sessions.json").write_text(json.dumps([asdict(x) for x in records],default=str,indent=2),encoding="utf-8")
