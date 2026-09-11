from typing import Dict
from context.models import EmotionState
class EMASmoother:
 def __init__(self,alpha=.3): self.alpha=alpha; self._scores:Dict[EmotionState,float]={}
 def update(self,observed,confidence):
  for s in EmotionState:self._scores[s]=self.alpha*(confidence if s==observed else 0)+(1-self.alpha)*self._scores.get(s,0)
 def dominant(self): return (max(self._scores,key=self._scores.get),self._scores[max(self._scores,key=self._scores.get)]) if self._scores else (EmotionState.NEUTRAL,0.0)
 def reset(self): self._scores.clear()
