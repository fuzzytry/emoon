"""
Typed data models for EMU's perception/context/intent pipeline.
No arbitrary dicts passed between layers — every boundary is a dataclass.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time


class EmotionState(str, Enum):
    NEUTRAL = "NEUTRAL"
    HAPPY = "HAPPY"
    SAD = "SAD"
    EXCITED = "EXCITED"
    TIRED = "TIRED"
    ANGRY = "ANGRY"
    SURPRISED = "SURPRISED"
    CONFUSED = "CONFUSED"
    STRESSED = "STRESSED"
    ANXIOUS = "ANXIOUS"
    FOCUSED = "FOCUSED"
    BORED = "BORED"


class InteractionState(str, Enum):
    """Mirrors the Arduino-side state machine vocabulary so both ends of the
    serial link share the same concepts — the robot doesn't need to reinterpret."""
    BOOT = "BOOT"
    IDLE = "IDLE"
    ATTENTION = "ATTENTION"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    INTERACTION = "INTERACTION"
    PRIVACY = "PRIVACY"
    RECOVERY = "RECOVERY"
    FAULT = "FAULT"


class IntentType(str, Enum):
    GREET = "GREET"
    SUPPORT = "SUPPORT"
    ACKNOWLEDGE = "ACKNOWLEDGE"
    INFORM = "INFORM"
    IDLE_CHAT = "IDLE_CHAT"
    PRODUCTIVITY_NUDGE = "PRODUCTIVITY_NUDGE"
    PRIVACY_ACK = "PRIVACY_ACK"
    SAFETY_REDIRECT = "SAFETY_REDIRECT"  # see decision.py — used for serious distress


class GestureType(str, Enum):
    NONE = "NONE"
    WAVE = "WAVE"
    NOD = "NOD"
    GENTLE_ATTENTION = "GENTLE_ATTENTION"
    SHUFFLE = "SHUFFLE"
    ACKNOWLEDGE = "ACKNOWLEDGE"


class ExpressionType(str, Enum):
    NEUTRAL = "NEUTRAL"
    HAPPY = "HAPPY"
    CURIOUS = "CURIOUS"
    SURPRISED = "SURPRISED"
    SLEEPY = "SLEEPY"
    ALERT = "ALERT"
    CONFUSED = "CONFUSED"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    PRIVACY = "PRIVACY"
    CONCERNED = "CONCERNED"


class LightingState(str, Enum):
    IDLE = "IDLE"
    ATTENTION = "ATTENTION"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    HAPPY = "HAPPY"
    CALM = "CALM"
    ALERT = "ALERT"
    PRIVACY = "PRIVACY"


# ---------------- Perception observations ----------------
# Every field defaults to "unavailable" (None) rather than a fabricated
# value — a provider that can't determine something must say so.

@dataclass
class VisionObservation:
    timestamp: float = field(default_factory=time.time)
    face_detected: bool = False
    face_count: int = 0
    face_x: Optional[float] = None   # normalized 0-1, left to right
    face_y: Optional[float] = None   # normalized 0-1, top to bottom
    face_size: Optional[float] = None
    head_yaw: Optional[float] = None
    head_pitch: Optional[float] = None
    expression: Optional[EmotionState] = None
    expression_confidence: Optional[float] = None
    tracking_confidence: Optional[float] = None


@dataclass
class SpeechObservation:
    timestamp: float = field(default_factory=time.time)
    speaking: bool = False
    speech_ended: bool = False
    duration: Optional[float] = None
    audio_energy: Optional[float] = None
    pitch_hz: Optional[float] = None
    speaking_rate_wpm: Optional[float] = None


@dataclass
class SemanticObservation:
    """What the user said, independent of how they said it."""
    timestamp: float = field(default_factory=time.time)
    text: str = ""
    stt_confidence: Optional[float] = None
    contains_distress_signal: bool = False  # set by a simple keyword/semantic
                                             # safety check — see decision.py


@dataclass
class VocalObservation:
    """How the user said it — separate from SemanticObservation deliberately."""
    timestamp: float = field(default_factory=time.time)
    energy_level: Optional[float] = None      # 0-1
    estimated_emotion: Optional[EmotionState] = None
    estimated_confidence: Optional[float] = None


# ---------------- Fused context ----------------

@dataclass
class UnifiedContext:
    timestamp: float = field(default_factory=time.time)
    interaction_state: InteractionState = InteractionState.IDLE
    emotion: EmotionState = EmotionState.NEUTRAL
    emotion_confidence: float = 0.0
    face_present: bool = False
    face_x: Optional[float] = None
    face_y: Optional[float] = None
    speaking: bool = False
    last_utterance: str = ""
    recent_history_summary: str = ""
    privacy_active: bool = False
    robot_connected: bool = False


# ---------------- Validated intent (LLM output, never used raw) ----------------

@dataclass
class Intent:
    intent: IntentType = IntentType.IDLE_CHAT
    emotion: EmotionState = EmotionState.NEUTRAL
    speech: str = ""
    gesture: GestureType = GestureType.NONE
    expression: ExpressionType = ExpressionType.NEUTRAL
    head_target_deg: Optional[int] = None
    lighting: LightingState = LightingState.IDLE

    def validate(self) -> "Intent":
        """Clamp/repair anything out of range rather than trust the LLM blindly.
        This is layer 1 of the two-layer safety validation — layer 2 is the
        Arduino's own servo clamping in hardware/protocol.py's schema."""
        if self.head_target_deg is not None:
            self.head_target_deg = max(-30, min(30, self.head_target_deg))
        if len(self.speech) > 400:
            self.speech = self.speech[:400]
        return self


# ---------------- Robot command envelope ----------------

@dataclass
class RobotCommand:
    """A single low-level command bound for the Arduino."""
    type: str      # "expression" | "gesture" | "servo" | "system"
    payload: dict = field(default_factory=dict)
