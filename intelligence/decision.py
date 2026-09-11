import json,logging,re
from context.models import UnifiedContext,Intent,IntentType,EmotionState,GestureType,ExpressionType,LightingState
from intelligence.llm import LLMClient
from intelligence.prompts import SYSTEM_PROMPT,build_context_block
logger=logging.getLogger('emu.decision')
DISTRESS=('suicide','kill myself','self-harm','want to die','end it all')
class DecisionEngine:
 def __init__(self):self.llm=LLMClient()
 def decide(self,ctx):
  text=ctx.last_utterance.lower()
  if any(k in text for k in DISTRESS):return Intent(IntentType.SAFETY_REDIRECT,EmotionState.NEUTRAL,"That sounds really heavy. Please consider reaching out to someone you trust or a crisis resource.",GestureType.NONE,ExpressionType.CONCERNED,None,LightingState.CALM).validate()
  if ctx.privacy_active:return Intent(IntentType.PRIVACY_ACK,EmotionState.NEUTRAL,"",GestureType.NONE,ExpressionType.PRIVACY,None,LightingState.PRIVACY).validate()
  try:
   d=json.loads(self.llm.complete(SYSTEM_PROMPT,build_context_block(ctx))); return Intent(IntentType(d['intent']),EmotionState(d['emotion']),str(d.get('speech',''))[:400],GestureType(d.get('gesture','NONE')),ExpressionType(d.get('expression','NEUTRAL')),None,LightingState(d.get('lighting','IDLE'))).validate()
  except (json.JSONDecodeError,KeyError,ValueError): return Intent(IntentType.IDLE_CHAT,EmotionState.NEUTRAL,"Sorry, I lost my train of thought there.",GestureType.NONE,ExpressionType.CONFUSED,None,LightingState.ATTENTION).validate()
