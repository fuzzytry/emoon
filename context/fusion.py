from typing import Optional
from context.models import VisionObservation,SpeechObservation,SemanticObservation,VocalObservation,UnifiedContext,EmotionState,InteractionState
from context.confidence import EMASmoother
from context.history import ConversationHistory
class FusionEngine:
 def __init__(self): self._smoother=EMASmoother(.3); self.history=ConversationHistory(); self._interaction_state=InteractionState.IDLE
 def fuse(self,vision:Optional[VisionObservation]=None,speech:Optional[SpeechObservation]=None,semantic:Optional[SemanticObservation]=None,vocal:Optional[VocalObservation]=None,privacy_active=False,robot_connected=False):
  c=[]
  if vision and vision.expression and vision.expression_confidence: c.append((vision.expression,vision.expression_confidence))
  if vocal and vocal.estimated_emotion and vocal.estimated_confidence: c.append((vocal.estimated_emotion,vocal.estimated_confidence))
  if c:self._smoother.update(*max(c,key=lambda x:x[1]))
  e,conf=self._smoother.dominant()
  if privacy_active:s=InteractionState.PRIVACY
  elif semantic and semantic.text and speech and speech.speech_ended:s=InteractionState.PROCESSING
  elif speech and speech.speaking:s=InteractionState.LISTENING
  elif vision and vision.face_detected:s=InteractionState.ATTENTION
  else:s=InteractionState.IDLE
  self._interaction_state=s
  return UnifiedContext(interaction_state=s,emotion=e,emotion_confidence=round(conf,2),face_present=bool(vision and vision.face_detected),face_x=vision.face_x if vision else None,face_y=vision.face_y if vision else None,speaking=bool(speech and speech.speaking),last_utterance=semantic.text if semantic else '',recent_history_summary=self.history.recent_summary(),privacy_active=privacy_active,robot_connected=robot_connected)
