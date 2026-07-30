import tempfile,unittest,wave
from types import SimpleNamespace
from dataclasses import replace
from pathlib import Path
from commands.command_parser import CommandParser
from jarvis.voice_intelligence import *

class FakeAdapter:
 adapter_id="test-stt";name="test";version="1";local=True;capabilities=("transcription",);supported_languages=("en",);supported_formats=("wav",);available=True
 def health_check(self):return {"status":"healthy"}

class VoiceTests(unittest.TestCase):
 def setUp(self):self.v=VoiceIntelligence()
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
 def test_stt_truthful_unavailable(self):self.assertFalse(self.v.registry.get("offline-stt").available)
 def test_adapter_registration(self):self.v.registry.register(FakeAdapter());self.assertIsNotNone(self.v.registry.get("test-stt"))
 def test_duplicate_adapter_rejected(self):self.v.registry.register(FakeAdapter());self.assertRaises(ValueError,self.v.registry.register,FakeAdapter())
 def test_malformed_adapter_rejected(self):
  a=FakeAdapter();a.adapter_id="?";self.assertRaises(ValueError,self.v.registry.register,a)
 def test_devices_normalized(self):self.assertEqual(self.v.devices("output")[0].direction,"output")
 def test_no_input_device_fabricated(self):self.assertEqual(self.v.devices("input"),())
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
 def test_code_response_blocked(self):self.v.output_enabled=True;self.assertFalse(self.v.response_policy("```python\nx=1\n```")["speak"])
 def test_long_response_summarized(self):self.v.output_enabled=True;self.assertIn("More detail",self.v.response_policy("word "*200)["text"])
 def test_output_must_be_enabled(self):self.assertRaises(ValueError,self.v.say,"hello")
 def test_real_sapi_file_when_available(self):
  if not self.v.registry.get("windows-sapi").available:self.skipTest("Windows SAPI unavailable")
  with tempfile.TemporaryDirectory() as d:self.v.output_enabled=True;r=self.v.say("voice test",output_path=Path(d)/"out.wav");self.assertEqual(r.status,VoiceStatus.COMPLETED);self.assertGreater(r.audio_size,0)
 def test_stt_unavailable_not_fake(self):
  with tempfile.TemporaryDirectory() as d:p=self.wav(d);self.v.settings=SimpleNamespace(base_dir=Path(d));r=self.v.transcribe_file(str(p));self.assertEqual(r.status,VoiceStatus.UNAVAILABLE)
 def test_interrupt_idempotent(self):self.assertFalse(self.v.interrupt())
 def test_cancel(self):self.v.enabled=True;s=self.v.create_session();self.v.cancel();self.assertEqual(self.v.sessions[s.voice_session_id].state,VoiceState.CANCELLED)
 def test_persistence_summary(self):
  with tempfile.TemporaryDirectory() as d:v=VoiceIntelligence(storage_dir=Path(d));v.enabled=True;v.create_session();v.cancel();self.assertTrue((Path(d)/"sessions.json").exists())
 def test_parser_command_separation(self):self.assertEqual(CommandParser().parse("voice say hello").name,"voice say")
 def test_parser_preserves_windows_audio_path(self):
  parsed=CommandParser().parse(r"voice transcribe C:\voice-input\sample.wav")
  self.assertEqual(parsed.arguments,(r"C:\voice-input\sample.wav",))
 def test_health(self):self.assertIn("windows-sapi",self.v.health())
 def test_strict_privacy_local(self):self.v.privacy_mode="strict";self.v.enabled=True;self.assertTrue(self.v.create_session().local_only)
 def test_wake_word_no_approval(self):self.assertNotIn("approval",self.v.health())

if __name__=="__main__":unittest.main()
