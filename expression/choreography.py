"""
Named Behavior presets — each is a coordinated set of outputs across every
subsystem at once, matching "HAPPY is one behavior, not unrelated commands."
"""
from dataclasses import dataclass, field
from context.models import ExpressionType, GestureType, LightingState


@dataclass
class Behavior:
    expression: ExpressionType
    head_target_deg: int
    gesture: GestureType
    lighting: LightingState
    audio_cue: str = ""  # short semantic name, e.g. "positive_beep" — TTS
                          # speech is handled separately by the intent's
                          # own "speech" field, this is a non-verbal cue only


BEHAVIOR_LIBRARY: dict[ExpressionType, Behavior] = {
    ExpressionType.NEUTRAL: Behavior(ExpressionType.NEUTRAL, 0, GestureType.NONE, LightingState.IDLE),
    ExpressionType.HAPPY: Behavior(ExpressionType.HAPPY, 5, GestureType.WAVE, LightingState.HAPPY, "positive_beep"),
    ExpressionType.CURIOUS: Behavior(ExpressionType.CURIOUS, 15, GestureType.GENTLE_ATTENTION, LightingState.ATTENTION),
    ExpressionType.SURPRISED: Behavior(ExpressionType.SURPRISED, -10, GestureType.NONE, LightingState.ALERT, "alert_beep"),
    ExpressionType.SLEEPY: Behavior(ExpressionType.SLEEPY, -15, GestureType.NONE, LightingState.CALM),
    ExpressionType.ALERT: Behavior(ExpressionType.ALERT, 0, GestureType.NONE, LightingState.ALERT, "alert_beep"),
    ExpressionType.CONFUSED: Behavior(ExpressionType.CONFUSED, 10, GestureType.NONE, LightingState.ATTENTION),
    ExpressionType.LISTENING: Behavior(ExpressionType.LISTENING, 0, GestureType.NONE, LightingState.LISTENING),
    ExpressionType.PROCESSING: Behavior(ExpressionType.PROCESSING, 0, GestureType.NONE, LightingState.PROCESSING),
    ExpressionType.PRIVACY: Behavior(ExpressionType.PRIVACY, 0, GestureType.NONE, LightingState.PRIVACY),
    ExpressionType.CONCERNED: Behavior(ExpressionType.CONCERNED, -5, GestureType.GENTLE_ATTENTION, LightingState.CALM),
}
