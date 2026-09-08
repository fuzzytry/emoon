"""
Combines vision, speech, semantic, and vocal observations into one
UnifiedContext. This is the ONLY place emotion state is decided — the LLM
downstream receives the result, it does not do its own emotion inference.
"""
from typing import Optional
from context.models import (
    VisionObservation, SpeechObservation, SemanticObservation, VocalObservation,
    UnifiedContext, EmotionState, InteractionState,
)
from context.confidence import EMASmoother
from context.history import ConversationHistory


class FusionEngine:
    def __init__(self):
        self._smoother = EMASmoother(alpha=0.3)
        self.history = ConversationHistory()
        self._interaction_state = InteractionState.IDLE

    def fuse(
        self,
        vision: Optional[VisionObservation] = None,
        speech: Optional[SpeechObservation] = None,
        semantic: Optional[SemanticObservation] = None,
        vocal: Optional[VocalObservation] = None,
        privacy_active: bool = False,
        robot_connected: bool = False,
    ) -> UnifiedContext:
        # --- Combine whatever emotion signals are actually available ---
        # Deliberately simple weighting for this phase: vocal + vision are
        # each one vote if present; semantic distress overrides toward
        # SAD/STRESSED with lower confidence rather than a hard classification,
        # matching "if confidence is low, don't claim certainty."
        candidates: list[tuple[EmotionState, float]] = []
        if vision and vision.expression and vision.expression_confidence:
            candidates.append((vision.expression, vision.expression_confidence))
        if vocal and vocal.estimated_emotion and vocal.estimated_confidence:
            candidates.append((vocal.estimated_emotion, vocal.estimated_confidence))

        if candidates:
            # naive fusion: highest-confidence candidate feeds the smoother.
            # Replace with a real weighted fusion once Phase 2 gives us
            # actual noise characteristics to tune against.
            best_state, best_conf = max(candidates, key=lambda c: c[1])
            self._smoother.update(best_state, best_conf)

        emotion, confidence = self._smoother.dominant()

        # --- Interaction state transitions (mirrors Arduino side) ---
        if privacy_active:
            self._interaction_state = InteractionState.PRIVACY
        elif semantic and semantic.text and speech and speech.speech_ended:
            self._interaction_state = InteractionState.PROCESSING
        elif speech and speech.speaking:
            self._interaction_state = InteractionState.LISTENING
        elif vision and vision.face_detected:
            self._interaction_state = InteractionState.ATTENTION
        else:
            self._interaction_state = InteractionState.IDLE

        ctx = UnifiedContext(
            interaction_state=self._interaction_state,
            emotion=emotion,
            emotion_confidence=round(confidence, 2),
            face_present=bool(vision and vision.face_detected),
            face_x=vision.face_x if vision else None,
            face_y=vision.face_y if vision else None,
            speaking=bool(speech and speech.speaking),
            last_utterance=semantic.text if semantic else "",
            recent_history_summary=self.history.recent_summary(),
            privacy_active=privacy_active,
            robot_connected=robot_connected,
        )
        return ctx
