import logging,threading,numpy as np,sounddevice as sd,torch
from silero_vad import load_silero_vad,VADIterator
from faster_whisper import WhisperModel
from context.models import SpeechObservation,SemanticObservation
logger=logging.getLogger('emu.speech'); SAMPLE_RATE=16000; WINDOW_SAMPLES=512
class SpeechProvider:
 def __init__(self,stt_model='small.en',input_device=None):
  self.vad=load_silero_vad(onnx=True); self.vad_it=VADIterator(self.vad,sampling_rate=SAMPLE_RATE); self.whisper=WhisperModel(stt_model,device='cpu',compute_type='int8'); self._lock=threading.Lock(); self._buffer=[]; self._speaking=False; self._pending=None
  self._stream=sd.InputStream(samplerate=SAMPLE_RATE,channels=1,dtype='float32',blocksize=WINDOW_SAMPLES,device=input_device,callback=self._on_audio)
 def _on_audio(self,indata,frames,time_info,status):
  chunk=indata[:,0].copy(); r=self.vad_it(torch.from_numpy(chunk),return_seconds=True)
  with self._lock:
   if self._speaking:self._buffer.append(chunk)
   if r and 'start' in r:self._speaking=True; self._buffer=[chunk]
   elif r and 'end' in r and self._speaking:self._speaking=False; self._pending=np.concatenate(self._buffer) if self._buffer else None; self._buffer=[]
 def start(self):self._stream.start()
 def stop(self):self._stream.stop();self._stream.close()
 def poll(self):
  with self._lock:speaking=self._speaking; p=self._pending; self._pending=None
  obs=SpeechObservation(speaking=speaking)
  if p is not None:
   obs.speech_ended=True; obs.duration=len(p)/SAMPLE_RATE; obs.audio_energy=float(np.sqrt(np.mean(p**2)))
   try: segs,info=self.whisper.transcribe(p,language='en'); text=' '.join(s.text.strip() for s in segs).strip(); conf=round(float(getattr(info,'language_probability',0)),2)
   except Exception as e: logger.error('Whisper failed: %s',e); text=''; conf=0.
   return obs,SemanticObservation(text=text,stt_confidence=conf),p
  return obs,None,None
