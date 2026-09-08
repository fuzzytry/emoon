"""
Turns UnifiedContext + raw LLM text into a VALIDATED Intent. Arbitrary LLM
text never reaches hardware directly — this is the checkpoint.
"""
import json
import logging
from context.models import UnifiedContext, Intent, IntentType, EmotionState, \
    GestureType, ExpressionType, LightingState
from intelligence.llm import LLMClient
from intelligence.prompts import SYSTEM_PROMPT, build_context_block

logger = logging.getLogger("emu.decision")

DISTRESS_KEYWORDS = {"suicide", "kill myself", "self-harm", "want to die", "end it all"}


def _check_distress(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in DISTRESS_KEYWORDS)


class DecisionEngine:
    def __init__(self):
        self.llm = LLMClient()

    def decide(self, ctx: UnifiedContext) -> Intent:
        if _check_distress(ctx.last_utterance):
            # Bypass the LLM entirely for this — deterministic, tested,
            # non-negotiable safety path rather than trusting a model call.
            return Intent(
                intent=IntentType.SAFETY_REDIRECT,
                emotion=EmotionState.NEUTRAL,
                speech="That sounds really heavy. I'm not able to help with "
                       "something this serious, but please consider reaching "
                       "out to someone you trust or a crisis line.",
                gesture=GestureType.NONE,
                expression=ExpressionType.CONCERNED,
                lighting=LightingState.CALM,
            ).validate()

        if ctx.privacy_active:
            return Intent(
                intent=IntentType.PRIVACY_ACK,
                expression=ExpressionType.PRIVACY,
                lighting=LightingState.PRIVACY,
                speech="",
            ).validate()

        raw = self.llm.complete(SYSTEM_PROMPT, build_context_block(ctx))
        try:
            data = json.loads(raw)
            intent = Intent(
                intent=IntentType(data["intent"]),
                emotion=EmotionState(data["emotion"]),
                speech=str(data.get("speech", ""))[:400],
                gesture=GestureType(data.get("gesture", "NONE")),
                expression=ExpressionType(data.get("expression", "NEUTRAL")),
                lighting=LightingState(data.get("lighting", "IDLE")),
            )
            return intent.validate()
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("Malformed LLM output (%s) — using safe fallback intent", e)
            return Intent(
                intent=IntentType.IDLE_CHAT,
                speech="Sorry, I lost my train of thought there.",
                expression=ExpressionType.CONFUSED,
            ).validate()
