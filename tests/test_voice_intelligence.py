import base64,os,subprocess,tempfile,unittest,wave
from types import SimpleNamespace
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from commands import CommandManager
from commands.command_parser import CommandParser
from conversation import ConversationContext,ConversationSession
from jarvis.stt_intelligence import VoskSTTAdapter
from jarvis.voice_intelligence import *

class FakeAdapter:
 adapter_id="test-stt";name="test";version="1";local=True;capabilities=("transcription",);supported_languages=("en",);supported_formats=("wav",);available=True
 def health_check(self):return {"status":"healthy"}

class VoiceTests(unittest.TestCase):
 def setUp(self):self.v=VoiceIntelligence()
 def sapi(self):
  adapter=object.__new__(WindowsSapiAdapter);adapter.available=True;return adapter
 def synthesis_request(self,mode,path=None,text="JARVIS voice test"):
  return SpeechSynthesisRequest("synth","session","parent","windows-sapi",text,output_mode=mode,output_path=str(path) if path else None)
 def successful_run(self,args,**kwargs):
  output=kwargs["env"].get("JARVIS_SPEECH_PATH")
  if output:Path(output).write_bytes(b"RIFF-test-wave")
  return subprocess.CompletedProcess(args,0,"","")
 def decoded_script(self,run):
  args=run.call_args.args[0];return base64.b64decode(args[args.index("-EncodedCommand")+1]).decode("utf-16le")
 def force_stt_unavailable(self):
  self.v.voice_input.stt_adapter=VoskSTTAdapter(Path(__file__).parent/"missing-vosk-model")
 def wav(self,root,seconds=.1):
  p=Path(root)/"x.wav"
  with wave.open(str(p),"wb") as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(b"\0\0"*int(16000*seconds))
  return p
 def test_disabled_default(self):self.assertFalse(self.v.enabled)
 def test_input_disabled_default(self):self.assertFalse(self.v.input_enabled)
 def test_output_disabled_default(self):self.assertFalse(self.v.output_enabled)
 def test_wake_word_disabled(self):self.assertFalse(self.v.wake_word_enabled)
 def test_raw_audio_disabled(self):self.assertFalse(self.v.raw_audio_persistence)
 def test_runtime_uses_voice_configuration(self):
  config=SimpleNamespace(enabled=True,input_enabled=True,output_enabled=True,mode="push-to-talk",local_only=True,language="en-GB",rate=2,volume=80,max_capture_seconds=12,max_audio_size=100000,max_transcript_length=900,max_spoken_response_length=200,retention_limit=0,allowed_audio_directories=())
  voice=VoiceIntelligence(SimpleNamespace(voice=config,base_dir=Path.cwd()))
  self.assertTrue(voice.enabled);self.assertTrue(voice.input_enabled);self.assertEqual(voice.mode,VoiceMode.PUSH_TO_TALK);self.assertEqual(voice.limits.max_capture_seconds,12);self.assertEqual(voice.language,"en-GB")
 def test_configured_audio_scope_is_enforced(self):
  with tempfile.TemporaryDirectory() as allowed,tempfile.TemporaryDirectory() as blocked:
   config=SimpleNamespace(allowed_audio_directories=(Path(allowed),))
   voice=VoiceIntelligence(SimpleNamespace(voice=config,base_dir=Path.cwd()))
   self.assertEqual(voice.validate_audio_file(str(self.wav(allowed))).status,VoiceStatus.COMPLETED)
   self.assertRaises(ValueError,voice.validate_audio_file,str(self.wav(blocked)))
 def test_local_tts_registered(self):self.assertIsNotNone(self.v.registry.get("windows-sapi"))
 def test_stt_availability_is_reported_truthfully(self):
  status=self.v.input_status();self.assertEqual(status["stt_available"],self.v.voice_input.stt_adapter.available)
 def test_adapter_registration(self):self.v.registry.register(FakeAdapter());self.assertIsNotNone(self.v.registry.get("test-stt"))
 def test_duplicate_adapter_rejected(self):self.v.registry.register(FakeAdapter());self.assertRaises(ValueError,self.v.registry.register,FakeAdapter())
 def test_malformed_adapter_rejected(self):
  a=FakeAdapter();a.adapter_id="?";self.assertRaises(ValueError,self.v.registry.register,a)
 def test_devices_normalized(self):self.assertEqual(self.v.devices("output")[0].direction,"output")
 def test_input_devices_match_detected_microphone_state(self):
  devices=self.v.devices("input");self.assertEqual(bool(devices),self.v.input_status()["microphone_available"]);self.assertTrue(all(item.direction=="input" for item in devices))
 def test_session_unavailable_when_disabled(self):self.assertEqual(self.v.create_session().state,VoiceState.UNAVAILABLE)
 def test_session_ready_after_enable(self):self.v.enabled=True;self.assertEqual(self.v.create_session().state,VoiceState.READY)
 def test_session_limit(self):self.v.enabled=True;self.v.create_session();self.assertRaises(ValueError,self.v.create_session)
 def test_audio_file_validation(self):
  with tempfile.TemporaryDirectory() as d:p=self.wav(d);self.assertEqual(self.v.validate_audio_file(str(p),(Path(d),)).status,VoiceStatus.COMPLETED)
 def test_path_scope_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=self.wav(d)
   with tempfile.TemporaryDirectory() as other:self.assertRaises(ValueError,self.v.validate_audio_file,str(p),(Path(other),))
 def test_unsupported_format(self):
  with tempfile.TemporaryDirectory() as d:p=Path(d)/"x.txt";p.write_text("x");self.assertRaises(ValueError,self.v.validate_audio_file,str(p),(Path(d),))
 def test_malformed_wav(self):
  with tempfile.TemporaryDirectory() as d:p=Path(d)/"x.wav";p.write_bytes(b"bad");self.assertRaises(ValueError,self.v.validate_audio_file,str(p),(Path(d),))
 def test_audio_size_limit(self):
  with tempfile.TemporaryDirectory() as d:p=self.wav(d);v=VoiceIntelligence();v.limits=replace(v.limits,max_audio_size=1);self.assertRaises(ValueError,v.validate_audio_file,str(p),(Path(d),))
 def test_audio_duration_limit(self):
  with tempfile.TemporaryDirectory() as d:p=self.wav(d,.2);v=VoiceIntelligence();v.limits=replace(v.limits,max_audio_duration=0);self.assertRaises(ValueError,v.validate_audio_file,str(p),(Path(d),))
 def transcript(self,text="hello",confidence=.9):return TranscriptionResult("t","s",None,"test",VoiceStatus.COMPLETED,text,text,"en",confidence)
 def test_empty_transcript(self):self.assertEqual(self.v.validate_transcript(self.transcript("")),"rejected")
 def test_long_transcript(self):self.assertEqual(self.v.validate_transcript(self.transcript("x"*5000)),"rejected")
 def test_low_confidence(self):self.assertEqual(self.v.validate_transcript(self.transcript(confidence=.4)),"low_confidence")
 def test_ambiguous(self):self.assertEqual(self.v.validate_transcript(self.transcript(confidence=.7)),"ambiguous")
 def test_accepted(self):self.assertEqual(self.v.validate_transcript(self.transcript()),"accepted")
 def test_cancellation_classified(self):self.assertEqual(self.v.classify("stop"),"cancellation")
 def test_conversation_classified(self):self.assertEqual(self.v.classify("hello"),"conversation")
 def test_sensitive_response_blocked(self):self.assertFalse(self.v.response_policy("API key abc",False)["speak"])
 def test_secret_response_blocked(self):self.v.output_enabled=True;self.assertFalse(self.v.response_policy("Client secret hidden",False)["speak"])
 def test_code_response_blocked(self):self.v.output_enabled=True;self.assertFalse(self.v.response_policy("```python\nx=1\n```")["speak"])
 def test_long_response_summarized(self):self.v.output_enabled=True;self.assertIn("More detail",self.v.response_policy("word "*200)["text"])
 def test_output_must_be_enabled(self):self.assertRaises(ValueError,self.v.say,"hello")
 def test_playback_does_not_create_a_wav_by_default(self):
  self.v.output_enabled=True;self.v.enabled=True
  completed=SpeechSynthesisResult("s","session","parent","windows-sapi",VoiceStatus.COMPLETED,output_mode="playback")
  with patch.object(self.v.registry.get("windows-sapi"),"synthesize",return_value=completed) as synthesize:
   result=self.v.say("voice test",playback=True)
  request=synthesize.call_args.args[0]
  self.assertEqual(result.status,VoiceStatus.COMPLETED);self.assertEqual(request.output_mode,"playback");self.assertIsNone(request.output_path)
 def test_say_defaults_to_playback_without_permanent_audio(self):
  self.v.output_enabled=True;self.v.enabled=True
  completed=SpeechSynthesisResult("s","session","parent","windows-sapi",VoiceStatus.COMPLETED,output_mode="playback")
  with patch.object(self.v.registry.get("windows-sapi"),"synthesize",return_value=completed) as synthesize:self.v.say("voice test")
  request=synthesize.call_args.args[0]
  self.assertEqual(request.output_mode,"playback");self.assertIsNone(request.output_path)
 def test_explicit_output_path_is_required_for_file_creation(self):
  self.v.output_enabled=True;self.v.enabled=True
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/"saved.wav";completed=SpeechSynthesisResult("s","session","parent","windows-sapi",VoiceStatus.COMPLETED,str(path),"file")
   with patch.object(self.v.registry.get("windows-sapi"),"synthesize",return_value=completed) as synthesize:self.v.say("voice test",output_path=path,playback=False)
   self.assertEqual(synthesize.call_args.args[0].output_mode,"file");self.assertEqual(synthesize.call_args.args[0].output_path,str(path))
 def test_real_sapi_file_when_available(self):
  if not self.v.registry.get("windows-sapi").available:self.skipTest("Windows SAPI unavailable")
  with tempfile.TemporaryDirectory() as d:self.v.output_enabled=True;r=self.v.say("voice test",output_path=Path(d)/"out.wav");self.assertEqual(r.status,VoiceStatus.COMPLETED);self.assertGreater(r.audio_size,0)
 def test_sapi_file_only_mode(self):
  with tempfile.TemporaryDirectory() as d,patch("jarvis.voice_intelligence.subprocess.run",side_effect=self.successful_run) as run:
   path=Path(d)/"nested"/"out.wav";result=self.sapi().synthesize(self.synthesis_request("file",path));script=self.decoded_script(run)
   self.assertEqual(result.status,VoiceStatus.COMPLETED);self.assertGreater(result.audio_size,0);self.assertIn("SetOutputToWaveFile",script);self.assertNotIn("SetOutputToDefaultAudioDevice",script)
 def test_sapi_playback_only_mode(self):
  with patch("jarvis.voice_intelligence.subprocess.run",return_value=subprocess.CompletedProcess([],0,"","")) as run:
   result=self.sapi().synthesize(self.synthesis_request("playback"));script=self.decoded_script(run)
   self.assertEqual(result.status,VoiceStatus.COMPLETED);self.assertIsNone(result.audio_reference);self.assertIn("SetOutputToDefaultAudioDevice",script);self.assertNotIn("SetOutputToWaveFile",script)
   self.assertEqual(run.call_args.kwargs["timeout"],30)
 def test_sapi_long_playback_uses_bounded_adaptive_timeout(self):
  spoken="A reasonably detailed assistant sentence. "*12
  with patch("jarvis.voice_intelligence.subprocess.run",return_value=subprocess.CompletedProcess([],0,"","")) as run:
   result=self.sapi().synthesize(self.synthesis_request("playback",text=spoken))
  timeout=run.call_args.kwargs["timeout"]
  self.assertEqual(result.status,VoiceStatus.COMPLETED);self.assertGreater(timeout,30);self.assertLessEqual(timeout,90);self.assertIsNone(result.audio_reference)
 def test_sapi_timeout_bounds_cover_slow_and_fast_rates(self):
  adapter=self.sapi();text="x"*500
  slow=adapter.bounded_synthesis_timeout(text,5,-10);normal=adapter.bounded_synthesis_timeout(text,30,0);fast=adapter.bounded_synthesis_timeout(text,5,10)
  self.assertLessEqual(slow,90);self.assertGreaterEqual(fast,15);self.assertGreater(slow,normal);self.assertGreater(normal,fast)
 def test_sapi_both_mode(self):
  with tempfile.TemporaryDirectory() as d,patch("jarvis.voice_intelligence.subprocess.run",side_effect=self.successful_run) as run:
   result=self.sapi().synthesize(self.synthesis_request("both",Path(d)/"out.wav"));script=self.decoded_script(run)
   self.assertEqual(result.status,VoiceStatus.COMPLETED);self.assertIn("SetOutputToWaveFile",script);self.assertIn("SetOutputToDefaultAudioDevice",script)
 def test_sapi_file_modes_require_output_path(self):
  for mode in ("file","both"):
   with self.subTest(mode=mode):self.assertEqual(self.sapi().synthesize(self.synthesis_request(mode)).errors,("output_path_required",))
 def test_sapi_powershell_failure_is_bounded_and_redacted(self):
  spoken="don't expose $secret; \"quoted\""
  failed=subprocess.CompletedProcess([],1,"",f"device failed while processing {spoken}")
  with patch("jarvis.voice_intelligence.subprocess.run",return_value=failed):result=self.sapi().synthesize(self.synthesis_request("playback",text=spoken))
  self.assertEqual(result.status,VoiceStatus.FAILED);self.assertIn("device failed",result.errors[1]);self.assertNotIn(spoken,result.errors[1]);self.assertLessEqual(len(result.errors[1]),300)
 def test_sapi_timeout(self):
  with patch("jarvis.voice_intelligence.subprocess.run",side_effect=subprocess.TimeoutExpired("powershell",1)):result=self.sapi().synthesize(self.synthesis_request("playback"))
  self.assertEqual(result.status,VoiceStatus.TIMED_OUT);self.assertEqual(result.errors,("synthesis_timeout",));self.assertIsNone(result.audio_reference)
 def test_sapi_special_text_uses_environment_not_command(self):
  spoken="O'Brien says $value; \"hello\"\nUnicode: \u0928\u092e\u0938\u094d\u0924\u0947"
  with patch("jarvis.voice_intelligence.subprocess.run",return_value=subprocess.CompletedProcess([],0,"","")) as run:
   self.assertEqual(self.sapi().synthesize(self.synthesis_request("playback",text=spoken)).status,VoiceStatus.COMPLETED)
   self.assertEqual(run.call_args.kwargs["env"]["JARVIS_SPEECH_TEXT"],spoken);self.assertNotIn(spoken," ".join(run.call_args.args[0]));self.assertNotIn(spoken,self.decoded_script(run))
 def test_stt_unavailable_not_fake(self):
  self.force_stt_unavailable()
  with tempfile.TemporaryDirectory() as d:p=self.wav(d);self.v.settings=SimpleNamespace(base_dir=Path(d));r=self.v.transcribe_file(str(p));self.assertEqual(r.status,VoiceStatus.UNAVAILABLE)
 def test_input_status_reports_missing_local_capabilities(self):
  status=self.v.input_status();self.assertEqual(status["ready"],status["stt_available"] and status["microphone_available"])
  self.assertEqual("local_stt_model" in status["missing_capabilities"],not status["model_ready"]);self.assertEqual("microphone_capture_adapter" in status["missing_capabilities"],not status["microphone_available"])
 def test_temp_audio_cleanup_is_scoped_and_safe(self):
  with tempfile.TemporaryDirectory() as d:
   voice=VoiceIntelligence(SimpleNamespace(voice=SimpleNamespace(temp_directory=Path(d)),base_dir=Path(d)))
   (Path(d)/"capture.wav").write_bytes(b"audio");(Path(d)/"keep.txt").write_text("keep",encoding="utf-8")
   result=voice.cleanup_temp_audio();self.assertEqual(result,{"removed":1,"failed":0,"remaining":0});self.assertTrue((Path(d)/"keep.txt").exists())
 def test_temp_audio_retention_policy_keeps_allowed_recent_files(self):
  with tempfile.TemporaryDirectory() as d:
   config=SimpleNamespace(temp_directory=Path(d),retention_limit=1,temp_audio_lifetime_seconds=300)
   voice=VoiceIntelligence(SimpleNamespace(voice=config,base_dir=Path(d)));older=Path(d)/"older.wav";newer=Path(d)/"newer.wav";older.write_bytes(b"a");newer.write_bytes(b"b");os.utime(older,(1,1))
   result=voice.cleanup_temp_audio(remove_all=False);self.assertEqual(result["remaining"],1);self.assertTrue(newer.exists())
 def test_voice_status_reports_input_output_and_storage(self):
  commands=CommandManager();commands.initialize();context=ConversationContext(session=ConversationSession(),voice_intelligence=self.v)
  response=commands.execute("voice status",context)
  expected_stt="ready" if self.v.input_status()["stt_available"] else "unavailable"
  for value in ("output=off","input=off",f"stt={expected_stt}","raw_audio_persistence=off","retained_audio=0"):self.assertIn(value,response.response)
 def test_voice_input_commands_are_truthful_without_stt(self):
  self.force_stt_unavailable()
  commands=CommandManager();commands.initialize();context=ConversationContext(session=ConversationSession(),voice_intelligence=self.v)
  self.assertIn("stt=unavailable",commands.execute("voice input status",context).response)
  response=commands.execute("voice input on",context).response
  self.assertIn("not available",response);self.assertIn("local Vosk model",response);self.assertFalse(self.v.input_enabled)
  listen_response=commands.execute("voice listen",context).response
  self.assertIn("not available",listen_response);self.assertIn("local Vosk model",listen_response)
  self.assertIn("disabled",commands.execute("voice input off",context).response)
 def test_voice_cleanup_command(self):
  with tempfile.TemporaryDirectory() as d:
   voice=VoiceIntelligence(SimpleNamespace(voice=SimpleNamespace(temp_directory=Path(d)),base_dir=Path(d)));(Path(d)/"capture.wav").write_bytes(b"audio")
   commands=CommandManager();commands.initialize();context=ConversationContext(session=ConversationSession(),voice_intelligence=voice)
   response=commands.execute("voice cleanup",context);self.assertIn("removed=1",response.response);self.assertFalse((Path(d)/"capture.wav").exists())
 def test_cleanup_removes_legacy_generated_output_but_not_input(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);temp=root/"temp";output=root/"voice-output";input_dir=root/"voice-input";output.mkdir();input_dir.mkdir()
   (output/"old.wav").write_bytes(b"audio");(input_dir/"user.wav").write_bytes(b"audio")
   voice=VoiceIntelligence(SimpleNamespace(voice=SimpleNamespace(temp_directory=temp),base_dir=root),storage_dir=root)
   self.assertFalse((output/"old.wav").exists());self.assertTrue((input_dir/"user.wav").exists())
 def test_repository_tracks_no_audio_artifacts(self):
  tracked=subprocess.run(["git","ls-files","*.wav","*.mp3","*.flac","*.ogg"],capture_output=True,text=True,check=True,cwd=Path(__file__).resolve().parents[1])
  self.assertEqual(tracked.stdout.strip(),"")
 def test_interrupt_idempotent(self):self.assertFalse(self.v.interrupt())
 def test_cancel(self):self.v.enabled=True;s=self.v.create_session();self.v.cancel();self.assertEqual(self.v.sessions[s.voice_session_id].state,VoiceState.CANCELLED)
 def test_persistence_summary(self):
  with tempfile.TemporaryDirectory() as d:v=VoiceIntelligence(storage_dir=Path(d));v.enabled=True;v.create_session();v.cancel();self.assertTrue((Path(d)/"sessions.json").exists())
 def test_parser_command_separation(self):self.assertEqual(CommandParser().parse("voice say hello").name,"voice say")
 def test_voice_say_command_requests_playback(self):
  class CapturingVoice:
   def __init__(self):self.playback=None
   def say(self,text,parent_request_id,playback=False):self.playback=playback;return SimpleNamespace(status=VoiceStatus.COMPLETED,audio_reference="out.wav",synthesis_id="s",backend_id="windows-sapi")
  voice=CapturingVoice();commands=CommandManager();commands.initialize();context=ConversationContext(session=ConversationSession(),voice_intelligence=voice)
  self.assertIn("completed",commands.execute("voice say hello",context).response);self.assertTrue(voice.playback)
 def test_parser_preserves_windows_audio_path(self):
  parsed=CommandParser().parse(r"voice transcribe C:\voice-input\sample.wav")
  self.assertEqual(parsed.arguments,(r"C:\voice-input\sample.wav",))
 def test_health(self):self.assertIn("windows-sapi",self.v.health())
 def test_strict_privacy_local(self):self.v.privacy_mode="strict";self.v.enabled=True;self.assertTrue(self.v.create_session().local_only)
 def test_wake_word_no_approval(self):self.assertNotIn("approval",self.v.health())

if __name__=="__main__":unittest.main()
