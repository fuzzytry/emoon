import numpy as np,librosa
from context.models import VocalObservation,EmotionState
SAMPLE_RATE=16000
def analyze(audio,duration_s,word_count):
 o=VocalObservation()
 if audio is None or len(audio)<SAMPLE_RATE//2:return o
 rms=float(np.sqrt(np.mean(audio**2))); o.energy_level=round(min(1,rms*8),2); rate=(word_count/duration_s*60) if duration_s>0 and word_count>0 else None
 if o.energy_level>.6 and rate and rate>160:o.estimated_emotion,o.estimated_confidence=EmotionState.EXCITED,.45
 elif o.energy_level<.2:o.estimated_emotion,o.estimated_confidence=EmotionState.TIRED,.4
 else:o.estimated_emotion,o.estimated_confidence=EmotionState.NEUTRAL,.3
 return o
