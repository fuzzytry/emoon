"""Kokoro TTS with explicit speaking lifecycle."""
import logging,threading
import numpy as np
import sounddevice as sd
from kokoro import KPipeline
logger=logging.getLogger("emu.tts"); SAMPLE_RATE=24000
class TTSEngine:
 def __init__(self,lang_code="a",voice="af_heart",output_device=None):
  self.pipeline=KPipeline(lang_code=lang_code); self.voice=voice; self.output_device=output_device; self._speaking=threading.Event(); self._stop_flag=threading.Event(); self._lock=threading.Lock()
 @property
 def is_speaking(self): return self._speaking.is_set()
 def stop(self): self._stop_flag.set(); sd.stop()
 def speak(self,text,blocking=False):
  if not text:return
  if blocking:self._speak_now(text)
  else: threading.Thread(target=self._speak_now,args=(text,),daemon=True).start()
 def _speak_now(self,text):
  with self._lock:
   self._stop_flag.clear(); self._speaking.set(); logger.info("[TTS] starting: %r",text)
   try:
    for _,_,audio in self.pipeline(text,voice=self.voice):
     if self._stop_flag.is_set(): break
     a=audio.numpy() if hasattr(audio,"numpy") else np.asarray(audio,dtype=np.float32); sd.play(a,SAMPLE_RATE,device=self.output_device); sd.wait()
   except Exception as exc: logger.error("[TTS] error: %s",exc,exc_info=True)
   finally:self._speaking.clear()
