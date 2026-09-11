"""Typed data models shared by EMU's perception, reasoning and hardware layers."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time

class EmotionState(str, Enum):
    NEUTRAL="NEUTRAL"; HAPPY="HAPPY"; SAD="SAD"; EXCITED="EXCITED"; TIRED="TIRED"; ANGRY="ANGRY"; SURPRISED="SURPRISED"; CONFUSED="CONFUSED"; STRESSED="STRESSED"; ANXIOUS="ANXIOUS"; FOCUSED="FOCUSED"; BORED="BORED"
class ExpressionType(str, Enum):
    NEUTRAL="NEUTRAL"; HAPPY="HAPPY"; SAD="SAD"; CURIOUS="CURIOUS"; SURPRISED="SURPRISED"; SLEEPY="SLEEPY"; TIRED="TIRED"; ALERT="ALERT"; CONFUSED="CONFUSED"; ANXIOUS="ANXIOUS"; LISTENING="LISTENING"; PROCESSING="PROCESSING"; EXCITED="EXCITED"; EMBARRASSED="EMBARRASSED"; PRIVACY="PRIVACY"; CONCERNED="CONCERNED"; ANGRY="ANGRY"; TALKING="TALKING"
class InteractionState(str, Enum):
    BOOT="BOOT"; IDLE="IDLE"; ATTENTION="ATTENTION"; LISTENING="LISTENING"; PROCESSING="PROCESSING"; INTERACTION="INTERACTION"; PRIVACY="PRIVACY"; RECOVERY="RECOVERY"; FAULT="FAULT"
class IntentType(str, Enum):
    GREET="GREET"; SUPPORT="SUPPORT"; ACKNOWLEDGE="ACKNOWLEDGE"; INFORM="INFORM"; IDLE_CHAT="IDLE_CHAT"; PRODUCTIVITY_NUDGE="PRODUCTIVITY_NUDGE"; PRIVACY_ACK="PRIVACY_ACK"; SAFETY_REDIRECT="SAFETY_REDIRECT"
class GestureType(str, Enum):
    NONE="NONE"; WAVE="WAVE"; NOD="NOD"; GENTLE_ATTENTION="GENTLE_ATTENTION"; SHUFFLE="SHUFFLE"; ACKNOWLEDGE="ACKNOWLEDGE"
class LightingState(str, Enum):
    IDLE="IDLE"; ATTENTION="ATTENTION"; LISTENING="LISTENING"; PROCESSING="PROCESSING"; HAPPY="HAPPY"; CALM="CALM"; ALERT="ALERT"; PRIVACY="PRIVACY"
@dataclass
class VisionObservation:
    timestamp: float=field(default_factory=time.time); face_detected: bool=False; face_count:int=0; face_x:Optional[float]=None; face_y:Optional[float]=None; face_size:Optional[float]=None; head_yaw:Optional[float]=None; head_pitch:Optional[float]=None; expression:Optional[EmotionState]=None; expression_confidence:Optional[float]=None; tracking_confidence:Optional[float]=None
@dataclass
class SpeechObservation:
    timestamp: float=field(default_factory=time.time); speaking:bool=False; speech_ended:bool=False; duration:Optional[float]=None; audio_energy:Optional[float]=None; pitch_hz:Optional[float]=None; speaking_rate_wpm:Optional[float]=None
@dataclass
class SemanticObservation:
    timestamp: float=field(default_factory=time.time); text:str=""; stt_confidence:Optional[float]=None; contains_distress_signal:bool=False
@dataclass
class VocalObservation:
    timestamp: float=field(default_factory=time.time); energy_level:Optional[float]=None; estimated_emotion:Optional[EmotionState]=None; estimated_confidence:Optional[float]=None
@dataclass
class UnifiedContext:
    timestamp:float=field(default_factory=time.time); interaction_state:InteractionState=InteractionState.IDLE; emotion:EmotionState=EmotionState.NEUTRAL; emotion_confidence:float=0.0; face_present:bool=False; face_x:Optional[float]=None; face_y:Optional[float]=None; speaking:bool=False; last_utterance:str=""; recent_history_summary:str=""; privacy_active:bool=False; robot_connected:bool=False
@dataclass
class Intent:
    intent:IntentType=IntentType.IDLE_CHAT; emotion:EmotionState=EmotionState.NEUTRAL; speech:str=""; gesture:GestureType=GestureType.NONE; expression:ExpressionType=ExpressionType.NEUTRAL; head_target_deg:Optional[int]=None; lighting:LightingState=LightingState.IDLE
    def validate(self)->"Intent":
        if self.head_target_deg is not None: self.head_target_deg=max(-30,min(30,self.head_target_deg))
        self.speech=self.speech[:400]
        return self
@dataclass
class RobotCommand:
    type:str
    payload:dict=field(default_factory=dict)
