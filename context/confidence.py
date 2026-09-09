"""Exponential moving average smoothing — prevents emotion state from
flickering between values on noisy single-frame estimates."""
from typing import Dict, Optional
from context.models import EmotionState


class EMASmoother:
    def __init__(self, alpha: float = 0.3):
        """alpha closer to 1.0 = more responsive/less smooth.
        0.3 is a reasonable starting point — tune once real camera noise
        is observed in Phase 2, don't guess further than that now."""
        self.alpha = alpha
        self._scores: Dict[EmotionState, float] = {}

    def update(self, observed: EmotionState, observed_confidence: float) -> None:
        for state in EmotionState:
            prior = self._scores.get(state, 0.0)
            target = observed_confidence if state == observed else 0.0
            self._scores[state] = self.alpha * target + (1 - self.alpha) * prior

    def dominant(self) -> tuple[EmotionState, float]:
        if not self._scores:
            return EmotionState.NEUTRAL, 0.0
        state = max(self._scores, key=self._scores.get)
        return state, self._scores[state]

    def reset(self) -> None:
        self._scores.clear()
